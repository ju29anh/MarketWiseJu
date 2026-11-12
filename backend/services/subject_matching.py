"""Identity matching keeps product generations and variants separate."""
import re
from urllib.parse import urlsplit
from services.research_evidence import key

VARIANTS = r'(?:pro\s*max|pro|ultra|fold|flip|lite|plus|mini|fe)'


def assess_match(query, title, excerpt=''):
    q = ' '.join(key(query).split())
    title_key, body = key(title), key(title + ' ' + excerpt)
    tokens = re.findall(r'[^\W_]+(?:\+\+|#)?', q)
    if not tokens:
        return 'unrelated', ''
    # A model number must be next to its name. "Xiaomi ... age 18" is not Xiaomi 18.
    if any(t.isdigit() for t in tokens):
        pattern = r'(?<!\w)' + r'[\s\-]*'.join(re.escape(t) for t in tokens) + r'(?!\d)'
        match = re.search(pattern, body)
        if not match:
            return 'unrelated', ''
        suffix = re.match(r'\s*(' + VARIANTS + r')\b', body[match.end():])
        has_variant = re.search(r'\b' + VARIANTS + r'\b', q)
        if suffix and not has_variant:
            return 'variant', query + ' ' + suffix[1].title()
        if has_variant and has_variant[0] == 'pro' and suffix and suffix[1] == 'max':
            return 'variant', query + ' Max'
        # Pro must not match Pro Max; use the complete tail after the query as well.
        if q.endswith(' pro') and re.match(r'\s*max\b', body[match.end():]):
            return 'variant', query + ' Max'
        return 'exact', query
    ignored = {'dai', 'hoc', 'truong', 'dh', 'university', 'the', 'of', 'va', 'and', 'cong', 'ty', 'thuong', 'hieu', 'tra', 'sua'}
    wanted = [t for t in tokens if t not in ignored] or tokens
    found = set(re.findall(r'[^\W_]+(?:\+\+|#)?', body))
    ratio = sum(t in found for t in wanted) / len(wanted)
    threshold = .6 if len(wanted) >= 4 else .8
    if ratio < threshold:
        return 'unrelated', ''
    return 'exact', query


def source_kind(query, source):
    host = (urlsplit(source['url']).hostname or '').lower()
    official = {'xiaomi': ('mi.com', 'xiaomi.com'), 'samsung': ('samsung.com',),
                'iphone': ('apple.com',), 'apple': ('apple.com',), 'vinfast': ('vinfastauto.com', 'vinfastauto.vn'),
                'asus': ('asus.com',), 'oppo': ('oppo.com',)}
    for term, domains in official.items():
        if term in key(query) and any(host == d or host.endswith('.'+d) for d in domains):
            return 'official'
    if host.endswith(('.edu.vn', '.gov.vn', '.edu', '.gov')):
        return 'institution'
    if host == 'news.google.com':
        return 'headline'
    if source.get('provider') in ('Wikipedia', 'Wikidata', 'OpenAlex Research'):
        return 'reference'
    return 'publication' if source.get('is_reputable') else 'web'


def prepare_sources(query, sources):
    relevant, unrelated = [], 0
    for source in sources:
        status, matched_name = assess_match(query, source['title'], source.get('excerpt', ''))
        if status == 'unrelated':
            if source.get('provider') == 'Wikidata':
                status, matched_name = 'alias', source.get('title') or query
            else:
                unrelated += 1
                continue
        item = dict(source)
        item.update(match_status=status, matched_name=matched_name, source_kind=source_kind(query, source))
        relevant.append(item)
    order = {'official': 0, 'institution': 1, 'publication': 2, 'reference': 3, 'web': 4, 'headline': 5}
    relevant.sort(key=lambda s: (s['match_status'] != 'exact', order[s['source_kind']], -(len(s.get('excerpt', '')))))
    for i, source in enumerate(relevant):
        source['source_id'] = f'S{i+1}'
    return relevant, unrelated
