import pandas as pd
import pytest
from services.analysis_context import describe_analysis_data
from ml_engine.regression import MarketRegression


def test_context_names_the_reference_indicator_without_changing_subject():
    frame = pd.DataFrame({'value':[3,4], 'indicator_code':['TX.VAL.TECH.CD']*2,
        'unit':['USD']*2, 'observed_entity':['Việt Nam']*2,
        'source_url':['https://api.worldbank.org/v2/country/VNM/indicator/TX.VAL.TECH.CD']*2})
    context = describe_analysis_data(frame,'value',{})
    assert 'xuất khẩu công nghệ cao' in context['indicator_label']
    assert context['unit'] == 'USD'
    assert context['observed_entities'] == ['Việt Nam']
    assert context['analyzed_rows'] == 2


def test_context_checks_all_units_and_excludes_unsafe_source_urls():
    frame = pd.DataFrame({'value':[1,2,3], 'unit':['USD','USD','VND'],
        'source_url':['javascript:alert(1)','https://127.0.0.1/private','https://example.org/data']})
    context = describe_analysis_data(frame,'value',{})
    assert context['unit_status'] == 'mixed'
    assert context['unit'] is None
    assert context['source_urls'] == ['https://example.org/data']


def test_generic_numeric_column_does_not_invent_a_currency():
    context = describe_analysis_data(pd.DataFrame({'value':[1,2]}),'value',{})
    assert context['unit_status'] == 'unknown'
    assert context['unit'] is None


@pytest.mark.parametrize('rows,mode,test_rows', [(5,'in_sample',0),(16,'heldout',4)])
def test_validation_describes_independent_test_and_previous_period_baseline(rows,mode,test_rows):
    frame = pd.DataFrame({'period':list(range(2000,2000+rows)), 'step':list(range(rows)), 'sales':list(range(1,rows+1))})
    result = MarketRegression.train_and_forecast(frame,'sales',['step'],date_col='period')
    validation = result['validation']
    assert validation['mode'] == mode
    assert validation['test_rows'] == test_rows
    if mode == 'heldout':
        assert validation['baseline_mae'] == 1
        assert validation['test_start'] == '2012'
        assert validation['test_end'] == '2015'
    else:
        assert validation['baseline_mae'] is None
        assert validation['test_start'] is None
