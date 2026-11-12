"""Per-query datasets, honest out-of-time evaluation and actionable market reports."""
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
import threading
import time
from datetime import datetime, timezone
from urllib.request import Request, build_opener

import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, f1_score, silhouette_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from core.config import settings
from core.serialization import np_clean

_training = threading.BoundedSemaphore(settings.max_research_training)
_cache_lock = threading.Lock()

# These are national context indicators, never school/company observations.
INDICATORS = {
    'Education & EdTech': ('SE.TER.ENRR', 'Tỷ lệ nhập học giáo dục đại học Việt Nam', '% tỷ lệ nhập học gộp'),
    'Tourism & Hospitality': ('ST.INT.ARVL', 'Lượt khách du lịch quốc tế đến Việt Nam', 'lượt khách'),
    'Healthcare & Fitness': ('SH.XPD.CHEX.PC.CD', 'Chi y tế bình quân đầu người Việt Nam', 'USD/người'),
    'Technology & Gaming': ('TX.VAL.TECH.CD', 'Giá trị xuất khẩu công nghệ cao Việt Nam', 'USD'),
    'Smartphones & Mobile': ('TX.VAL.TECH.CD', 'Giá trị xuất khẩu công nghệ cao Việt Nam', 'USD'),
    'Audio & Consumer Electronics': ('TX.VAL.TECH.CD', 'Giá trị xuất khẩu công nghệ cao Việt Nam', 'USD'),
    'Smart Home & IoT': ('TX.VAL.TECH.CD', 'Giá trị xuất khẩu công nghệ cao Việt Nam', 'USD'),
    'Digital Services & SaaS': ('IT.NET.USER.ZS', 'Tỷ lệ dân số sử dụng Internet Việt Nam', '% dân số'),
    'FinTech & Digital Finance': ('FS.AST.PRVT.GD.ZS', 'Tín dụng khu vực tư nhân Việt Nam', '% GDP'),
    'Logistics & Supply Chain': ('IS.SHP.GOOD.TU', 'Lưu lượng container cảng biển Việt Nam', 'TEU'),
    'Real Estate & Housing': ('SP.URB.TOTL.IN.ZS', 'Tỷ lệ dân số đô thị Việt Nam', '% dân số'),
    'Food & Beverage': ('NE.CON.PRVT.PC.KD', 'Tiêu dùng hộ gia đình bình quân đầu người Việt Nam', 'USD cố định 2015/người'),
    'FMCG & Consumer Goods': ('NE.CON.PRVT.PC.KD', 'Tiêu dùng hộ gia đình bình quân đầu người Việt Nam', 'USD cố định 2015/người'),
    'Beauty & Skincare': ('NE.CON.PRVT.PC.KD', 'Tiêu dùng hộ gia đình bình quân đầu người Việt Nam', 'USD cố định 2015/người'),
    'Fashion & E-Commerce': ('NE.CON.PRVT.PC.KD', 'Tiêu dùng hộ gia đình bình quân đầu người Việt Nam', 'USD cố định 2015/người'),
    'Electric Vehicles': ('NE.CON.PRVT.PC.KD', 'Tiêu dùng hộ gia đình bình quân đầu người Việt Nam', 'USD cố định 2015/người'),
}
DEFAULT_INDICATOR = ('NY.GDP.PCAP.KD', 'GDP bình quân đầu người Việt Nam', 'USD cố định 2015/người')


def storage():
    root = settings.database_path.parent / 'research_runs'
    root.mkdir(parents=True, exist_ok=True)
    return root


