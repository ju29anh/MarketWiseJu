"""Bounded, concurrent discovery through every configured source."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import urlencode, quote, urlsplit
import re
import xml.etree.ElementTree as ET

from core.config import settings
from services.research_evidence import subject_context, summarize


def collect(name, query):
    from services.research import fetch_json, fetch_text, add_source, relevant_title, plain, _unwrap_ddg_url, provider_failure
    sources = []
    def add(title, url, excerpt=''):
        from services.subject_matching import assess_match
        if name != 'Wikidata' and assess_match(query,plain(title or ''),plain(excerpt or ''))[0] == 'unrelated':
            return
        add_source(sources, title=title, url=url, excerpt=excerpt, provider=name, query=query)
    try:
        if name == 'Wikipedia':
            for lang in ('vi', 'en'):
                data = fetch_json(f'https://{lang}.wikipedia.org/w/rest.php/v1/search/page?' + urlencode({'q': query, 'limit': 6}))
                for item in data.get('pages', [])[:6]:
                    if relevant_title(query, item.get('title', '')):
                        add(item.get('title'), f'https://{lang}.wikipedia.org/wiki/' + quote(str(item.get('key', '')), safe=''), item.get('excerpt', ''))
                if sources: break
        elif name == 'DuckDuckGo Web':
            ctx = subject_context(query)
            searches = [query]
            if ctx['category'] == 'Education & EdTech': searches.append(f'"{query}" {ctx["search_suffix"]}')
            for search in searches:
                html = fetch_text('https://html.duckduckgo.com/html/', form_data={'q': search, 'kl': 'vn-vi'})
                blocks = re.findall(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', html, re.S)
                for url, title, excerpt in blocks[:10]: add(title, _unwrap_ddg_url(url), excerpt)
            if not sources:
                data = fetch_json('https://api.duckduckgo.com/?' + urlencode({'q': query, 'format': 'json', 'no_html': 1, 'skip_disambig': 1}))
                if data.get('AbstractText'): add(data.get('Heading') or query, data.get('AbstractURL'), data['AbstractText'])
        elif name == 'Bing Web':
            text = fetch_text('https://www.bing.com/search?' + urlencode({'q': '"'+query+'"', 'format':'rss', 'setlang':'vi'}))
            for item in ET.fromstring(text).findall('.//item')[:10]:
                add(item.findtext('title'),item.findtext('link'),item.findtext('description') or '')
        elif name == 'Google News':
            text = fetch_text('https://news.google.com/rss/search?' + urlencode({'q': f'"{query}"', 'hl': 'vi', 'gl': 'VN', 'ceid': 'VN:vi'}))
            items = ET.fromstring(text).findall('.//item')[:12]
            if not items and len(query.split()) >= 3:
                text = fetch_text('https://news.google.com/rss/search?' + urlencode({'q': query, 'hl': 'vi', 'gl': 'VN', 'ceid': 'VN:vi'}))
                items = ET.fromstring(text).findall('.//item')[:12]
            for item in items:
                title, url = item.findtext('title') or '', item.findtext('link') or ''
                source = item.find('source')
                publisher = source.text if source is not None else ''
                description = item.findtext('description') or title
                add(title, url, plain(title if re.search(r'<(?:ol|li)\b',description,re.I) else description))
                if sources and sources[-1]['url'] == url:
                    sources[-1]['published_at'] = item.findtext('pubDate') or None
                    sources[-1]['publisher'] = publisher
                    sources[-1]['publisher_url'] = source.attrib.get('url') if source is not None else None
        elif name == 'Brave Search':
            data = fetch_json('https://api.search.brave.com/res/v1/web/search?' + urlencode({'q': query, 'count': 12, 'safesearch': 'strict', 'search_lang': 'vi'}), {'X-Subscription-Token': settings.brave_search_api_key.get_secret_value().strip()})
            for item in data.get('web', {}).get('results', [])[:12]: add(item.get('title'), item.get('url'), item.get('description', ''))
        elif name == 'Tavily':
            data = fetch_json('https://api.tavily.com/search', {'Authorization': 'Bearer ' + settings.tavily_api_key.get_secret_value().strip()}, payload={
                'query': query, 'topic': 'general', 'search_depth': 'basic', 'max_results': 12,
                'include_answer': False, 'include_raw_content': False, 'include_images': False, 'auto_parameters': False, 'safe_search': True})
            for item in data.get('results', [])[:12]: add(item.get('title'), item.get('url'), item.get('content', ''))
        elif name == 'OpenAlex Research':
            data = fetch_json('https://api.openalex.org/works?' + urlencode({'search': query, 'per-page': 8}))
            for item in data.get('results', [])[:8]:
                loc = item.get('primary_location') or {}
                abstract = item.get('abstract_inverted_index') or {}
                words = sorted((position, word) for word, positions in abstract.items() for position in positions)[:160]
                excerpt = ' '.join(word for _, word in words)
                add(item.get('title'), loc.get('landing_page_url') or item.get('doi') or item.get('id'), excerpt or f"Tài liệu nghiên cứu: {item.get('title', '')}. Năm xuất bản: {item.get('publication_year') or 'chưa rõ'}.")
                if sources: sources[-1]['published_at'] = item.get('publication_date')
        elif name == 'Wikidata':
            for lang in ('vi', 'en'):
                data = fetch_json('https://www.wikidata.org/w/api.php?' + urlencode({'action': 'wbsearchentities', 'format': 'json', 'search': query, 'language': lang, 'uselang': 'vi', 'type': 'item', 'limit': 5}))
                for item in data.get('search', [])[:5]:
                    identity = str(item.get('id', ''))
                    if re.fullmatch(r'Q[1-9][0-9]*', identity): add(item.get('label', identity), 'https://www.wikidata.org/wiki/' + identity, item.get('description', ''))
                if sources: break
        return sources, {'name': name, 'status': 'ok' if sources else 'no_results'}
    except Exception as error:
        return sources, {'name': name, 'status': 'partial' if sources else provider_failure(error)}


def discover(query, fast=False):
    from services.research import provider_configuration
    config = provider_configuration()
    specs = [p for p in config['providers'] if p.get('kind') != 'synthesis']
    enabled = [p['name'] for p in specs if p['configured']]
    providers = [{'name': p['name'], 'status': 'not_configured' if p['requires_key'] else 'disabled'} for p in specs if not p['configured']]
    sources, seen = [], set()
    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = [executor.submit(collect, name, query) for name in enabled]
        for future in futures:
            items, status = future.result()
            providers.append(status)
            for item in items:
                canonical = item['url'].rstrip('/')
                if canonical in seen: continue
                seen.add(canonical)
                item['source_id'] = f'S{len(sources)+1}'
                sources.append(item)
    from services.subject_matching import prepare_sources
    from services.subject_report import make_report
    from services.market_report import build_report
    sources, excluded = prepare_sources(query,sources)
    if settings.research_fetch_pages and not fast:
        from services.source_reader import enrich_sources
        sources = enrich_sources(query,sources)
    # Numeric excerpts and comparison criteria also exclude other product variants.
    result = summarize(query, [s for s in sources if s['match_status']=='exact'])
    entity_report = None if fast else make_report(query,sources,excluded)
    quant_report = None if fast else build_report(query,sources,result)
    if entity_report and quant_report and quant_report.get('training_data'):
        entity_report['dataset_id'] = quant_report['dataset_id']
        entity_report['csv_url'] = quant_report['csv_url']
    advisor_context_id = None
    if not fast:
        from services.advisor import save_research_context
        advisor_context_id = save_research_context(query, sources)
    return {'query': query, 'search_query': query, 'checked_at': datetime.now(timezone.utc).isoformat(),
            'sources': sources, 'providers': providers, 'advisor_context_id': advisor_context_id,
            'status': 'needs_review' if sources else 'insufficient_evidence',
            'web_search_configured': config['web_search_configured'], 'market_analysis': result, 'entity_report': entity_report, 'report': quant_report,
            'next_steps': result['dataset_readiness']['requirements'],
            'notice': 'Kết quả là tài liệu được tìm thấy và số liệu trích từ nguồn. Nguồn có uy tín không tự xác nhận mọi nhận định trong bài viết.'}
