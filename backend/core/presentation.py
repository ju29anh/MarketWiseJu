"""Public branding without changing private execution/audit metadata."""
ASSISTANT_NAME = 'MarketWiseJu'
_PRIVATE_AI_FIELDS = frozenset({
    'model_used', 'routing_model', 'ai_model_active', 'ai_model_used',
    'google_models_integrated', 'ai_models', 'ai_configured',
})


def public_payload(value):
    if isinstance(value, list):
        return [public_payload(item) for item in value]
    if isinstance(value, dict):
        result = {key: public_payload(item) for key, item in value.items() if key not in _PRIVATE_AI_FIELDS}
        if _PRIVATE_AI_FIELDS.intersection(value):
            result['assistant_name'] = ASSISTANT_NAME
        return result
    return value
