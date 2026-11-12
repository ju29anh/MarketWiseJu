"""Evidence summaries: source excerpts are observations, never invented time series."""
import re
import math
import unicodedata
from urllib.parse import urlsplit
from collections import Counter
from datetime import datetime, timezone


def key(text):
    text = unicodedata.normalize('NFD', str(text).casefold()).replace('đ', 'd')
    return ''.join(c for c in text if unicodedata.category(c) != 'Mn')


def subject_context(query, sources=()):
    q = key(query)
    if any(t in query.casefold() for t in ('váy', 'chân váy', 'đầm xòe', 'đầm nữ')) or any(re.search(r'\b' + re.escape(t) + r'\b', q) for t in ('vay xoe', 'chan vay', 'vay lien', 'dam xoe', 'dam nu', 'skirt', 'dress')):
        q += ' thoi trang'
    if any(t in q for t in ('dai hoc', 'truong dh', 'university', 'hoc vien', 'cao dang', 'college', 'canh sat nhan dan', 'an ninh nhan dan', 'bach khoa', 'su pham', 'y duoc', 'ngoai thuong', 'tdmu', 'bdu', 'hutech', 'ueh', 'rmit')):
        return {'category': 'Education & EdTech', 'label': 'Giáo dục đại học & tuyển sinh',
                'focus': 'Năng lực đào tạo, tuyển sinh và lựa chọn trường; không đồng nhất với thị trường khóa học trực tuyến.',
                'criteria': ['Học phí & học bổng', 'Tuyển sinh & điểm chuẩn', 'Ngành & chương trình đào tạo', 'Kiểm định chất lượng', 'Quy mô sinh viên', 'Việc làm sau tốt nghiệp'],
                'search_suffix': 'tuyển sinh học phí báo cáo công khai kiểm định',
                'requirements': ['Số nhập học theo năm và ngành', 'Học phí cùng chương trình, đơn vị và năm học', 'Chỉ tiêu, điểm chuẩn và phương thức tuyển sinh', 'Tỷ lệ việc làm kèm cỡ mẫu khảo sát']}
    groups = [
        (('tai nghe', 'airpod', 'airpods', 'earphone', 'headphone', 'tws', 'sony wh', 'bose', 'sennheiser', 'marshall', 'jbl', 'harman kardon', 'loa bluetooth', 'soundbar', 'loa keo', 'am thanh', 'micro', 'karaoke', 'edifier', 'soundcore'), 'Audio & Consumer Electronics', 'Âm thanh & điện tử tiêu dùng', ['Giá bán & phân khúc', 'Chất âm & chống ồn', 'Pin & kết nối', 'Phân phối & bảo hành']),
        (('robot hut bui', 'roborock', 'ecovacs', 'dreame', 'nha thong minh', 'smart home', 'iot', 'camera an ninh', 'camera wifi', 'ezviz', 'imou', 'khoa cua thong minh', 'may loc khong khi', 'may loc nuoc', 'karofi', 'kangaroo', 'noi chien khong dau', 'do gia dung thong minh'), 'Smart Home & IoT', 'Nhà thông minh & thiết bị IoT', ['Giá bán', 'Tính năng tự động hóa', 'Hệ sinh thái & ứng dụng', 'Bảo hành & hậu mãi']),
        (('ca phe', 'tra sua', 'coffee', 'phela', 'phe la', 'highland', 'katinat', 'phuc long', 'starbucks', 'nuoc ep', 'do uong', 'thuc pham', 'nha hang', 'banh mi', 'juice', 'restaurant', 'beverage', 'quan an', 'matcha', 'tra o long', 'kombucha', 'lau', 'nuong', 'pho', 'bun bo', 'com tam', 'ga ran', 'pizza'), 'Food & Beverage', 'Ẩm thực & đồ uống', ['Giá bán & thực đơn', 'Cửa hàng & địa bàn', 'Sản phẩm & khách hàng', 'Doanh thu & nhu cầu']),
        (('iphone', 'dien thoai', 'samsung', 'xiaomi', 'smartphone', 'oppo', 'vivo', 'realme', 'redmi', 'honor', 'huawei', 'galaxy s', 'galaxy z', 'di dong', 'poco', 'oneplus', 'pixel', 'ipad', 'tablet', 'may tinh bang'), 'Smartphones & Mobile', 'Điện thoại & thiết bị di động', ['Giá bán', 'Cấu hình & tính năng', 'Phân phối & bảo hành', 'Doanh số & thị phần']),
        (('du lich', 'khach san', 'tourism', 'resort', 'vinpearl', 'sun world', 'hang khong', 'vietnam airlines', 'vietjet', 'homestay', 'nghi duong', 've may bay', 'phu quoc', 'da nang', 'nha trang', 'da lat', 'sapa', 'hoi an', 'ha long', 'lu hanh', 'traveloka', 'booking'), 'Tourism & Hospitality', 'Du lịch & lưu trú', ['Giá & chi phí', 'Địa điểm & dịch vụ', 'Lượng khách', 'Công suất & mùa vụ']),
        (('vinfast', 'xe dien', 'tesla', 'byd', 'vf3', 'vf 3', 'vf5', 'vf6', 'vf7', 'vf8', 'vf9', 'o to dien', 'xe may dien', 'wuling', 'ioniq', 'xanh sm', 'dat bike', 'yadea', 'tram sac', 'pin xe dien'), 'Electric Vehicles', 'Xe điện & phương tiện xanh', ['Giá & chi phí vận hành', 'Thông số kỹ thuật', 'Hạ tầng & bảo hành', 'Doanh số']),
        (('my pham', 'cocoon', 'skincare', 'son duong', 'son moi', 'kem chong nang', 'serum', 'sua rua mat', 'la roche', 'cerave', 'the ordinary', 'innisfree', 'cham soc da', 'nuoc hoa', 'toner', 'retinol', 'niacinamide', 'bha', 'skin1004', 'anessa', 'bioderma', 'hasaki', 'guardian'), 'Beauty & Skincare', 'Mỹ phẩm & chăm sóc da', ['Giá bán', 'Thành phần & công dụng', 'Công bố & kiểm nghiệm', 'Phân phối']),
        (('laptop', 'gaming', 'may tinh', 'nvidia', 'asus', 'rog', 'lenovo', 'legion', 'acer', 'predator', 'msi', 'dell', 'macbook', 'hp', 'man hinh', 'ban phim', 'chuot gaming', 'card do hoa', 'rtx', 'ban dan', 'semiconductor', 'ps5', 'esports'), 'Technology & Gaming', 'Công nghệ & máy tính', ['Giá & cấu hình', 'Nhu cầu sử dụng', 'Phân phối & bảo hành', 'Cạnh tranh']),
        (('ngan hang', 'tai chinh', 'fintech', 'momo', 'zalopay', 'vnpay', 'vietcombank', 'techcombank', 'mbbank', 'vpbank', 'tin dung', 'chung khoan', 'vi dien tu', 'acb', 'bidv', 'vietinbank', 'tpbank', 'tcbs', 'ssi', 'vndirect', 'bao hiem', 'cho vay', 'vay von'), 'FinTech & Digital Finance', 'Tài chính & ngân hàng số', ['Dịch vụ & chi phí', 'Khách hàng', 'Rủi ro & quy định', 'Mạng lưới']),
        (('logistics', 'van chuyen', 'kho van', 'chuoi cung ung', 'giao hang', 'ghtk', 'ghn', 'viettel post', 'cang bien', 'xuat nhap khau', 'fulfillment', 'j&t', 'spx', 'dhl', 'fedex', 'gemadept', 'kho lanh', 'van tai'), 'Logistics & Supply Chain', 'Vận tải & chuỗi cung ứng', ['Nhu cầu vận chuyển', 'Chi phí', 'Năng lực phục vụ', 'Thời gian giao nhận']),
        (('bat dong san', 'vinhomes', 'can ho', 'nha o', 'chung cu', 'dat nen', 'biet thu', 'masterise', 'ecopark', 'khu do thi', 'nha pho', 'khang dien', 'nam long', 'novaland', 'shophouse', 'nha o xa hoi', 'van phong cho thue'), 'Real Estate & Housing', 'Bất động sản & nhà ở', ['Giá & khả năng chi trả', 'Vị trí', 'Nguồn cung & nhu cầu', 'Pháp lý']),
        (('phan mem', 'saas', 'fpt', 'crm', 'dich vu so', 'erp', 'cloud', 'tri tue nhan tao', 'chuyen doi so', 'misa', 'kiotviet', 'base.vn', 'an ninh mang', 'chatgpt', 'openai', 'sapo', 'haravan', 'cybersecurity', 'big data'), 'Digital Services & SaaS', 'Phần mềm & dịch vụ số', ['Nhu cầu số hóa', 'Giá & tính năng', 'Khách hàng', 'Chất lượng dịch vụ']),
        (('suc khoe', 'benh vien', 'y te', 'fitness', 'nha thuoc', 'long chau', 'pharmacity', 'vinmec', 'tam anh', 'vnvc', 'phong kham', 'duoc pham', 'smartwatch', 'dong ho thong minh', 'apple watch', 'garmin', 'thuc pham chuc nang', 'nha khoa', 'gym', 'yoga', 'pickleball'), 'Healthcare & Fitness', 'Y tế & sức khỏe', ['Nhu cầu chăm sóc', 'Chi phí', 'Chất lượng chuyên môn', 'Khả năng tiếp cận']),
        (('thoi trang', 'quan ao', 'zara', 'uniqlo', 'coolmate', 'giay', 'bitis', 'nike', 'adidas', 'shopee', 'tiktok shop', 'lazada', 'local brand', 'routine', 'ivy moda', 'hoodie', 'sneaker', 'tui xach', 'streetwear'), 'Fashion & E-Commerce', 'Thời trang & thương mại điện tử', ['Phân khúc khách hàng', 'Giá bán', 'Kênh phân phối', 'Xu hướng tiêu dùng']),
        (('tieu dung nhanh', 'fmcg', 'mi hao hao', 'mi tom', 'mi goi', 'acecook', 'vinamilk', 'th true milk', 'masan', 'chinsu', 'omachi', 'unilever', 'sua tuoi', 'bach hoa xanh', 'winmart', 'nuoc mam', 'dau an', 'banh keo', 'nuoc ngot', 'pepsi', 'coca cola', 'thien long'), 'FMCG & Consumer Goods', 'Hàng tiêu dùng nhanh (FMCG)', ['Giá bán & độ phủ', 'Kênh siêu thị & tạp hóa', 'Tần suất mua lặp lại', 'Thị phần & thương hiệu']),
        (('khoa hoc', 'edtech', 'hoc truc tuyen', 'online learning', 'coursera', 'udemy', 'ielts', 'toeic', 'tieng anh', 'anh ngu', 'luyen thi', 'hoc lap trinh', 'e-learning', 'elsa', 'prep'), 'Education & EdTech', 'Giáo dục & công nghệ giáo dục (EdTech)', ['Học phí & gói khóa học', 'Chương trình & giảng viên', 'Học viên & tỷ lệ hoàn thành', 'Nền tảng & chứng chỉ']),
    ]
    for terms, category, label, criteria in groups:
        if any((t in q if (' ' in t or len(t) >= 6) else re.search(r'(?<!\w)' + re.escape(t) + r'(?!\w)', q)) for t in terms):
            return {'category': category, 'label': label, 'focus': f'Đối chiếu thông tin về {label.lower()} theo nguồn và thời điểm công bố.', 'criteria': criteria, 'search_suffix': 'báo cáo giá số liệu chính thức', 'requirements': ['Quan sát định lượng đúng đối tượng', 'Cùng đơn vị đo và kỳ thời gian', 'Ngày công bố và đường dẫn nguồn cho từng dòng']}
    return {'category': 'General Research', 'label': 'Nghiên cứu đối tượng & bối cảnh hoạt động',
            'focus': 'Xác định danh tính và lĩnh vực từ nguồn tìm được; chưa ép từ khóa vào một thị trường khi thiếu bằng chứng.',
            'criteria': ['Danh tính & phạm vi hoạt động', 'Sản phẩm hoặc dịch vụ', 'Địa điểm & thời gian', 'Chỉ tiêu định lượng có nguồn'],
            'search_suffix': 'thông tin báo cáo số liệu chính thức',
            'requirements': ['Xác định chỉ tiêu cần phân tích', 'Dữ liệu đúng đối tượng, đơn vị và thời kỳ', 'Đường dẫn và ngày công bố của mỗi quan sát']}


