"""Multi-source web research, news discovery, and market intelligence synthesis."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import datetime, timezone
from html import unescape
import ipaddress
import json
from pathlib import Path
import re
import threading
import unicodedata
from urllib.error import HTTPError
from urllib.parse import urlencode, quote, urlsplit, parse_qs
from urllib.request import Request, build_opener, HTTPRedirectHandler
import xml.etree.ElementTree as ET
import numpy as np

from core.config import settings, DATASETS_DIR, UPLOADS_DIR

slots = threading.BoundedSemaphore(4)

CATEGORY_VI_MAP = {
    "Technology & Gaming": "Công nghệ & Máy tính Gaming",
    "Smartphones & Mobile": "Điện thoại & Thiết bị di động",
    "Fashion & E-Commerce": "Thời trang & Thương mại điện tử",
    "Food & Beverage": "F&B & Đồ uống Đặc sản",
    "Beauty & Skincare": "Mỹ phẩm & Chăm sóc sắc đẹp",
    "Electric Vehicles": "Xe điện & Ô tô thông minh",
    "Education & EdTech": "Giáo dục & Đào tạo (EdTech)",
    "Healthcare & Fitness": "Sức khỏe, Y tế & Thể chất",
    "Smart Home & IoT": "Nhà thông minh & Thiết bị Gia dụng",
    "Digital Services & SaaS": "Dịch vụ Số, AI & Phần mềm SaaS",
    "FMCG & Consumer Goods": "Hàng Tiêu Dùng Nhanh (FMCG)",
    "Real Estate & Housing": "Bất Động Sản & Đô Thị",
    "Tourism & Hospitality": "Du Lịch, Khách Sạn & Hàng Không",
    "FinTech & Digital Finance": "Tài Chính, Ngân Hàng & Đầu Tư",
    "Logistics & Supply Chain": "Logistics & Chuỗi Cung Ứng",
    "Audio & Consumer Electronics": "Thiết Bị Âm Thanh & Điện Tử",
}


def normalize(value):
    value = unicodedata.normalize('NFD', str(value).casefold().strip()).replace('đ', 'd')
    return ' '.join(''.join(c for c in value if unicodedata.category(c) != 'Mn').split())


def plain(value):
    return unescape(re.sub(r'<[^>]*>', '', str(value)))[:1000].strip()


def relevant_title(query, title):
    # Preserve C++, C# and one-letter topics such as R; symbols can identify a topic.
    words = lambda value: {word.rstrip('s') if len(word) > 3 else word
                           for word in re.findall(r'[^\W_]+(?:\+\+|#)?', normalize(value))}
    wanted = words(query)
    return bool(wanted) and len(wanted & words(title)) / len(wanted) >= 0.7


def safe_url(value):
    try:
        url = urlsplit(value)
        if url.scheme != 'https' or not url.hostname or url.username or url.password or url.port not in (None, 443):
            return None
        host = url.hostname.lower()
        if '.' not in host or host.endswith(('.local', '.localhost', '.internal')):
            return None
        try:
            if not ipaddress.ip_address(host).is_global:
                return None
        except ValueError:
            pass
        return value
    except (ValueError, TypeError):
        return None


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def fetch_json(url, headers=None, *, payload=None):
    # Enforce fixed provider hosts and paths, including when adding a new caller.
    parsed = urlsplit(url)
    allowed = {
        ('vi.wikipedia.org', '/w/rest.php/v1/search/page'),
        ('en.wikipedia.org', '/w/rest.php/v1/search/page'),
        ('www.wikidata.org', '/w/api.php'),
        ('api.search.brave.com', '/res/v1/web/search'),
        ('api.tavily.com', '/search'),
        ('api.duckduckgo.com', '/'),
        ('api.openalex.org', '/works'),
    }
    if parsed.scheme != 'https' or parsed.netloc != parsed.hostname or (parsed.hostname, parsed.path) not in allowed:
        raise ValueError('Unsupported provider endpoint')
    request_headers = {'User-Agent': 'MarketWise/2.5 (source research)', **(headers or {})}
    body = None
    if payload is not None:
        body = json.dumps(payload).encode('utf-8')
        request_headers['Content-Type'] = 'application/json'
    request = Request(url, data=body, headers=request_headers)
    with build_opener(NoRedirect).open(request, timeout=6) as response:
        body = response.read(1_000_001)
        if len(body) > 1_000_000:
            raise ValueError('Provider response too large')
        data = json.loads(body)
        if not isinstance(data, dict) or data.get('error'):
            raise ValueError('Invalid provider response')
        return data


def fetch_text(url, headers=None, *, form_data=None):
    parsed = urlsplit(url)
    allowed = {
        ('html.duckduckgo.com', '/html/'),
        ('news.google.com', '/rss/search'),
        ('www.bing.com', '/search'),
    }
    if parsed.scheme != 'https' or parsed.netloc != parsed.hostname or (parsed.hostname, parsed.path) not in allowed:
        raise ValueError('Unsupported provider endpoint')
    request_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 MarketWise/2.5',
        **(headers or {})
    }
    body = None
    if form_data is not None:
        body = urlencode(form_data).encode('utf-8')
        request_headers['Content-Type'] = 'application/x-www-form-urlencoded'
    request = Request(url, data=body, headers=request_headers)
    with build_opener(NoRedirect).open(request, timeout=6) as response:
        raw = response.read(1_000_001)
        if len(raw) > 1_000_000:
            raise ValueError('Provider response too large')
        return raw.decode('utf-8', errors='ignore')


def provider_failure(error):
    if isinstance(error, HTTPError):
        if error.code in (401, 403):
            return 'authentication_failed'
        if error.code in (429, 432, 433):
            return 'rate_limited'
    return 'unavailable'


def provider_configuration():
    specs = [
        ('Wikipedia', settings.research_wikipedia, False, 'Bách khoa & tổng quan thực thể'),
        ('DuckDuckGo Web', settings.research_duckduckgo, False, 'Tìm kiếm web rộng'),
        ('Bing Web', settings.research_duckduckgo, False, 'Tìm kiếm web bổ sung và đối chiếu tên'),
        ('Google News', settings.research_google_news, False, 'Tin tức; kiểm tra nhà xuất bản gốc'),
        ('OpenAlex Research', settings.research_openalex, False, 'Tài liệu & ấn phẩm nghiên cứu'),
        ('Wikidata', settings.research_wikidata, False, 'Định danh và đồ thị tri thức'),
        ('Brave Search', bool(settings.brave_search_api_key.get_secret_value().strip()), True, 'Tìm kiếm bổ sung'),
        ('Tavily', bool(settings.tavily_api_key.get_secret_value().strip()), True, 'Tìm kiếm bổ sung'),
    ]
    return {'web_search_configured': any(p[1] for p in specs), 'providers': [
        {'name': name, 'configured': bool(enabled), 'requires_key': needs_key, 'role': role}
        for name, enabled, needs_key, role in specs
    ]}


def _unwrap_ddg_url(href: str) -> str:
    href = unescape(href or '').strip()
    if href.startswith('//'):
        href = 'https:' + href
    try:
        parsed = urlsplit(href)
        if 'duckduckgo.com' in (parsed.hostname or '') and parsed.query:
            qs = parse_qs(parsed.query)
            if 'uddg' in qs and qs['uddg']:
                return qs['uddg'][0]
    except Exception:
        pass
    return href


def add_source(sources, *, title, url, excerpt, provider, query):
    url = safe_url(url)
    if not url:
        return
    # Fragments of the same document should not appear as independent evidence.
    url = url.split('#', 1)[0]
    if any(source['url'].rstrip('/') == url.rstrip('/') for source in sources):
        return
    from services.ai_engine import score_web_source_credibility
    cred = score_web_source_credibility(url, provider, excerpt or '')
    sources.append({
        'title': plain(title or 'Nguồn chưa có tiêu đề'),
        'url': url,
        'excerpt': plain(excerpt or ''),
        'provider': provider,
        'identity_match': normalize(str(title or '')) == normalize(query),
        'verified': False,
        'credibility_score': cred['credibility_score'],
        'credibility_tier': cred['credibility_tier'],
        'is_reputable': cred['is_reputable'],
        'domain': cred['domain'],
    })


def synthesize_market_analysis(query, sources):
    from services.research_evidence import summarize
    return summarize(query, sources)


def discover(query, fast=False):
    from services.research_collectors import discover as collect
    return collect(query, fast=True) if fast else collect(query)


def compare_profiles(left, right):
    from services.research_evidence import compare
    return compare(left, right)
