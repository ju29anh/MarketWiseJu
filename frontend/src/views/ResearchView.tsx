import { useEffect, useEffectEvent, useRef, useState, type FormEvent } from 'react';
import { Search, ArrowLeftRight, ExternalLink, Download, Printer, Volume2, X } from 'lucide-react';
import { API_BASE, downloadDatasetCsv, safeFetch } from '../api/http';
import { apiClient } from '../api/client';
import { csvCell } from '../utils/csv';
import { SubjectReportPanel, type SubjectReport, type SubjectSource } from '../components/SubjectReportPanel';
import { ResearchReference } from '../components/ResearchReference';
import { ReportAdvisor } from '../components/ReportAdvisor';
import { MarketReportPanel, type MarketReport } from '../components/MarketReportPanel';
import { subjectMarkdown, sourceKind, referenceMarkdown } from '../utils/reportExports';

type Observation = {entity:string;metric:string;value:number;unit:string;period:string|null;raw_value:string;context:string;source_url:string;source_title:string;provider:string;verified:boolean;review_status:string};
type Profile = {query:string;checked_at:string;advisor_context_id?:string|null;entity_report:SubjectReport;report?:MarketReport|null;sources:SubjectSource[];market_analysis:{observations:Observation[]}};
type Comparison = {left:Profile;right:Profile;conclusion:string;comparison_matrix:{metric:string;left_sources:SubjectSource[];right_sources:SubjectSource[]}[]};
type Tab = 'advisor'|'overview'|'market'|'pricing'|'risks'|'sources'|'data';
const tabs:{id:Tab;label:string}[]=[{id:'advisor',label:'Trao đổi & lập kế hoạch'},{id:'overview',label:'Tổng quan đối tượng'},{id:'market',label:'Thị trường & căn cứ'},{id:'pricing',label:'Giá & chi phí'},{id:'risks',label:'Rủi ro'},{id:'sources',label:'Tài liệu nguồn'},{id:'data',label:'Dữ liệu & dự báo'}];
const field='w-full min-w-0 rounded-xl border border-slate-600 bg-slate-950 p-3.5 text-sm text-white';
const secondary='inline-flex items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-slate-200 hover:bg-slate-800 disabled:opacity-50';
const columns=['entity','metric','value','unit','period','raw_value','context','source_url','source_title','provider','verified','review_status'] as const;
function download(name:string,content:string,type:string){const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function csv(headers:string[],rows:unknown[][]){return '\uFEFF'+[headers.map(csvCell).join(','),...rows.map(r=>r.map(csvCell).join(','))].join('\r\n');}

export function ResearchView({initialQuery='',onStartAnalysis}:{initialQuery?:string;onStartAnalysis?:(category?:string,datasetFilename?:string,productName?:string)=>void;onViewAnalysis?:(id:string)=>void}) {
  const [mode,setMode]=useState<'search'|'compare'>('search');
  const [left,setLeft]=useState(initialQuery),[right,setRight]=useState('');
  const [profiles,setProfiles]=useState<Profile[]>([]),[comparison,setComparison]=useState<Comparison|null>(null);
  const [busy,setBusy]=useState(false),[error,setError]=useState('');
  const [promotingId,setPromotingId]=useState<string|null>(null);
  const [tab,setTab]=useState<Tab>('advisor'),[filter,setFilter]=useState(''),[includeRelated,setIncludeRelated]=useState(false);
  const controller=useRef<AbortController|null>(null),audio=useRef<HTMLAudioElement|null>(null);
  const promotionController=useRef<AbortController|null>(null),speechController=useRef<AbortController|null>(null);
  const [speaking,setSpeaking]=useState(false),[audioBusy,setAudioBusy]=useState(false);
  useEffect(()=>()=>{controller.current?.abort();promotionController.current?.abort();speechController.current?.abort();audio.current?.pause();window.speechSynthesis?.cancel();},[]);
  async function search(query:string,other?:string) {
    controller.current?.abort();const abort=new AbortController();controller.current=abort;
    promotionController.current?.abort();speechController.current?.abort();setPromotingId(null);setAudioBusy(false);
    setBusy(true);setError('');setProfiles([]);setComparison(null);setTab('advisor');setFilter('');setIncludeRelated(false);
    audio.current?.pause();window.speechSynthesis?.cancel();setSpeaking(false);
    try {
      const response=await safeFetch(`${API_BASE}/research/${other?'compare':'search'}`,{method:'POST',headers:{'Content-Type':'application/json'},signal:abort.signal,body:JSON.stringify(other?{left:{query:query.trim()},right:{query:other.trim()}}:{query:query.trim()})});
      const result=await response.json();if(abort.signal.aborted)return;
      const list:Profile[]=other?[result.left,result.right]:[result];
      if(list.some(p=>!p.entity_report))throw new Error('Máy chủ đang dùng phiên bản cũ. Hãy tải lại trang hoặc thử lại sau.');
      if(other)setComparison(result);setProfiles(list);
    } catch(e){if(!abort.signal.aborted)setError(e instanceof Error?e.message:'Chưa thể tra cứu. Hãy thử lại.');}
    finally{if(!abort.signal.aborted)setBusy(false);}
  }
  const searchInitial = useEffectEvent((query:string) => { void search(query); });
  useEffect(()=>{
    let cancelled=false;
    // Defer external loading so StrictMode cleanup can discard its first mount.
    if(initialQuery.trim())void Promise.resolve().then(()=>{if(!cancelled)searchInitial(initialQuery);});
    return ()=>{cancelled=true;controller.current?.abort();};
  },[initialQuery]);
  function submit(event:FormEvent){event.preventDefault();if(!busy)void search(left,mode==='compare'?right:undefined);}
  function selectRelated(query:string){setMode('search');setLeft(query);void search(query);}
  async function startMLWithResearchDataset(p:Profile) {
    if (!onStartAnalysis) return;
    const datasetId = p.report?.dataset_id || p.entity_report.dataset_id;
    const category = p.entity_report.category === 'General Research' ? undefined : p.entity_report.category;
    promotionController.current?.abort();
    const abort = new AbortController();promotionController.current=abort;
    setPromotingId(datasetId);
    setError('');
    try {
      const res = await safeFetch(`${API_BASE}/research/datasets/${datasetId}/csv`,{signal:abort.signal});
      if(!res.headers.get('content-type')?.includes('text/csv'))throw new Error('Chưa có CSV hợp lệ để phân tích.');
      const blob = await res.blob();
      const file = new File([blob], `du-lieu-phan-tich-${datasetId.slice(0, 8)}.csv`, { type: 'text/csv' });
      const uploaded = await apiClient.uploadDataset(file, category || 'General Market',undefined,abort.signal);
      if(abort.signal.aborted)return;
      onStartAnalysis(category, uploaded.filename, p.query);
    } catch(e) {
      if(!abort.signal.aborted)setError(e instanceof Error?e.message:'Chưa chuyển được dữ liệu. Hãy thử lại hoặc tải lên CSV riêng.');
    } finally {
      if(!abort.signal.aborted)setPromotingId(null);
    }
  }
  const observations=profiles.flatMap(p=>p.market_analysis.observations);
  const allSources=profiles.flatMap(p=>p.sources.map(s=>({...s,entity:p.query})));
  async function downloadCsv(datasetId:string,event:{preventDefault:()=>void}) {
    setError('');
    try { await downloadDatasetCsv(datasetId,event); }
    catch(e) { setError(e instanceof Error?e.message:'Chưa tải được CSV. Hãy thử lại.'); }
  }
  function exportReport(){download('bao-cao-nghien-cuu.md',['# Báo cáo nghiên cứu đối tượng',...profiles.flatMap(p=>[`Tra cứu lúc: ${p.checked_at}`,...subjectMarkdown(p.entity_report,p.sources),...(p.report?referenceMarkdown(p.report):[]),'## Tài liệu nguồn',...p.sources.map(s=>`- ${s.source_id}: [${s.title}](${s.url}) — ${s.match_status==='exact'?'Đúng tên':'Phiên bản liên quan'}. ${s.excerpt}`)]),...(comparison?['## So sánh',comparison.conclusion]:[])].join('\n\n'),'text/markdown;charset=utf-8');}
  async function listen(){
    if(speaking){audio.current?.pause();window.speechSynthesis?.cancel();setSpeaking(false);return;}
    setAudioBusy(true);setError('');
    speechController.current?.abort();const abort=new AbortController();speechController.current=abort;
    try{const text=profiles.map(p=>`${p.query}. ${p.entity_report.sections.overview.map(c=>c.text).join(' ')}`).join(' ').slice(0,2400);const response=await apiClient.synthesizeTTS(text,'Kore',abort.signal);if(abort.signal.aborted)return;
      if(response.audio_base64){const player=new Audio(`data:${response.mime_type};base64,${response.audio_base64}`);audio.current=player;player.onended=()=>setSpeaking(false);await player.play();setSpeaking(true);}
      else if('speechSynthesis' in window){const speech=new SpeechSynthesisUtterance(text);speech.lang='vi-VN';speech.onend=()=>setSpeaking(false);speech.onerror=()=>setSpeaking(false);window.speechSynthesis.speak(speech);setSpeaking(true);}else setError('Trình duyệt chưa hỗ trợ đọc báo cáo.');
    }catch{if(!abort.signal.aborted)setError('Chưa thể đọc báo cáo. Bạn vẫn có thể tải bản văn bản.');}finally{if(!abort.signal.aborted)setAudioBusy(false);}
  }
  function sourceCards(p:Profile){
    const list=p.sources.filter(s=>(includeRelated||s.match_status==='exact')&&`${s.title} ${s.excerpt} ${s.publisher||s.domain}`.toLocaleLowerCase().includes(filter.toLocaleLowerCase()));
    return <div className="space-y-4">{list.map(s=><article key={s.url} className="rounded-2xl border border-slate-700 bg-slate-950 p-5 space-y-3 min-w-0"><div className="flex flex-wrap gap-2 text-[11px] text-slate-400"><span className="text-blue-300">{s.source_id}</span><span>{sourceKind[s.source_kind]||'Tài liệu tham khảo'}</span><span>{s.publisher||s.domain}</span>{s.match_status==='variant'&&<span className="text-amber-200">Phiên bản liên quan · {s.matched_name}</span>}</div><a href={s.url} target="_blank" rel="noopener noreferrer" className="flex items-start gap-2 text-base text-white hover:text-blue-300">{s.title}<ExternalLink size={16} className="shrink-0 mt-1"/></a><p className="text-sm leading-relaxed text-slate-300">{s.excerpt||'Mở tài liệu để đọc nội dung.'}</p><p className="text-xs text-slate-400">{s.content_status==='article'?'Đã đọc thêm nội dung trang':'Thông tin từ kết quả tìm kiếm'}{s.published_at?` · ${s.published_at}`:''}</p></article>)}{!list.length&&<p className="text-sm text-slate-400">Chưa có tài liệu khớp bộ lọc. Có thể bật xem phiên bản liên quan hoặc bổ sung tên đầy đủ.</p>}</div>;
  }
  return <div className="research-workspace space-y-6 py-4">
    <header className="space-y-3 no-print"><p className="text-xs uppercase tracking-widest text-blue-300">Tìm hiểu đúng đối tượng · quyết định từ dẫn chứng</p><h1 className="text-3xl sm:text-4xl text-white">Bạn muốn phân tích điều gì?</h1><p className="max-w-3xl text-sm text-slate-300">Nhập tên sản phẩm, trường học, thương hiệu hoặc chủ đề. Đọc thông tin cụ thể, diễn biến thị trường, giá và rủi ro từ tài liệu liên quan đến đúng tên đã nhập.</p></header>
    <form onSubmit={submit} className="glass-panel rounded-2xl p-5 sm:p-6 space-y-5 no-print">
      <div className="flex flex-wrap gap-2" aria-label="Chế độ tra cứu">{([['search','Phân tích một đối tượng'],['compare','So sánh trực tiếp hai đối tượng']] as const).map(([id,label])=><button key={id} type="button" aria-pressed={mode===id} disabled={busy} onClick={()=>{setMode(id);setProfiles([]);setComparison(null);setError('');}} className={`${secondary} ${mode===id?'border-blue-400 text-blue-300':''}`}>{id==='search'?<Search size={16}/>:<ArrowLeftRight size={16}/>} {label}</button>)}</div>
      <div className={`grid gap-4 ${mode==='compare'?'md:grid-cols-2':''}`}><label className="min-w-0 space-y-2"><span className="block text-sm text-slate-200">{mode==='compare'?'Đối tượng 1':'Tên đối tượng cần phân tích'}</span><input required maxLength={200} value={left} onChange={e=>setLeft(e.target.value)} className={field} placeholder="Ví dụ: Xiaomi 18, Đại học Thủ Dầu Một…"/></label>{mode==='compare'&&<label className="min-w-0 space-y-2"><span className="block text-sm text-slate-200">Đối tượng 2</span><input required maxLength={200} value={right} onChange={e=>setRight(e.target.value)} className={field} placeholder="Nhập đối tượng thứ hai…"/></label>}</div>
      <div className="flex flex-wrap items-center gap-3"><button disabled={busy||!left.trim()||(mode==='compare'&&!right.trim())} className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-500 px-5 py-3.5 text-sm font-semibold text-white disabled:opacity-50" type="submit"><Search size={17}/>{busy?'Đang đọc và phân tích nguồn…':mode==='compare'?'Tìm nguồn & so sánh ngay':'Tra cứu & phân tích'}</button>{busy&&<button type="button" className={secondary} onClick={()=>{controller.current?.abort();setBusy(false);}}><X size={16}/>Dừng tra cứu</button>}<p className="text-xs text-slate-400">Tách đúng tên, phiên bản và thông tin chưa xác nhận.</p></div>
    </form>
    {error&&<p role="alert" className="rounded-2xl border border-rose-700 p-5 text-sm text-rose-200">{error}</p>}
    {busy&&<div role="status" className="glass-panel rounded-2xl p-6 space-y-3"><div className="h-1 rounded-full bg-slate-800 overflow-hidden"><div className="h-full w-1/3 bg-blue-400 animate-pulse"/></div><p className="text-sm text-slate-200">Đang tìm đúng tên, loại kết quả không liên quan và đọc tài liệu để phân tích.</p><p className="text-xs text-slate-400">Báo cáo sẽ nêu thông tin về đối tượng, dẫn chứng, giá và hành động có cơ sở.</p></div>}
    {!!profiles.length&&<section aria-label="Kết quả nghiên cứu" className="research-results space-y-6">
      {comparison&&<section className="glass-panel rounded-2xl p-5 space-y-4"><h2 className="text-2xl text-white">So sánh {comparison.left.query} và {comparison.right.query}</h2><p className="text-sm text-slate-300">{comparison.conclusion}</p><div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Bảng so sánh hai đối tượng"><table className="comparison-table w-full text-sm text-left"><thead><tr><th className="p-3">Tiêu chí</th><th className="p-3">{comparison.left.query}</th><th className="p-3">{comparison.right.query}</th></tr></thead><tbody>{comparison.comparison_matrix.map(row=><tr key={row.metric} className="border-t border-slate-700 align-top"><th className="p-3 font-medium text-slate-200">{row.metric}</th>{[row.left_sources,row.right_sources].map((list,i)=><td className="p-3" key={i}>{list.length?list.slice(0,2).map(s=><div key={s.url} className="mb-4"><p className="text-slate-300">{s.excerpt||s.title}</p><a href={s.url} target="_blank" rel="noopener noreferrer" className="block mt-2 text-xs text-blue-300 underline">{s.title}</a></div>):<span className="text-slate-400">Chưa có tài liệu phù hợp</span>}</td>)}</tr>)}</tbody></table></div><p className="text-xs text-slate-400">Giá và chỉ tiêu chỉ đối chiếu được khi cùng phiên bản, đơn vị, địa bàn và thời kỳ. Không xếp hạng từ số bài viết.</p></section>}
      <div className="flex flex-wrap gap-2 no-print" aria-label="Nội dung báo cáo">{tabs.map(({id,label})=><button type="button" key={id} aria-pressed={tab===id} onClick={()=>setTab(id)} className={`${secondary} ${tab===id?'border-blue-400 text-blue-300':''}`}>{label}</button>)}</div>
      {profiles.map(p=>{
        const csvDatasetId = p.report?.dataset_id || p.entity_report.dataset_id;
        return <article key={p.entity_report.dataset_id} className="subject-report glass-panel rounded-2xl p-5 sm:p-7 space-y-6">
        <header className="space-y-4 border-b border-slate-700 pb-5">
          <div className="flex flex-wrap justify-between items-start gap-3">
            <div>
              <p className="text-xs uppercase tracking-widest text-blue-300">Hồ sơ đối tượng · {p.entity_report.category_label}</p>
              <h2 className="text-3xl text-white mt-2">{p.query}</h2>
            </div>
            <p className="text-xs text-slate-400">Cập nhật {new Date(p.checked_at).toLocaleString('vi-VN')}</p>
          </div>
          <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-slate-400">
            <span><strong className="text-white">{p.entity_report.identity.exact_sources}</strong> tài liệu đúng tên</span>
            <span><strong className="text-white">{p.entity_report.data_status.article_documents}</strong> trang đã đọc thêm</span>
            <span><strong className="text-white">{p.entity_report.data_status.supported_claims}</strong> nhận định có dẫn chứng</span>
            {!!p.entity_report.identity.related_sources&&<span>{p.entity_report.identity.related_sources} tài liệu phiên bản liên quan được tách riêng</span>}
          </div>
          <div className="flex flex-wrap gap-3 pt-1 no-print">
            <a className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 px-4 py-2.5 text-xs font-bold text-slate-950 transition-colors" href={`${API_BASE}/research/datasets/${csvDatasetId}/csv`} onClick={e => void downloadCsv(csvDatasetId, e)}>
              <Download size={15}/>Tải dữ liệu phân tích (CSV)
            </a>
            {onStartAnalysis && (
              <button
                type="button"
                disabled={promotingId !== null || !p.report?.training_data.length}
                onClick={() => void startMLWithResearchDataset(p)}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 hover:bg-blue-500 px-4 py-2.5 text-xs font-bold text-white transition-colors disabled:opacity-50"
              >
                {promotingId === csvDatasetId ? 'Đang chuẩn bị dữ liệu…' : 'Phân tích & dự báo từ dữ liệu này'}
              </button>
            )}
            {onStartAnalysis && (
              <button
                type="button"
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-900 hover:bg-slate-800 px-4 py-2.5 text-xs text-slate-200"
                onClick={() => onStartAnalysis(p.entity_report.category === 'General Research' ? undefined : p.entity_report.category, undefined, p.query)}
              >
                Tải lên CSV / XLSX riêng để dự báo
              </button>
            )}
          </div>
        </header>
        <div hidden={tab!=='advisor'} className="no-print"><ReportAdvisor query={p.query} researchId={p.advisor_context_id}/></div>
        <div className="no-print">{tab!=='advisor'&&tab!=='sources'&&tab!=='data'&&<SubjectReportPanel report={p.entity_report} sources={p.sources} view={tab} onResearch={selectRelated}/>}</div><div className="print-only"><SubjectReportPanel report={p.entity_report} sources={p.sources} view="full"/></div>
        <div className={tab==='sources'?'space-y-5':'print-only space-y-5'}><div className="no-print flex flex-col sm:flex-row gap-3"><input className={field} aria-label="Lọc tài liệu nguồn" placeholder="Lọc tiêu đề, nội dung, nhà xuất bản…" value={filter} onChange={e=>setFilter(e.target.value)}/><label className="flex items-center gap-2 text-xs text-slate-300 sm:shrink-0"><input type="checkbox" checked={includeRelated} onChange={e=>setIncludeRelated(e.target.checked)}/>Hiện phiên bản liên quan</label></div>{sourceCards(p)}</div>
        <div className={tab==='data'?'space-y-6':'print-only space-y-6'}><section className="rounded-2xl bg-slate-950 p-5 space-y-4"><h3 className="text-xl text-white">Dữ liệu thu được cho {p.query}</h3><p className="text-sm text-slate-300">{p.entity_report.data_status.reason}</p><p className="text-xs text-slate-400">Bộ CSV gồm {p.report?.training_data.length || 0} quan sát định lượng. Chỉ tiêu tham khảo quốc gia giữ nguyên phạm vi quốc gia khi phân tích; nếu chưa có quan sát, cần bổ sung CSV / XLSX riêng.</p><div className="flex flex-wrap gap-3 no-print"><a className={secondary} href={`${API_BASE}/research/datasets/${csvDatasetId}/csv`} onClick={e => void downloadCsv(csvDatasetId, e)}><Download size={16}/>Tải dữ liệu và phạm vi nguồn (CSV)</a>{onStartAnalysis&&<button type="button" className={secondary} onClick={()=>onStartAnalysis(p.entity_report.category==='General Research'?undefined:p.entity_report.category,undefined,p.query)}>Bổ sung CSV / XLSX để dự báo</button>}</div></section>
          {!!p.market_analysis.observations.length&&<section className="space-y-3"><h3 className="text-lg text-white">Số liệu nguyên văn cần đối chiếu</h3><div className="grid sm:grid-cols-2 gap-3">{p.market_analysis.observations.map((r,i)=><div key={i} className="rounded-xl border border-slate-700 p-4 space-y-2"><p className="text-xs text-slate-400">{r.metric} · {r.period||'Chưa rõ kỳ đo'}</p><p className="text-2xl text-blue-300">{r.raw_value}</p><p className="text-xs text-slate-300">{r.context}</p><a href={r.source_url} target="_blank" rel="noopener noreferrer" className="block text-xs text-blue-300 underline">{r.source_title}</a></div>)}</div></section>}<div className="no-print"><ResearchReference query={p.query} initialReport={p.report}/></div><div className="print-only">{p.report&&<MarketReportPanel report={p.report}/>}</div>
        </div>
      </article>;})}
      <div className="glass-panel rounded-2xl p-5 space-y-3 no-print"><h3 className="text-lg text-white">Lưu báo cáo & dữ liệu</h3><div className="flex flex-wrap gap-3"><button type="button" className={secondary} onClick={()=>window.print()}><Printer size={16}/>In / Lưu PDF</button><button type="button" className={secondary} onClick={exportReport}><Download size={16}/>Tải báo cáo</button>{profiles[0]&&<a className={secondary} href={`${API_BASE}/research/datasets/${profiles[0].report?.dataset_id||profiles[0].entity_report.dataset_id}/csv`} onClick={e => void downloadCsv(profiles[0].report?.dataset_id||profiles[0].entity_report.dataset_id, e)}><Download size={16}/>Tải CSV dữ liệu phân tích</a>}<button type="button" className={secondary} disabled={!observations.length} onClick={()=>download('so-lieu-co-nguon.csv',csv([...columns],observations.map(r=>columns.map(c=>r[c]??''))),'text/csv;charset=utf-8')}>CSV số liệu trích nguồn</button><button type="button" className={secondary} onClick={()=>download('tai-lieu-nguon.csv',csv(['entity','title','url','provider','published_at','excerpt','match_status','review_status'],allSources.map(s=>[s.entity,s.title,s.url,s.provider,s.published_at||'',s.excerpt,s.match_status,'needs_review'])),'text/csv;charset=utf-8')}>CSV tài liệu nguồn</button><button type="button" className={secondary} onClick={()=>download('ket-qua-co-nguon.json',JSON.stringify(comparison||profiles[0],null,2),'application/json')}>Dữ liệu JSON</button><button type="button" className={secondary} disabled={audioBusy} onClick={()=>void listen()}><Volume2 size={16}/>{audioBusy?'Đang chuẩn bị…':speaking?'Dừng đọc':'Nghe tóm tắt'}</button></div><p className="text-xs text-slate-400">Báo cáo giữ các mục và dẫn chứng, kể cả mục chưa mở. Tệp &ldquo;Tải CSV dữ liệu phân tích&rdquo; có thể nạp trực tiếp vào mục Phân tích mới.</p></div>
    </section>}
  </div>;
}