def extract_observations(query, sources):
    """Extract literal values only. Missing period/denominator remains missing."""
    rows, seen = [], set()
    pattern = re.compile(r'(?P<number>[+-]?\d+(?:[.,]\d+)*)(?:\s*)(?P<unit>tỷ\s*đồng|triệu\s*đồng|triệu\s*USD|nghìn\s*đồng|sinh\s*viên|học\s*viên|chỉ\s*tiêu|cửa\s*hàng|chi\s*nhánh|ngành\s*học|USD|VND|VNĐ|%)', re.I)
    for source in sources:
        text = source.get('excerpt', '')
        for match in pattern.finditer(text):
            literal = match.group(0)
            signature = (source['url'], literal)
            if signature in seen:
                continue
            seen.add(signature)
            numeric = match['number']
            if len(numeric) > 32:
                continue
            if re.fullmatch(r'[+-]?\d{1,3}(?:[.,]\d{3})+', numeric):
                numeric = numeric.replace('.', '').replace(',', '')
            elif ',' in numeric and '.' in numeric:
                numeric = numeric.replace('.', '').replace(',', '.')
            else:
                numeric = numeric.replace(',', '.')
            try:
                value = float(numeric)
                if not math.isfinite(value):
                    continue
            except ValueError:
                continue
            context = text[max(0, match.start()-90):min(len(text), match.end()+90)]
            years = sorted(set(re.findall(r'\b(?:19|20)\d{2}\b', context)))
            unit = match['unit'].lower()
            metric = 'Chỉ tiêu cần xác minh'
            if 'sinh' in unit or 'viên' in unit: metric = 'Quy mô người học'
            elif 'cửa' in unit or 'nhánh' in unit: metric = 'Mạng lưới hoạt động'
            elif 'ngành' in unit: metric = 'Số ngành đào tạo'
            elif 'chỉ' in unit: metric = 'Chỉ tiêu tuyển sinh'
            elif any(t in key(context) for t in ('hoc phi', 'tuition')): metric = 'Học phí (cần xác minh kỳ tính)'
            elif unit == '%': metric = 'Tỷ lệ (cần xác minh chỉ tiêu và mẫu số)'
            rows.append({'entity': query, 'metric': metric, 'value': value, 'unit': unit,
                         'period': years[0] if len(years) == 1 else None, 'raw_value': literal,
                         'context': context, 'source_url': source['url'], 'source_title': source['title'],
                         'provider': source['provider'], 'verified': False, 'review_status': 'needs_review'})
    return rows


