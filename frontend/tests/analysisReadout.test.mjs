import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import ts from 'typescript';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

const moduleUrl = (source, imports = {}) => {
  const code = ts.transpileModule(source, { compilerOptions: {
    module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX,
  } }).outputText.replace(/from\s+(['"])([^'"]+)\1/g, (match, _quote, specifier) =>
    imports[specifier] ? `from ${JSON.stringify(imports[specifier])}` : match);
  return 'data:text/javascript;base64,' + Buffer.from(code).toString('base64');
};
const readoutModule = moduleUrl(await readFile(new URL('../src/utils/analysisReadout.ts', import.meta.url), 'utf8'));
const { buildAnalysisReadout, formatMeasure, analysisSummaryMarkdown } = await import(readoutModule);
const viewModule = moduleUrl(await readFile(new URL('../src/views/AnalysisResultView.tsx', import.meta.url), 'utf8'), {
  'react': import.meta.resolve('react'), 'react/jsx-runtime': import.meta.resolve('react/jsx-runtime'),
  '../components/ReportAdvisor': moduleUrl('export function ReportAdvisor(){ return null; }'),
  'lucide-react': import.meta.resolve('lucide-react'), '../utils/analysisReadout': readoutModule,
  '../utils/locale': moduleUrl(await readFile(new URL('../src/utils/locale.ts', import.meta.url), 'utf8')),
  '../utils/csv': moduleUrl(await readFile(new URL('../src/utils/csv.ts', import.meta.url), 'utf8')),
});
const { AnalysisResultView } = await import(viewModule);

function fixture() {
  return {
    product_name: 'Redmi K100 Pro Max', category: 'Smartphones & Mobile', session_id: 'saved-report', dataset_name: 'upload_sample.csv',
    potential_score: 60, quality_score: 99, supporting_models_summary: { ai_model_active: 'Internal engine' },
    data_validation: { total_rows: 16, total_columns: 9, missing_pct: 0, duplicate_pct: 0, sample_data: [{
      indicator_code: 'TX.VAL.TECH.CD', unit: 'USD', observed_entity: 'Việt Nam', scope: 'national_reference',
      source_url: 'https://api.worldbank.org/v2/country/VNM/indicator/TX.VAL.TECH.CD',
    }] },
    evidence_scope: { analysis_mode: 'national_reference', matched_item: false, rows: 16 },
    regression: {
      target_variable: 'value', projected_growth_pct: 31.61, metrics: { mae: 17662940435.72, rmse: 18972029232.2, r2_score: -.9751 },
      chart_data: Array.from({length:16}, (_, i) => ({period:String(2008+i),actual:(i+1)*1e9,predicted:(i+1)*1e9})),
      future_forecast: Array.from({length:7}, (_, i) => ({period:`T+${i+1}`,forecast_value:17e9+i*1e9,lower_bound:15e9,upper_bound:25e9})),
    },
    classification: { current_market_classification: 'High' }, clustering: { current_item_cluster: { cluster_name: 'Cluster 1' } },
  };
}

test('the screenshot case explains the real indicator and weak validation', () => {
  const report = buildAnalysisReadout(fixture());
  assert.equal(report.scope, 'national');
  assert.match(report.metric, /xuất khẩu công nghệ cao/);
  assert.match(report.title, /Chưa thể kết luận riêng về Redmi/);
  assert.match(report.summary, /2008–2023/);
  assert.match(report.qualityReason, /17,66 tỷ USD/);
  assert.equal(report.quality, 'weak');
  assert.deepEqual(report.time.labels, ['2024','2025','2026','2027','2028','2029','2030']);
  assert.ok(report.guide.fields.includes('unit_price_vnd'));
});

test('rendered result removes product rankings and the unsupported growth headline', () => {
  const html = renderToStaticMarkup(React.createElement(AnalysisResultView, {
    data:fixture(),onBackToDashboard(){},onNewAnalysis(){},onUploadData(){},onResearch(){},
  }));
  assert.match(html, /Chưa thể kết luận riêng về Redmi K100 Pro Max/);
  assert.match(html, /Giá trị xuất khẩu công nghệ cao/);
  assert.match(html, /Bạn nên làm gì tiếp theo/);
  assert.doesNotMatch(html, /60\/100|31\.61%|31,61%|Internal engine|5 Trụ cột|Chiến lược Chuyên sâu/);
  assert.match(html, /aria-expanded="false"/);
  assert.match(html, /Bổ sung dữ liệu đúng đối tượng/);
});

test('mixed or missing units do not become currency assumptions', () => {
  const data = fixture();
  data.data_context = {indicator_label:'Chỉ tiêu thử',indicator_code:null,unit:null,unit_status:'mixed',observed_entities:['Việt Nam'],source_urls:[]};
  assert.equal(buildAnalysisReadout(data).unit, null);
  data.data_context = undefined;
  data.data_validation.sample_data = [];
  assert.equal(buildAnalysisReadout(data).unit, null);
  assert.match(buildAnalysisReadout(data).qualityReason, /chưa ghi rõ đơn vị/);
});

test('gaps do not turn T+1 into a promised calendar year', () => {
  const data = fixture();
  data.regression.chart_data[3].period = '2012';
  const report = buildAnalysisReadout(data);
  assert.equal(report.time.gaps, true);
  assert.equal(report.time.cadence, 'period');
  assert.equal(report.time.labels[0], 'Bước 1');
});

test('zero observations remain zero and do not create a percentage', () => {
  const data = fixture();
  data.regression.chart_data.at(-2).actual = 0;
  data.regression.chart_data.at(-1).actual = 0;
  const report = buildAnalysisReadout(data);
  assert.equal(report.recentChange, null);
  assert.match(report.facts[1].value, /^0 USD$/);
  assert.equal(formatMeasure(0), '0');
  assert.equal(formatMeasure(Number.NaN), 'Chưa xác định');
});

test('a strong in-sample score is not described as independent validation', () => {
  const data = fixture();
  data.regression.chart_data = data.regression.chart_data.slice(0,5);
  data.regression.metrics.r2_score = 1;
  const report = buildAnalysisReadout(data);
  assert.equal(report.quality, 'unvalidated');
  assert.match(report.qualityReason, /chưa tách được phần dữ liệu riêng/);
});

test('even positive R squared cannot override a worse baseline comparison', () => {
  const data = fixture();
  data.regression.metrics.r2_score = .8;
  data.regression.validation = {mode:'heldout',beats_baseline:false,baseline_mae:1};
  assert.equal(buildAnalysisReadout(data).quality, 'weak');
});

test('a matched item gets an item-specific summary and monthly rollover', () => {
  const data = fixture();
  data.product_name = 'ROG Strix G16';
  data.evidence_scope = {analysis_mode:'exact_item',matched_item:true};
  data.data_validation.sample_data = [];
  data.data_context = {indicator_label:'Số lượng bán',unit:'máy',unit_status:'known',observed_entities:['ROG Strix G16'],source_urls:[]};
  data.regression.metrics.r2_score = .8;
  data.regression.validation = {mode:'heldout',beats_baseline:true,baseline_mae:100};
  data.regression.chart_data = Array.from({length:12},(_,i)=>({period:`2024-${String(i+1).padStart(2,'0')}`,actual:100+i}));
  const report = buildAnalysisReadout(data);
  assert.equal(report.scope, 'entity');
  assert.equal(report.quality, 'supported');
  assert.equal(report.time.labels[0], '2025-01');
  assert.match(report.title, /Trong dữ liệu, chỉ tiêu kỳ gần nhất tăng/);
  assert.match(report.summary, /12 quan sát của ROG Strix G16/);
  assert.match(report.actions[0].title, /2024-12/);
});

test('education requests enrollment and tuition rather than phone sales columns', () => {
  const data = fixture();
  data.category = 'Education & EdTech';
  const report = buildAnalysisReadout(data);
  assert.ok(report.guide.fields.includes('enrollments'));
  assert.ok(report.guide.fields.includes('tuition_vnd'));
  assert.ok(!report.guide.fields.includes('units_sold'));
});

test('only matching subject documents are shown, separately from training data', () => {
  const data=fixture();
  data.web_research={sources:[
    {title:'Khác phiên bản',excerpt:'Giá của phiên bản khác',url:'https://example.org/variant',match_status:'variant'},
    {title:'Đúng tên',excerpt:'Thông tin theo nguồn cần đối chiếu',url:'https://example.org/exact',match_status:'exact'},
    {title:'Không có URL an toàn',excerpt:'Nội dung',url:'javascript:alert(1)',match_status:'exact'},
  ]};
  const report=buildAnalysisReadout(data);
  assert.deepEqual(report.subjectSources.map(s=>s.title),['Đúng tên']);
  assert.equal(report.observedName,'Việt Nam');
});

test('mixed units override a high score and a successful baseline comparison', () => {
  const data=fixture();
  data.regression.metrics.r2_score=.95;
  data.regression.validation={mode:'heldout',beats_baseline:true};
  data.data_context={unit_status:'mixed',unit:null,observed_entities:[],source_urls:[]};
  const report=buildAnalysisReadout(data);
  assert.equal(report.quality,'weak');
  assert.match(report.qualityReason,/nhiều đơn vị khác nhau/);
});

test('exports preserve the explanation, units, actual dates and next steps', () => {
  const data = fixture();
  const markdown = analysisSummaryMarkdown(data);
  assert.match(markdown, /xuất khẩu công nghệ cao/);
  assert.match(markdown, /17,66 tỷ USD/);
  assert.match(markdown, /2024:/);
  assert.match(markdown, /units_sold/);
  assert.doesNotMatch(markdown, /Internal engine/);
  data.supporting_models_summary.web_synthesis_meta = {is_web_grounded:true};
  const legacy = buildAnalysisReadout(data);
  assert.equal(legacy.facts.length, 0);
  assert.doesNotMatch(analysisSummaryMarkdown(data,legacy), /2024:/);
});