def atomic_text(path, content):
    handle, name = tempfile.mkstemp(dir=path.parent, prefix='.writing-')
    try:
        with os.fdopen(handle, 'w', encoding='utf-8', newline='') as stream:
            stream.write(content)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def fetch_reference(code):
    """Fixed public API only; no user-controlled host, path, or country."""
    if code not in {v[0] for v in INDICATORS.values()} | {DEFAULT_INDICATOR[0]}:
        raise ValueError('Unsupported reference series')
    from services.research import NoRedirect
    if settings.environment == 'test':
        raise OSError('External reference requests are disabled in tests')
    url = f'https://api.worldbank.org/v2/country/VNM/indicator/{code}?format=json&per_page=100&date=1990:{datetime.now(timezone.utc).year}'
    cache = storage() / f'cache-{code}.json'
    with _cache_lock:
        try:
            cached = json.loads(cache.read_text(encoding='utf-8'))
            if time.time() - cached['fetched_at'] < 86400:
                return cached['rows'], url, cached['retrieved_at'], True
        except (OSError, ValueError, KeyError, TypeError):
            pass
    try:
        req = Request(url, headers={'User-Agent': 'MarketWise/3.0 (public indicator research)'})
        with build_opener(NoRedirect).open(req, timeout=10) as response:
            body = response.read(1_000_001)
            if len(body) > 1_000_000:
                raise ValueError('Reference response too large')
            payload = json.loads(body)
        if not isinstance(payload, list) or len(payload) != 2 or not isinstance(payload[1], list):
            raise ValueError('Invalid reference response')
        rows = []
        for entry in payload[1]:
            if (entry.get('countryiso3code') != 'VNM' or entry.get('indicator', {}).get('id') != code
                    or not re.fullmatch(r'\d{4}', str(entry.get('date', '')))):
                continue
            year, value = int(entry['date']), entry.get('value')
            if isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value) and 1990 <= year <= datetime.now(timezone.utc).year:
                rows.append({'period': str(year), 'value': float(value), 'source_url': url, 'observed_entity': 'Việt Nam'})
        rows.sort(key=lambda row: row['period'])
        if len({r['period'] for r in rows}) != len(rows) or len(rows) < 12:
            raise ValueError('Insufficient distinct annual observations')
        retrieved = datetime.now(timezone.utc).isoformat()
        atomic_text(cache, json.dumps({'fetched_at': time.time(), 'retrieved_at': retrieved, 'rows': rows}, ensure_ascii=False))
        return rows, url, retrieved, False
    except Exception:
        # A previously downloaded source remains usable with its real retrieval date.
        try:
            cached = json.loads(cache.read_text(encoding='utf-8'))
            if time.time() - cached['fetched_at'] < 30 * 86400 and len(cached['rows']) >= 12:
                return cached['rows'], url, cached['retrieved_at'], True
        except (OSError, ValueError, KeyError, TypeError):
            pass
        raise