def summarize(query, sources):
    ctx = subject_context(query, sources)
    observations = extract_observations(query, sources)
    criteria = []
    terms = {
        'Học phí & học bổng': ('hoc phi', 'hoc bong', 'tuition'),
        'Tuyển sinh & điểm chuẩn': ('tuyen sinh', 'diem chuan', 'nhap hoc'),
        'Ngành & chương trình đào tạo': ('nganh', 'chuong trinh', 'dao tao'),
        'Kiểm định chất lượng': ('kiem dinh', 'accredit', 'aun-qa', 'abet'),
        'Quy mô sinh viên': ('sinh vien', 'hoc vien', 'quy mo'),
        'Việc làm sau tốt nghiệp': ('viec lam', 'tot nghiep', 'employment'),
    }
    for label in ctx['criteria']:
        tokens = terms.get(label, tuple(key(label).split(' & ')))
        hits = [s for s in sources if any(t in key(s['title'] + ' ' + s.get('excerpt', '')) for t in tokens)]
        # Favor primary institutional documents over general summaries.
        hits.sort(key=lambda s: not (urlsplit(s['url']).hostname or '').endswith(('.edu.vn', '.gov.vn', '.edu', '.gov')))
        criteria.append({'label': label, 'status': 'Có tài liệu liên quan, cần đối chiếu nội dung' if hits else 'Chưa tìm thấy dữ liệu',
                         'sources': [{'title': s['title'], 'url': s['url'], 'excerpt': s.get('excerpt', '')} for s in hits[:3]]})
    counts = Counter(s['provider'] for s in sources)
    return {
        'query': query, 'detected_category': ctx['category'], 'detected_category_vi': ctx['label'],
        'recommended_dataset': None, 'matched_keyword': query, 'analysis_scope': ctx['focus'],
        'executive_summary': f"Đã tìm thấy {len(sources)} tài liệu liên quan đến “{query}” và {len(observations)} số liệu trong trích đoạn. "
                             + ctx['focus'] + ' Các số liệu cần được đối chiếu với tài liệu gốc trước khi sử dụng.',
        'criteria': criteria, 'observations': observations,
        'dataset_readiness': {'ready': False, 'status': 'needs_review' if observations else 'insufficient_data',
            'observed_rows': len(observations), 'verified_rows': 0,
            'reason': 'Trích đoạn tìm kiếm chưa xác nhận đầy đủ đối tượng, định nghĩa chỉ tiêu, đơn vị và thời kỳ. Không tự tạo thêm dòng hoặc gán số liệu của ngành cho đối tượng.',
            'requirements': ctx['requirements']},
        'market_signals': {'signal_score': None, 'signal_label': 'Độ phủ nguồn, không phải điểm chất lượng đối tượng',
            'total_sources': len(sources), 'news_count': counts['Google News'], 'web_count': sum(counts[p] for p in ('DuckDuckGo Web', 'Brave Search', 'Tavily')),
            'knowledge_count': counts['Wikipedia'] + counts['Wikidata'], 'academic_count': counts['OpenAlex Research'],
            'positive_signals': [], 'risk_signals': [], 'extracted_figures': [r['raw_value'] for r in observations], 'highlights': []},
        'benchmark_metrics': {'potential_score': None, 'avg_growth_pct': None, 'avg_rating': None, 'total_records': len(observations), 'dataset_title': 'Số liệu trích từ nguồn tìm kiếm; chờ kiểm chứng', 'top_competitors': [], 'price_stats': None},
        'strategic_takeaways': ctx['requirements'],
    }


