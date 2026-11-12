"""Reports about the requested subject, with auditable quotations for every claim."""
import csv
import io
import json
import re
import uuid
from datetime import datetime, timezone
from services.research_evidence import key, subject_context

GROUPS = ('overview', 'market', 'pricing', 'risks')
TERMS = {
    'market': ('thi truong','canh tranh','khach hang','doanh so','thi phan','nhu cau','tuyen sinh','chi tieu','market','sales','consumer','launch','ra mat','phan phoi'),
    'pricing': ('gia ban','gia niem yet','muc gia','dinh gia','gia tu','gia khoi diem','hoc phi','hoc bong','chi phi','price','pricing','cost','usd','vnd','vnđ'),
    'risks': ('rui ro','thach thuc','han che','canh bao','ro ri','tin don','du kien','chua','risk','challenge','rumor','leak','unconfirmed','expected','could','may '),
}
RUMOR = ('ro ri','tin don','lo dien','he lo','du kien','sap ra mat','chua xac nhan','leak','rumor','unconfirmed','expected','could','prototype')


def contains_terms(text, terms):
    text = key(text)
    return any(re.search(r'(?<!\w)' + re.escape(key(term.strip())) + r'(?!\w)', text) for term in terms)


def relevant_section(quote, group):
    if group == 'overview':
        return True
    return contains_terms(quote, TERMS[group]) or (group == 'pricing' and bool(
        re.search(r'(?:\d[\d., ]*\s*(?:đồng|dong|vnd|usd|eur|€|\$|£)|[€$£]\s*\d|\bgia\s+\d)', key(quote))))


def items(draft, name, limit=6):
    value = (draft or {}).get(name, [])
    return value[:limit] if isinstance(value, list) else []


def normalized(text):
    return ' '.join(str(text).split()).casefold()


def evidence_text(source):
    return '\n'.join(str(source.get(k) or '') for k in ('title','excerpt','content'))


def risk_level(source, quote):
    text = key(source['title']+' '+quote)
    return 'unconfirmed' if contains_terms(text, RUMOR) else 'reported'


def validate_claim(raw, index, query, *, action=False):
    if not isinstance(raw, dict):
        return None
    source = index.get(raw.get('source_id'))
    if not source or source.get('match_status') != 'exact':
        return None
    quote = ' '.join(str(raw.get('quote') or '').split())[:700]
    text = ' '.join(str(raw.get('text') or '').split())[:650]
    title = ' '.join(str(raw.get('title') or '').split())[:100]
    if len(quote) < 20 or not text or not title or normalized(quote) not in normalized(evidence_text(source)):
        return None
    kind = 'inference' if action or raw.get('kind') == 'inference' else 'fact'
    if kind == 'fact':
        numbers = lambda value: {re.sub(r'\D','',n) for n in re.findall(r'\d+(?:[.,]\d+)*',value)}
        if not numbers(title+' '+text).issubset(numbers(quote+' '+query)):
            return None
    result = {'title': title, 'text': text, 'source_id': source['source_id'], 'quote': quote,
              'kind': kind, 'evidence_status': risk_level(source,quote)}
    if action:
        result['measure'] = str(raw.get('measure') or 'Đối chiếu kết quả với tài liệu gốc trước khi triển khai.')[:250]
    return result


def excerpts(query, source):
    body = source.get('content') or source.get('excerpt') or source['title']
    candidates = [s.strip(' \t\r\n•–-') for s in re.split(r'\n+|(?<=[.!?])\s+(?=[A-ZÀ-Ỹ])', body)]
    from services.subject_matching import assess_match
    good = [s for s in candidates if 30 <= len(s) <= 650 and assess_match(query, s)[0] == 'exact']
    return good[:2] or [source.get('excerpt') or source['title']]


def extracted_claim(query, source, group='overview'):
    candidates = excerpts(query,source)
    if group != 'overview':
        candidates = [q for q in candidates if relevant_section(q,group)]
    if not candidates:
        return None
    quote = candidates[0][:650]
    return {'title': source['title'][:100], 'text': quote, 'source_id': source['source_id'], 'quote': quote,
            'kind':'fact', 'evidence_status':risk_level(source,quote)}