def evaluate_series(rows, horizon=3):
    """Train on lagged observations; compare to a persistence baseline on later years."""
    years = np.array([int(row['period']) for row in rows])
    values = np.array([float(row['value']) for row in rows])
    if len(rows) < 12 or not np.all(np.isfinite(values)) or np.any(np.diff(years) <= 0):
        raise ValueError('Insufficient chronological observations')
    # Never turn missing years into adjacent annual lags or interpolate them.
    triples = [i for i in range(2, len(rows)) if years[i]-years[i-1] == years[i-1]-years[i-2] == 1]
    if len(triples) < 10 or years[-1]-years[-2] != 1:
        raise ValueError('Cần ít nhất 10 bộ quan sát năm liên tiếp; không tự điền năm thiếu.')
    x = np.array([[years[i], values[i-1], values[i-2]] for i in triples])
    y = np.array([values[i] for i in triples])
    split = max(6, int(len(y)*.75))
    if len(y)-split < 3:
        split = len(y)-3
    train_x, test_x, train_y, test_y = x[:split], x[split:], y[:split], y[split:]
    candidates = [
        ('Xu hướng có điều chuẩn', make_pipeline(StandardScaler(), Ridge(alpha=1.0))),
        ('Quan hệ phi tuyến', RandomForestRegressor(n_estimators=60, max_depth=4, min_samples_leaf=2, random_state=42, n_jobs=1)),
    ]
    baseline_prediction = test_x[:,1]
    baseline_mae = float(mean_absolute_error(test_y, baseline_prediction))
    evaluations = []
    for label, estimator in candidates:
        estimator.fit(train_x, train_y)
        prediction = estimator.predict(test_x)
        evaluations.append({'label': label, 'mae': float(mean_absolute_error(test_y, prediction)),
            'rmse': float(np.sqrt(mean_squared_error(test_y, prediction))),
            'r2': float(r2_score(test_y, prediction)) if np.var(test_y) > 1e-12 else None,
            'test_rows': len(test_y), 'train_rows': len(train_y), 'estimator': estimator, 'prediction': prediction})
    best = min(evaluations, key=lambda e: e['mae'])
    beats_baseline = best['mae'] < baseline_mae
    selected = best['estimator'] if beats_baseline else None
    used_prediction = best['prediction'] if selected is not None else baseline_prediction
    mae = float(mean_absolute_error(test_y, used_prediction))
    residual = float(np.quantile(np.abs(test_y-used_prediction), .9))
    if selected is not None:
        selected.fit(x, y)
    last, previous = values[-1], values[-2]
    forecast = []
    for step in range(1,horizon+1):
        value = float(selected.predict([[years[-1]+step,last,previous]])[0]) if selected is not None else float(last)
        if (values >= 0).all(): value = max(0.0, value)
        spread = residual*np.sqrt(step)
        forecast.append({'period': str(years[-1]+step), 'value': value, 'lower': max(0.0,value-spread) if (values>=0).all() else value-spread, 'upper': value+spread})
        previous, last = last, value
    # Up/down labels are measured next-period changes, not invented market potential.
    labels = (y > x[:,1]).astype(int)
    classification = {'status': 'insufficient_classes', 'accuracy': None, 'f1': None, 'next_direction': None}
    if len(np.unique(labels[:split])) == 2:
        classifier = RandomForestClassifier(n_estimators=60, max_depth=3, min_samples_leaf=2, random_state=42, n_jobs=1)
        classifier.fit(train_x, labels[:split])
        predicted = classifier.predict(test_x)
        majority = int(np.mean(labels[:split]) >= .5)
        baseline_accuracy = float(accuracy_score(labels[split:], np.full(len(test_y), majority)))
        classification = {'status':'completed', 'accuracy': float(accuracy_score(labels[split:], predicted)),
            'f1': float(f1_score(labels[split:], predicted, zero_division=0)),
            'baseline_accuracy': baseline_accuracy,
            'beats_baseline': float(accuracy_score(labels[split:], predicted)) > baseline_accuracy,
            'test_rows': len(test_y), 'next_direction': 'Tăng' if classifier.predict([[years[-1]+1,values[-1],values[-2]]])[0] else 'Không tăng'}
    clusters = {'status': 'insufficient_variation', 'silhouette': None, 'groups': []}
    pair = np.array([[values[i],values[i]-values[i-1]] for i in range(1,len(values)) if years[i]-years[i-1] == 1])
    pair_years = [str(years[i]) for i in range(1,len(values)) if years[i]-years[i-1] == 1]
    if len(np.unique(pair,axis=0)) >= 3:
        z = StandardScaler().fit_transform(pair)
        km = KMeans(n_clusters=3, random_state=42, n_init=10)
        group_labels = km.fit_predict(z)
        if 1 < len(set(group_labels)) < len(pair):
            centers = {c: float(np.mean(pair[group_labels==c,0])) for c in set(group_labels)}
            ordered = sorted(centers,key=centers.get)
            clusters = {'status':'completed', 'silhouette': float(silhouette_score(z,group_labels)),
                'groups':[{'label':['Mức thấp trong chuỗi','Mức trung bình trong chuỗi','Mức cao trong chuỗi'][rank],
                    'count':int(sum(group_labels==c)), 'periods':[yr for yr,lab in zip(pair_years,group_labels) if lab==c]} for rank,c in enumerate(ordered)]}
    return np_clean({'status':'completed', 'method':best['label'] if beats_baseline else 'Giữ giá trị gần nhất (phương án cơ sở)',
        'evaluations':[{k:v for k,v in e.items() if k not in ('estimator','prediction')} for e in evaluations],
        'validation': {'mae':mae, 'baseline_mae':baseline_mae, 'beats_baseline':beats_baseline,
            'train_end':str(years[triples[split-1]]), 'test_start':str(years[triples[split]]), 'test_end':str(years[triples[-1]]),
            'test_rows':len(test_y), 'r2':float(r2_score(test_y,used_prediction)) if np.var(test_y)>1e-12 else None,
            'note':'Kiểm định trên các năm sau tập huấn luyện. R² có thể âm. Khoảng hiển thị dùng sai số thực nghiệm, không bảo đảm xác suất bao phủ.'},
        'forecast':forecast, 'classification':classification, 'clustering':clusters,
        'recent_change':float(values[-1]-values[-2]), 'recent_change_pct':float((values[-1]/values[-2]-1)*100) if abs(values[-2])>1e-9 else None,
        'forecast_change_pct':float((forecast[-1]['value']/values[-1]-1)*100) if abs(values[-1])>1e-9 else None})


