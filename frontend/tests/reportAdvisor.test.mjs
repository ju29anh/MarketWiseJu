import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import ts from 'typescript';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

function moduleUrl(source, imports={}) {
  const code=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX}}).outputText
    .replace(/from\s+(['"])([^'"]+)\1/g,(match,_q,spec)=>imports[spec]?`from ${JSON.stringify(imports[spec])}`:match);
  return 'data:text/javascript;base64,'+Buffer.from(code).toString('base64');
}
const utils=moduleUrl(await readFile(new URL('../src/utils/advisor.ts',import.meta.url),'utf8'));
const view=moduleUrl(await readFile(new URL('../src/components/ReportAdvisor.tsx',import.meta.url),'utf8'),{
  react:import.meta.resolve('react'),'react/jsx-runtime':import.meta.resolve('react/jsx-runtime'),
  'lucide-react':import.meta.resolve('lucide-react'),'../utils/advisor':utils,
  '../api/http':moduleUrl('export const API_BASE="/api";export function safeFetch(){throw Error("SSR must not call API")}'),
});
const {ReportAdvisor,AdvisorAnswer}=await import(view);
const {advisorMarkdown}=await import(utils);
const reply={
  conversation_id:'a'.repeat(32),query:'Váy xòe dành cho GenZ',question:'Vốn 0 đồng, làm trong 14 ngày?',
  answer:'Đây là kế hoạch thử đặt trước, chưa phải kết luận nhu cầu thị trường.',
  assumptions:['Chưa có dữ liệu giá vốn.'],questions:['Bạn đã có mẫu hay chưa?'],
  steps:[{title:'Xin bảng size',when:'Ngày 1',action:'Liên hệ nhà cung cấp để xin bảng size của hai mẫu váy.',
    deliverable:'Bảng size và báo giá vốn',decision_rule:'Chưa có giá vốn thì chưa nhận tiền đặt hàng.'}],
  evidence:[],assistant_name:'MarketWiseJu',generated_at:'2026-11-11T12:00:00Z',source_count:0,
  context_created_at:'2026-11-11T11:00:00Z',notice:'Đề xuất cần kiểm nghiệm.',
};

test('chat is available after a saved report and keeps prompts specific',()=>{
  const html=renderToStaticMarkup(React.createElement(ReportAdvisor,{query:reply.query,researchId:'a'.repeat(32)}));
  assert.match(html,/Trao đổi &amp; lập kế hoạch với MarketWiseJu/);
  assert.match(html,/Váy xòe dành cho GenZ/);
  assert.match(html,/Gửi yêu cầu/);
  assert.match(html,/Lập kế hoạch 14 ngày/);
  assert.doesNotMatch(html,/role="alert"/);
});

test('old reports give actionable missing-context message',()=>{
  const html=renderToStaticMarkup(React.createElement(ReportAdvisor,{query:'Váy xòe'}));
  assert.match(html,/Hãy tra cứu lại/);
  assert.match(html,/disabled=""/);
});

test('answer labels assumptions and no-source limits without a confidence percentage',()=>{
  const html=renderToStaticMarkup(React.createElement(AdvisorAnswer,{reply}));
  for(const text of ['đề xuất cần kiểm nghiệm','Giả định đang dùng','Cần có sau bước này','Điều kiện tiếp tục / dừng','chưa có trích dẫn','chưa tra cứu web mới'])assert.ok(html.includes(text),text);
  assert.doesNotMatch(html,/\d+%/);
});

test('macro scope is visible and source evidence remains verbatim',()=>{
  const html=renderToStaticMarkup(React.createElement(AdvisorAnswer,{reply:{...reply,
    scope:{analysis_mode:'national_reference',scope_label:'GDP Việt Nam'},
    evidence:[{source_id:'S1',title:'Bảng size',url:'https://example.com/size',quote:'Mẫu váy có bảng size riêng.',content_status:'article'}],
  }}));
  assert.match(html,/GDP Việt Nam/);
  assert.match(html,/Không dùng kết quả này/);
  assert.match(html,/Mẫu váy có bảng size riêng/);
  assert.match(html,/chưa xác nhận tài liệu đúng/);
});

test('generated HTML is rendered as text and export preserves source status',()=>{
  const html=renderToStaticMarkup(React.createElement(AdvisorAnswer,{reply:{...reply,answer:'<script>alert(1)</script>'}}));
  assert.doesNotMatch(html,/<script>/);
  assert.match(html,/&lt;script&gt;/);
  const text=advisorMarkdown([reply]);
  assert.match(text,/Vốn 0 đồng/);
  assert.match(text,/giá vốn/);
  assert.match(text,/MarketWiseJu/);
  assert.doesNotMatch(text,/gemini|google|model_used/i);
  assert.doesNotMatch(html,/gemini|google|model_used/i);
  assert.match(text,/Đề xuất cần kiểm nghiệm/);
});
