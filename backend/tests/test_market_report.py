import csv
import json
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from main import app
from services import market_report as reports
from services.research_evidence import summarize
from ml_engine.regression import MarketRegression


def reference():
    return [{'period': str(year), 'value': float(100+(year-2000)*4+np.sin(year)),
             'observed_entity':'Việt Nam','source_url':'https://api.worldbank.org/v2/country/VNM/indicator/SE.TER.ENRR'}
            for year in range(2000,2025)]


@pytest.fixture
def official_data(monkeypatch):
    monkeypatch.setattr(reports,'fetch_reference', lambda code:(reference(),'https://api.worldbank.org/v2/country/VNM/indicator/'+code,'2026-11-10T00:00:00+00:00',False))


def test_each_keyword_has_own_dataset_and_full_strategy(official_data):
    first=reports.build_report('Đại học Thủ Dầu Một',[],summarize('Đại học Thủ Dầu Một',[]))
    second=reports.build_report('Đại học Bình Dương',[],summarize('Đại học Bình Dương',[]))
    assert first['dataset_id'] != second['dataset_id']
    assert first['status']=='completed_reference'
    assert first['provenance']['observed_entity']=='Việt Nam'
    assert first['provenance']['is_entity_data'] is False
    assert first['provenance']['indicator_code']=='SE.TER.ENRR'
    assert len(first['strategy']['action_plan'])==3
    assert len(first['strategy']['kpis'])>=4
    assert first['quantitative']['validation']['train_end'] < first['quantitative']['validation']['test_start']
    path=reports.storage()/f"{first['dataset_id']}.csv"
    rows=list(csv.DictReader(path.open(encoding='utf-8-sig',newline='')))
    assert len(rows)==25
    assert {r['research_query'] for r in rows}=={'Đại học Thủ Dầu Một'}
    assert {r['observed_entity'] for r in rows}=={'Việt Nam'}
    assert [float(r['value']) for r in rows]==[r['value'] for r in reference()]
    assert json.loads((reports.storage()/f"{first['dataset_id']}.json").read_text(encoding='utf-8'))['dataset_id']==first['dataset_id']


@pytest.mark.parametrize('query',['R','C++','人工智能','trà sữa Phê La','đại học mở','một từ khóa chưa tồn tại xyz123'])
def test_arbitrary_keyword_gets_result_with_explicit_reference_scope(official_data,query):
    result=reports.build_report(query,[],summarize(query,[]))
    assert result['query']==query
    assert result['quantitative']['status']=='completed'
    assert result['strategy']['conclusion']
    assert 'Chưa có' in result['entity_data_status']
    assert len(result['quantitative']['forecast'])==3
    assert result['quantitative']['clustering']['status']=='completed'


def test_failure_is_explained_and_never_fabricates_rows(monkeypatch):
    monkeypatch.setattr(reports,'fetch_reference',lambda code: (_ for _ in ()).throw(OSError('private diagnostic')))
    result=reports.build_report('Đại học Thủ Dầu Một',[],{})
    assert result['training_data']==[]
    assert result['quantitative'] is None
    assert result['status']=='insufficient_quantitative_data'
    assert len(result['strategy']['action_plan'])==3
    assert 'private diagnostic' not in str(result)


def test_actual_r2_can_be_negative():
    score=MarketRegression._safe_r2(np.arange(5),np.arange(5),np.array([0.,1.,2.,3.]),np.array([50.,60.,70.,80.]))
    assert score < 0


def test_constant_series_does_not_invent_classes():
    rows=reference()
    for row in rows: row['value']=100.
    result=reports.evaluate_series(rows)
    assert result['classification']['status']=='insufficient_classes'
    assert result['clustering']['status']=='insufficient_variation'
    assert result['validation']['mae']==0
    assert all(row['value']==100 for row in result['forecast'])


def test_missing_years_are_not_filled():
    rows=[row for i,row in enumerate(reference()) if i%2==0]
    with pytest.raises(ValueError,match='năm liên tiếp'):
        reports.evaluate_series(rows)