def build_strategy(query, context, evidence, provenance, quantitative, ai_intel=None):
    from services.report_sections import build_sections, get_keyword_intelligence, _source_digest
    intel = get_keyword_intelligence(query, context, evidence)
    digest = _source_digest(query, evidence)
    audience = intel['audience']
    offer = intel['offer']
    focus = intel['focus']
    channels = intel['channels']
    peers = intel['peers']
    trend = quantitative.get('recent_change_pct') if quantitative else None
    validation = (quantitative or {}).get('validation') or {}
    reliable = bool(validation.get('beats_baseline') and validation.get('r2') is not None and validation['r2'] > 0)
    trend_text = f"Chỉ tiêu tham khảo thay đổi {trend:+.2f}% ở năm gần nhất có dữ liệu." if trend is not None else 'Chưa xác định được xu hướng định lượng đủ điều kiện.'
    scope = provenance.get('scope_label', 'Chưa có chuỗi dữ liệu đủ điều kiện')
    confirmed = [f"Tìm được {len(evidence)} tài liệu về từ khóa “{query}”.", f"Phạm vi định lượng: {scope}."]
    if digest['figures']:
        confirmed.append(f"Số liệu trích xuất từ nguồn tra cứu: {', '.join(digest['figures'])}.")

    sections = build_sections(query, context, evidence, provenance, quantitative)
    lead_summary = (
        ai_intel['executive_summary'].strip()
        if (ai_intel and ai_intel.get('executive_summary'))
        else f"Đối với “{query}” ({context['label'].lower()}), trọng tâm chiến lược là {focus} trong tương quan đối sánh với {peers}.{digest['title_note']}{digest['figure_note']}"
    )
    provenance_note = (
        'Chưa có chuỗi quan sát riêng đã xác nhận của đối tượng; kết quả định lượng bên dưới chỉ mô tả bối cảnh tham khảo.'
        if provenance.get('mode') != 'entity_observations'
        else 'Kết quả định lượng dựa trên các quan sát đúng đối tượng trong bộ dữ liệu được nêu.'
    )
    reliability_note = (
        ' Kiểm định hỗ trợ thử nghiệm nhỏ, vẫn cần dữ liệu riêng trước khi mở rộng.'
        if reliable
        else ' Mức hỗ trợ dự báo còn yếu; ưu tiên xác minh dữ liệu và thử nghiệm nhỏ, chưa dùng dự báo để quyết định mở rộng.'
    )
    specific_risks = list((ai_intel or {}).get('risks') or [r[1] for r in intel['risks_tuples']])
    specific_risks.extend([
        'Dữ liệu năm hoặc chuỗi tham khảo vĩ mô có độ trễ; cần đối chiếu với số liệu vận hành thực tế của chính đối tượng.',
        'Nếu sai số kiểm định chưa vượt qua phương án cơ sở, ưu tiên thử nghiệm phạm vi hẹp trước khi mở rộng vốn lớn.',
    ])
    action_plan = (
        ai_intel['action_plan_30_60_90']
        if (ai_intel and isinstance(ai_intel.get('action_plan_30_60_90'), list) and len(ai_intel['action_plan_30_60_90']) == 3)
        else intel['action_plan']
    )
    kpis = (
        ai_intel['specific_kpis']
        if (ai_intel and isinstance(ai_intel.get('specific_kpis'), list) and len(ai_intel['specific_kpis']) >= 4)
        else intel['kpis']
    )
    return {
        **sections,
        'conclusion': f"{lead_summary} {trend_text} {provenance_note}{reliability_note}",
        'recommended_scenario': 'Thử nghiệm có kiểm soát' if reliable else 'Thận trọng',
        'confirmed_findings': confirmed,
        'market_position': f"Đánh giá chuyên sâu “{query}” qua bộ tiêu chí {', '.join(context['criteria'][:4]).lower()} và đặt trong nhóm đối sánh trực tiếp gồm: {peers}.",
        'audience': audience,
        'value_proposition': (
            str(ai_intel.get('product_strategy') or '').lstrip('📦 ').strip()
            if (ai_intel and ai_intel.get('product_strategy'))
            else f"Tập trung chuẩn hóa và làm nổi bật {offer}; mọi cam kết giá trị cần gắn liền với dữ liệu kiểm chứng thực tế của {query}."
        ),
        'execution_axes': [
            {'area': 'Phân khúc đối tượng ưu tiên', 'action': f'Tập trung nguồn lực vào nhóm {audience}; phân loại theo nhu cầu thực tế và mức độ sẵn sàng chuyển đổi đối với {query}.', 'measure': 'Tỷ lệ phản hồi, nhu cầu xác nhận và tỷ lệ chuyển đổi theo từng phân nhóm.'},
            {'area': 'Cấu trúc sản phẩm & Giá trị cốt lõi', 'action': f'Chuẩn hóa chất lượng và thông tin công bố về {offer}; giải quyết trực tiếp các rào cản lựa chọn của người dùng.', 'measure': 'Mức độ hài lòng (CSAT), tỷ lệ hoàn tất hành động mục tiêu và phản hồi thực tế.'},
            {'area': 'Chính sách giá, Học phí & Đãi ngộ', 'action': intel['pricing_reason'], 'measure': 'Mức chi phí thực trả, khả năng chi trả của đối tượng và biên đóng góp đơn vị.'},
            {'area': 'Hệ thống kênh tiếp cận & Phân phối', 'action': f'Triển khai trọng điểm qua: {channels}. Gắn mã đo lường hiệu quả chuyển đổi riêng cho từng kênh theo tuần.', 'measure': 'Lượt tiếp cận hợp lệ, tỷ lệ chuyển đổi và chi phí thu hút trên mỗi kênh.'},
            {'area': 'Trải nghiệm thực tế & Giữ chân', 'action': f'Rà soát toàn bộ hành trình tiếp cận {query}, xử lý dứt điểm các điểm nghẽn gây bỏ cuộc và củng cố chất lượng hậu mãi/đồng hành.', 'measure': 'Thời gian phản hồi, tỷ lệ hoàn tất hồ sơ/đơn hàng và tỷ lệ gắn bó dài hạn.'},
            {'area': 'Đối sánh cạnh tranh & Định vị khác biệt', 'action': f'Đối chiếu trực tiếp {query} với nhóm cùng phân khúc ({peers}) trên cùng kỳ dữ liệu và tiêu chí chuyên môn.', 'measure': 'Số tiêu chí có bằng chứng vượt trội hoặc khác biệt rõ ràng được thị trường ghi nhận.'},
            {'area': 'Quản trị nguồn lực & Ngưỡng an toàn', 'action': f'Phân bổ ngân sách cho {focus} theo từng giai đoạn 30 ngày; thiết lập ngưỡng chi phí tối đa và điều kiện dừng rõ ràng.', 'measure': 'Chi phí thực tế so với ngân sách duyệt; hiệu suất ROI sau mỗi chu kỳ 30 ngày.'},
        ],
        'opportunities': [
            {'title': f'Tối ưu hóa {offer[:90]}', 'basis': intel['market_gap'], 'action': f'Triển khai khảo sát và thử nghiệm trực tiếp trên nhóm {audience[:90]} để đo lường mức độ hưởng ứng.'},
            {'title': f'Khai thác động lực thị trường & đối sánh cùng phân khúc', 'basis': f"{trend_text}{digest['figure_note']}", 'action': f'So sánh hiệu suất của {query} với {peers[:90]} để mở rộng tại phân khúc có tỷ lệ chuyển đổi cao nhất.'},
        ],
        'risks': specific_risks[:5],
        'scenarios': [
            {'name': 'Thận trọng', 'condition': f'Thiếu chuỗi dữ liệu riêng của {query} hoặc sai số kiểm định chưa vượt phương án cơ sở', 'decision': f'Giữ ổn định nguồn lực cốt lõi; ưu tiên chuẩn hóa dữ liệu và hoàn thiện {offer[:70]}.'},
            {'name': 'Thử nghiệm có kiểm soát', 'condition': f'Có dữ liệu đối chiếu rõ ràng cho {query} và thử nghiệm ban đầu đạt KPI', 'decision': f'Tập trung triển khai {focus} trên kênh hiệu quả nhất; đánh giá kết quả hàng tuần.'},
            {'name': 'Mở rộng từng bước', 'condition': 'Đạt vượt chỉ tiêu KPI trong ít nhất 2 kỳ liên tiếp với biên lợi nhuận/hiệu quả bền vững', 'decision': f'Tăng quy mô đầu tư cho {query} theo từng đợt; kiểm soát chặt chất lượng và rủi ro vận hành.'},
        ],
        'action_plan': action_plan,
        'kpis': kpis,
        'limitations': context['requirements'],
    }


