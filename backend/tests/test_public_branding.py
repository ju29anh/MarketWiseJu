from copy import deepcopy
from core.presentation import public_payload, ASSISTANT_NAME


def test_private_execution_metadata_is_removed_without_mutating_saved_data():
    private = {'query': 'Váy xòe', 'model_used': 'private-provider-model',
               'supporting_models_summary': {'ai_model_active': 'private-provider-model',
                  'google_models_integrated': ['private-model'], 'ai_configured': True,
                  'web_synthesis_meta': {'legacy': True}},
               'sources': [{'title': 'Tài liệu', 'quote': 'Nguồn nguyên văn', 'url': 'https://example.com'}],
               'steps': [{'action': 'Thử hai mẫu', 'ai_model_used': 'private-provider-model'}]}
    original = deepcopy(private)
    public = public_payload(private)
    assert private == original
    assert public['assistant_name'] == ASSISTANT_NAME
    assert 'model_used' not in public
    assert 'ai_model_active' not in public['supporting_models_summary']
    assert 'google_models_integrated' not in public['supporting_models_summary']
    assert public['supporting_models_summary']['web_synthesis_meta'] == {'legacy': True}
    assert public['sources'] == private['sources']
    assert public['steps'][0]['action'] == 'Thử hai mẫu'
    assert 'ai_model_used' not in public['steps'][0]