def test_report_and_training_csv_through_real_api(official_data,monkeypatch):
    from services import research_collectors as collectors
    monkeypatch.setattr(collectors,'collect',lambda name,query:([],{'name':name,'status':'no_results'}))
    with TestClient(app) as client:
        result=client.post('/api/research/search',json={'query':'Đại học Thủ Dầu Một'}).json()
        assert result['report']['status']=='completed_reference'
        response=client.get(result['report']['csv_url'])
        assert response.status_code==200
        assert 'attachment' in response.headers['content-disposition']
        assert 'observed_entity' in response.text
        assert client.get('/api/research/datasets/not-an-id/csv').status_code==404
        compared=client.post('/api/research/compare',json={'left':{'query':'Đại học Bình Dương'},'right':{'query':'Đại học Mở'}}).json()
        assert compared['left']['report']['dataset_id'] != compared['right']['report']['dataset_id']
        assert compared['left']['report']['quantitative'] and compared['right']['report']['quantitative']


def test_low_skill_forecast_does_not_recommend_expansion(official_data):
    strategy=reports.build_strategy('Trường X', {'category':'Education & EdTech','label':'Giáo dục','criteria':['Học phí'],'requirements':['Dữ liệu tuyển sinh']},[],{},
        {'recent_change_pct':10,'validation':{'beats_baseline':True,'r2':-2}})
    assert strategy['recommended_scenario']=='Thận trọng'
    assert 'chưa dùng dự báo' in strategy['conclusion']


def test_missing_sector_series_uses_explicit_macro_fallback(monkeypatch):
    def fetch(code):
        if code=='SE.TER.ENRR': raise OSError('not available')
        return reference(),'https://api.worldbank.org/v2/country/VNM/indicator/'+code,'2026-11-10T00:00:00+00:00',False
    monkeypatch.setattr(reports,'fetch_reference',fetch)
    result=reports.build_report('Đại học Thủ Dầu Một',[],{})
    assert result['status']=='completed_reference'
    assert result['provenance']['indicator_code']==reports.DEFAULT_INDICATOR[0]
    assert 'không coi đây là dữ liệu riêng của ngành' in result['provenance']['selection_note']


def test_research_csv_can_be_uploaded_and_analyzed_in_new_analysis(official_data, monkeypatch, tmp_path):
    from services import research_collectors as collectors, upload as upload_service, datasets as datasets_service
    monkeypatch.setattr(collectors, 'collect', lambda name, query: ([], {'name': name, 'status': 'no_results'}))
    monkeypatch.setattr(upload_service, 'UPLOADS_DIR', tmp_path)
    monkeypatch.setattr(datasets_service, 'UPLOADS_DIR', tmp_path)
    with TestClient(app) as client:
        res = client.post('/api/research/search', json={'query': 'Điện thoại nhập khẩu Trung Quốc'}).json()
        csv_url = res['entity_report']['csv_url']
        csv_bytes = client.get(csv_url).content
        up = client.post('/api/datasets/upload', files={'file': ('research.csv', csv_bytes, 'text/csv')}, data={'category': 'Smartphones & Mobile'})
        assert up.status_code == 200, up.text
        uploaded_filename = up.json()['filename']
        # Analyze with original keyword AND with short alias "ĐT"
        for kw in ('Điện thoại nhập khẩu Trung Quốc', 'ĐT'):
            analyzed = client.post('/api/analyze', json={
                'product_name': kw,
                'category': 'Smartphones & Mobile',
                'dataset_name': uploaded_filename,
            })
            assert analyzed.status_code == 200, analyzed.text
            payload = analyzed.json()
            assert 0 <= payload['potential_score'] <= 100
            assert payload['regression']['chart_data']
            assert payload['strategy_recommendation']['recommended_action']
            assert payload['evidence_scope']['analysis_mode'] == 'national_reference'
            assert payload['evidence_scope']['matched_item'] is False
            assert payload['evidence_scope']['observed_entities'] == ['Việt Nam']
            assert 'ai_models' not in payload['supporting_models_summary']
            assert payload['supporting_models_summary']['assistant_name'] == 'MarketWiseJu'
