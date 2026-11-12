"""Describe what the model actually measures, without inferring product facts."""
import re
from services.research import safe_url


def describe_analysis_data(frame, target, roles):
    from services.market_report import INDICATORS, DEFAULT_INDICATOR
    indicators = {code: label for code, label, _ in [*INDICATORS.values(), DEFAULT_INDICATOR]}

    def distinct(column):
        if column not in frame:
            return []
        return list(dict.fromkeys(str(v).strip() for v in frame[column].dropna() if str(v).strip()))

    codes, units = distinct('indicator_code'), distinct('unit')
    code = codes[0] if len(codes) == 1 else None
    name = indicators.get(code)
    labels = distinct('indicator_label')
    if not name and len(labels) == 1:
        name = labels[0][:160]
    unit = units[0] if len(units) == 1 else None
    if not units:
        if re.search(r'(?:^|_)usd$', target, re.I):
            unit = 'USD'
        elif re.search(r'(?:^|_)vnd$', target, re.I):
            unit = 'VND'
    sources = list(dict.fromkeys(url for raw in distinct('source_url') if (url := safe_url(raw))))[:3]
    return {
        'target_column': target,
        'indicator_label': name,
        'indicator_code': code,
        'unit': unit,
        'unit_status': 'mixed' if len(units) > 1 else 'known' if unit else 'unknown',
        'source_urls': sources,
        'observed_entities': distinct('observed_entity') or distinct(roles.get('item_col'))[:12],
        'analyzed_rows': len(frame),
    }