def make_report(query, sources, excluded_count=0):
    from services.grounded_writer import write_draft
    exact = [s for s in sources if s['match_status'] == 'exact']
    variants = [s for s in sources if s['match_status'] == 'variant']
    context = subject_context(query,sources)
    # Source readers and writers receive exact-identity documents only.
    draft, method = write_draft(query,context,exact)
    index = {s['source_id']:s for s in exact}
    sections, rejected = {}, 0
    for group in GROUPS:
        claims, seen = [], set()
        for raw in items(draft,group):
            claim = validate_claim(raw,index,query)
            if claim and relevant_section(claim['quote'],group) and normalized(claim['text']) not in seen:
                seen.add(normalized(claim['text']))
                claims.append(claim)
            else:
                rejected += 1
        if not claims:
            for source in exact:
                claim = extracted_claim(query,source,group)
                if claim and normalized(claim['text']) not in seen:
                    claims.append(claim)
                    seen.add(normalized(claim['text']))
                if len(claims) == (4 if group == 'overview' else 3):
                    break
        sections[group] = claims
    actions = []
    for raw in items(draft,'actions',4):
        action = validate_claim(raw,index,query,action=True)
        if action:
            actions.append(action)
        else:
            rejected += 1
    if not actions:
        rumor = next((c for c in sections['overview'] if c['evidence_status']=='unconfirmed'),None)
        price = next(iter(sections['pricing']),None)
        if rumor:
            actions.append({**rumor,'kind':'inference','title':'Chờ xác nhận trước khi chốt thông điệp bán hàng',
                'text':f'Nguồn đang mô tả thông tin chưa xác nhận về {query}. Chỉ dùng các chi tiết đã được công bố đúng phiên bản khi tư vấn hoặc chạy chiến dịch.',
                'measure':'Danh sách đặc điểm đã có văn bản công bố, kèm phiên bản và ngày kiểm tra.'})
        if price:
            actions.append({**price,'kind':'inference','title':'Xác minh thông tin giá và chi phí',
                'text':f'Đọc tài liệu “{index[price["source_id"]]["title"]}” để kiểm tra giá, điều kiện áp dụng và thời điểm. Chỉ lập bảng đối chiếu khi đã có mức giá cùng phiên bản, đơn vị và thị trường.',
                'measure':'Bảng giá có phiên bản, đơn vị, thời điểm, điều kiện và đường dẫn gốc.'})
    missing = [str(x)[:220] for x in items(draft,'missing',5) if isinstance(x,str)]
    if not missing:
        missing = ([f'Chưa tìm được tài liệu đủ khớp để mô tả chính xác “{query}”.'] if not exact else
                   ['Chưa có chuỗi doanh số, nhu cầu hoặc chuyển đổi theo thời gian của đúng đối tượng để dự báo.'])
        if not sections['pricing']:
            missing.append('Chưa có giá hoặc học phí đủ ngữ cảnh về đơn vị, phiên bản và thời điểm.')
    actual_claims = sum(len(v) for v in sections.values())
    status = 'with_findings' if exact and actual_claims else 'related_only' if variants else 'insufficient_evidence'
    report = {'version':2,'dataset_id':uuid.uuid4().hex,'query':query,'created_at':datetime.now(timezone.utc).isoformat(),
        'status':status,'category':context['category'],'category_label':context['label'],
        'identity':{'name':query,'status':status,'exact_sources':len(exact),'related_sources':len(variants),
                    'official_sources':sum(s['source_kind']=='official' for s in exact),
                    'message':f'Có {len(exact)} tài liệu khớp tên đã nhập. Các thông tin bên dưới giữ dẫn chứng để đối chiếu.' if exact else
                              'Các kết quả hiện chỉ nhắc tới phiên bản hoặc đối tượng liên quan; chưa xác nhận đúng tên đã nhập.' if variants else
                              'Chưa tìm được nguồn khớp tên. Hãy bổ sung tên đầy đủ, phiên bản hoặc địa điểm; không tạo thông tin thay thế.'},
        'sections':sections,'actions':actions,'missing':missing,
        'related_subjects':list(dict.fromkeys(s['matched_name'] for s in variants)),
        'data_status':{'training_ready':False,'exact_documents':len(exact),'article_documents':sum(bool(s.get('content')) for s in exact),
                       'excluded_documents':excluded_count,'supported_claims':actual_claims,
                       'reason':'Tài liệu và trích đoạn mô tả đối tượng; chưa phải chuỗi quan sát đã kiểm chứng để dự báo doanh số hoặc thị phần.'},
        'processing':{'mode':method,'rejected_claims':rejected},
        'csv_url':'','notice':'Thông tin nguồn công bố, suy luận phân tích và đề xuất được gắn nhãn riêng. Tin đồn không được coi là xác nhận chính thức.'}
    persist_report(report,index)
    return report


def persist_report(report,index):
    from services.market_report import storage, atomic_text
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['entity','section','claim','kind','evidence_quote','source_url','published_at','review_status'])
    def cell(value):
        text = str(value or '')
        return "'"+text if text.lstrip().startswith(('=','+','-','@')) else text
    for group, claims in {**report['sections'],'actions':report['actions']}.items():
        for claim in claims:
            source = index[claim['source_id']]
            writer.writerow([cell(v) for v in [report['query'],group,claim['text'],claim['kind'],claim['quote'],source['url'],source.get('published_at'), 'needs_review']])
    report['csv_url'] = f'/api/research/datasets/{report["dataset_id"]}/csv'
    atomic_text(storage()/f'{report["dataset_id"]}.csv','\ufeff'+output.getvalue())
    atomic_text(storage()/f'{report["dataset_id"]}.json',json.dumps(report,ensure_ascii=False,allow_nan=False))