def compare(left, right):
    lm = left.get('market_analysis') or summarize(left['query'], left.get('sources', []))
    rm = right.get('market_analysis') or summarize(right['query'], right.get('sources', []))
    labels = list(dict.fromkeys(c['label'] for c in lm['criteria'] + rm['criteria']))
    rows = []
    for label in labels:
        lc = next((c for c in lm['criteria'] if c['label'] == label), {'sources': []})
        rc = next((c for c in rm['criteria'] if c['label'] == label), {'sources': []})
        def value(c):
            return ' | '.join(s['excerpt'] or s['title'] for s in c['sources'][:2]) or 'Chưa có dữ liệu có nguồn'
        rows.append({'metric': label, 'left_value': value(lc), 'right_value': value(rc),
                     'left_sources': lc['sources'], 'right_sources': rc['sources'],
                     'diff': 'Đối chiếu cùng năm, đơn vị và chương trình; chưa xếp hạng'})
    enough = bool(left.get('sources') and right.get('sources'))
    return {'left': left, 'right': right, 'criteria': labels, 'comparison_matrix': rows,
            'shared_domains': [], 'conclusion': ('Đã tra cứu trực tiếp hai đối tượng. Bảng dưới đối chiếu tài liệu theo từng tiêu chí; số lượng bài viết không quyết định đối tượng nào tốt hơn.' if enough else 'Chưa đủ nguồn cho ít nhất một đối tượng. Vẫn hiển thị tài liệu tìm được; chưa kết luận bên nào tốt hơn.')}