def build_report(query, sources, analysis):
    from services.research_evidence import subject_context
    ctx = subject_context(query, sources)
    indicator = INDICATORS.get(ctx['category'], DEFAULT_INDICATOR)
    dataset_id = hashlib.sha256((query.strip().casefold()+'|'+datetime.now(timezone.utc).isoformat()).encode()).hexdigest()[:32]
    rows, quantitative, error = [], None, None
    provenance = {'mode':'reference_unavailable','scope_label':'Chưa có chuỗi định lượng', 'requested_entity':query,
                  'observed_entity':'Việt Nam', 'indicator_code':indicator[0], 'indicator_label':indicator[1], 'unit':indicator[2],
                  'country':'VNM', 'source_name':'World Bank · World Development Indicators',
                  'is_entity_data':False, 'independently_verified':False,
                  'geography_note':'Việt Nam là địa bàn tham khảo mặc định của ứng dụng; không khẳng định đây là địa bàn hoạt động của từ khóa.'}
    try:
        try:
            rows, url, retrieved, cached = fetch_reference(indicator[0])
        except Exception:
            if indicator == DEFAULT_INDICATOR:
                raise
            requested_indicator = indicator
            indicator = DEFAULT_INDICATOR
            rows, url, retrieved, cached = fetch_reference(indicator[0])
            provenance.update(indicator_code=indicator[0], indicator_label=indicator[1], unit=indicator[2],
                selection_note=f'Chưa tải được chỉ tiêu {requested_indicator[1]}; dùng bối cảnh kinh tế chung, không coi đây là dữ liệu riêng của ngành.')
        provenance.update(mode='national_reference', scope_label=indicator[1], source_url=url,
                          retrieved_at=retrieved, cached=cached, first_period=rows[0]['period'], last_period=rows[-1]['period'])
        with _training:
            quantitative = evaluate_series(rows)
    except Exception as exc:
        # Report remains actionable even when the authoritative source cannot be reached.
        error = 'Chưa tải được chuỗi dữ liệu chính thức hoặc chuỗi chưa đủ kỳ liên tiếp để kiểm định. Không tạo số liệu thay thế.'
    strategy = build_strategy(query,ctx,sources,provenance,quantitative)
    report = np_clean({'dataset_id':dataset_id,'query':query,'created_at':datetime.now(timezone.utc).isoformat(),
        'status':'completed_reference' if quantitative else 'insufficient_quantitative_data',
        'entity_data_status':'Chưa có chuỗi dữ liệu riêng đã xác nhận', 'provenance':provenance,
        'training_data':rows,'quantitative':quantitative,'data_issue':error,'strategy':strategy,
        'csv_url':f'/api/research/datasets/{dataset_id}/csv'})
    import io
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['research_query','observed_entity','period','value','growth_rate','unit','indicator_code','source_url','scope'])
    for idx, row in enumerate(rows):
        safe_query = "'"+query if query.lstrip().startswith(('=','+','-','@')) else query
        prev_val = float(rows[idx-1]['value']) if idx > 0 else float(row['value'])
        growth_pct = round(((float(row['value']) - prev_val) / max(1e-9, abs(prev_val))) * 100.0, 2) if idx > 0 else 0.0
        writer.writerow([safe_query,row['observed_entity'],row['period'],row['value'],growth_pct,indicator[2],indicator[0],row['source_url'],'national_reference'])
    atomic_text(storage()/f'{dataset_id}.csv','\ufeff'+output.getvalue())
    atomic_text(storage()/f'{dataset_id}.json',json.dumps(report,ensure_ascii=False,allow_nan=False))
    return report
