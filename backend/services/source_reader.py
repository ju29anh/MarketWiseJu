"""Bounded public HTTPS reader: pin DNS resolution and revalidate every redirect."""
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from http.client import HTTPSConnection
import ipaddress
import re
import socket
import ssl
from urllib.parse import urlsplit, urljoin


class ArticleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'nav', 'footer', 'header', 'noscript', 'svg', 'form'):
            self.skip += 1
        if tag in ('p', 'h1', 'h2', 'h3', 'li', 'tr', 'div') and not self.skip:
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'nav', 'footer', 'header', 'noscript', 'svg', 'form'):
            self.skip = max(0, self.skip-1)

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def text(self):
        return '\n'.join(' '.join(line.split()) for line in ''.join(self.parts).splitlines() if line.strip())


def public_addresses(host):
    addresses = list(dict.fromkeys(row[4][0] for row in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)))
    if not addresses or any(not ipaddress.ip_address(addr).is_global for addr in addresses):
        raise ValueError('Non-public destination')
    return addresses


class PinnedHTTPS(HTTPSConnection):
    def __init__(self, host, address):
        super().__init__(host, timeout=3, context=ssl.create_default_context())
        self.address = address

    def connect(self):
        raw = socket.create_connection((self.address, 443), timeout=self.timeout)
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except BaseException:
            raw.close()
            raise


def read_public_article(url):
    for _ in range(3):
        parsed = urlsplit(url)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443):
            raise ValueError('Unsupported article URL')
        if '.' not in parsed.hostname or parsed.hostname.endswith(('.local', '.localhost', '.internal')):
            raise ValueError('Non-public destination')
        addresses = public_addresses(parsed.hostname)
        connection = PinnedHTTPS(parsed.hostname, addresses[0])
        try:
            connection.request('GET', (parsed.path or '/') + ('?'+parsed.query if parsed.query else ''),
                               headers={'User-Agent': 'Mozilla/5.0 MarketWise/3.0', 'Accept': 'text/html', 'Accept-Encoding': 'identity'})
            response = connection.getresponse()
            if response.status in (301, 302, 303, 307, 308):
                url = urljoin(url, response.getheader('Location', ''))
                continue
            if response.status != 200 or 'text/html' not in response.getheader('Content-Type', '').lower():
                raise ValueError('Article unavailable')
            if response.getheader('Content-Encoding', 'identity') != 'identity':
                raise ValueError('Compressed response not requested')
            data = response.read(600_001)
            if len(data) > 600_000:
                raise ValueError('Article too large')
            parser = ArticleText()
            parser.feed(data.decode('utf-8', 'replace'))
            return parser.text()[:24000]
        finally:
            connection.close()
    raise ValueError('Too many redirects')


def enrich_sources(query, sources):
    from services.research_evidence import key
    def enrich(source):
        if source.get('source_kind') == 'headline' or source.get('match_status') != 'exact':
            return source
        item = dict(source)
        try:
            text = read_public_article(source['url'])
            # Find the topic inside the page rather than passing a site's navigation to synthesis.
            terms = re.findall(r'\w+', key(query))
            pattern = r'[\s\-]*'.join(re.escape(t) for t in terms)
            hits = list(re.finditer(pattern, key(text)))
            if hits:
                chunks = [text[max(0,m.start()-180):m.start()+2200] for m in hits[:4]]
                item['content'] = '\n'.join(dict.fromkeys(chunks))[:8500]
                item['content_status'] = 'article'
            else:
                item['content_status'] = 'snippet_only'
        except Exception:
            item['content_status'] = 'snippet_only'
        return item
    selected = [s for s in sources if s.get('match_status') == 'exact' and s.get('source_kind') != 'headline'][:6]
    with ThreadPoolExecutor(max_workers=6) as pool:
        enriched = {s['source_id']: s for s in pool.map(enrich, selected)}
    return [enriched.get(s['source_id'], s) for s in sources]
