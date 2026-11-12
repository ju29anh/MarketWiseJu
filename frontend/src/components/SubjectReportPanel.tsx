import { sourceKind, sectionInfo } from '../utils/reportExports';
import { ExternalLink, ArrowUpRight, CheckCircle2, AlertCircle } from 'lucide-react';

export type SubjectSource = {
  source_id: string; title: string; url: string; excerpt: string; provider: string;
  content?: string; content_status?: string; domain?: string; published_at?: string; publisher?: string;
  source_kind: string; match_status: string; matched_name?: string; verified: boolean;
};
export type SubjectClaim = {
  title: string; text: string; source_id: string; quote: string;
  kind: 'fact' | 'inference'; evidence_status: string; measure?: string;
};
export type SubjectReport = {
  version: number; dataset_id: string; query: string; category: string; category_label: string;
  status: string; created_at: string; csv_url: string;
  identity: {name: string; message: string; exact_sources: number; related_sources: number; official_sources: number};
  sections: Record<'overview'|'market'|'pricing'|'risks', SubjectClaim[]>;
  actions: SubjectClaim[]; missing: string[]; related_subjects: string[];
  processing: {mode: string};
  data_status: {training_ready: boolean; article_documents: number; excluded_documents: number; supported_claims: number; reason: string};
};


export function ClaimCard({claim, sources, compact=false}: {claim:SubjectClaim;sources:SubjectSource[];compact?:boolean}) {
  const source=sources.find(s=>s.source_id===claim.source_id);
  const uncertain=claim.evidence_status==='unconfirmed';
  return <article className="min-w-0 rounded-2xl border border-slate-700 bg-slate-950 p-5 space-y-3">
    <div className="flex flex-wrap gap-2 text-[11px]">
      <span className={`rounded-full px-2.5 py-1 ${uncertain?'bg-amber-500/10 text-amber-200':'bg-blue-500/10 text-blue-300'}`}>
        {uncertain?'Tin chưa xác nhận / dự kiến':claim.kind==='inference'?'Nhận định phân tích':'Thông tin nguồn công bố'}
      </span>
      {claim.kind==='inference'&&uncertain&&<span className="text-slate-400 py-1">Nhận định có điều kiện</span>}
    </div>
    <h4 className={`${compact?'text-base':'text-lg'} font-semibold text-white leading-snug`}>{claim.title}</h4>
    <p className="text-sm leading-relaxed text-slate-200 whitespace-pre-line">{claim.text}</p>
    {claim.measure&&<p className="text-xs leading-relaxed text-blue-300 border-t border-slate-800 pt-3"><strong>Theo dõi / bàn giao:</strong> {claim.measure}</p>}
    {source&&<details className="text-xs border-t border-slate-800 pt-3">
      <summary className="cursor-pointer text-blue-300">Cơ sở nhận định · {claim.source_id} · {source.publisher||source.domain||sourceKind[source.source_kind]||'Nguồn'}</summary>
      <blockquote className="mt-3 border-l-2 border-slate-600 pl-3 leading-relaxed text-slate-300">“{claim.quote}”</blockquote>
      <a href={source.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-start gap-1.5 mt-3 text-blue-300 underline"><ExternalLink size={13} className="shrink-0 mt-0.5"/>{source.title}</a>
      {source.published_at&&<p className="text-slate-400 mt-2">Ngày nguồn công bố: {source.published_at}</p>}
    </details>}
  </article>;
}

type ReportView = 'overview'|'market'|'pricing'|'risks'|'full';


export function SubjectReportPanel({report:r,sources,view,onResearch}:{report:SubjectReport;sources:SubjectSource[];view:ReportView;onResearch?:(query:string)=>void}) {
  function group(id:keyof typeof sectionInfo, limit?:number) {
    const claims=limit?r.sections[id].slice(0,limit):r.sections[id];
    return <section key={id} className="space-y-4">
      <h3 className="text-xl text-white">{sectionInfo[id].title}</h3>
      {claims.length?<div className="grid md:grid-cols-2 gap-4">{claims.map((c,i)=><ClaimCard key={`${c.source_id}-${i}`} claim={c} sources={sources}/>)}</div>:
        <p className="text-sm text-slate-400 border border-dashed border-slate-700 rounded-xl p-5">{sectionInfo[id].empty}</p>}
    </section>;
  }
  const showActions=view==='market'||view==='full'||view==='overview';
  return <div className="space-y-7">
    {(view==='overview'||view==='full')&&<>
      <div className={`rounded-2xl border p-5 flex items-start gap-3 ${r.status==='with_findings'?'border-blue-500/30 bg-blue-500/5':'border-amber-500/30 bg-amber-500/5'}`}>
        {r.status==='with_findings'?<CheckCircle2 size={20} className="text-blue-300 shrink-0 mt-0.5"/>:<AlertCircle size={20} className="text-amber-200 shrink-0 mt-0.5"/>}
        <div className="space-y-2"><p className="text-sm text-slate-200">{r.identity.message}</p><p className="text-xs text-slate-400">Thông tin được công bố và nhận định phân tích có nhãn riêng. Mở “Cơ sở nhận định” để xem câu nguồn gốc.</p></div>
      </div>
      {group('overview')}
      {!!r.related_subjects.length&&<div className="rounded-2xl border border-slate-700 p-5 space-y-3"><h3 className="text-base text-white">Phiên bản liên quan, được tách riêng</h3><p className="text-xs text-slate-400">Thông số hoặc giá của các tên dưới đây không được gán cho “{r.query}”. Chọn một tên để phân tích riêng.</p><div className="flex flex-wrap gap-2">{r.related_subjects.map(name=><button type="button" onClick={()=>onResearch?.(name)} key={name} className="inline-flex items-center gap-2 border border-slate-600 rounded-full px-3 py-2 text-sm text-blue-300 disabled:opacity-50" disabled={!onResearch}>{name}<ArrowUpRight size={14}/></button>)}</div></div>}
      {view==='overview'&&r.status==='with_findings'&&<div className="space-y-6">{(['market','pricing','risks'] as const).filter(id=>r.sections[id].length).map(id=>group(id,2))}</div>}
    </>}
    {(view==='market'||view==='full')&&group('market')}
    {(view==='pricing'||view==='full')&&group('pricing')}
    {(view==='risks'||view==='full')&&group('risks')}
    {showActions&&!!r.actions.length&&<section className="space-y-4"><div><p className="text-xs uppercase tracking-widest text-blue-300 mb-2">Từ thông tin đến quyết định</p><h3 className="text-xl text-white">Hành động đề xuất cho {r.query}</h3><p className="text-xs text-slate-400 mt-2">Đề xuất có điều kiện, dựa trên dẫn chứng bên dưới; chưa phải kết quả đã thực hiện.</p></div><div className="grid md:grid-cols-2 gap-4">{r.actions.map((c,i)=><ClaimCard key={i} claim={c} sources={sources}/>)}</div></section>}
    {(view==='overview'||view==='full')&&<section className="rounded-2xl bg-slate-950 border border-slate-700 p-5 space-y-3"><h3 className="text-base text-white">Những điều báo cáo chưa xác nhận</h3><ul className="list-disc pl-4 space-y-2 text-sm text-slate-300">{r.missing.map((m,i)=><li key={i}>{m}</li>)}</ul>{r.processing.mode==='extractive'&&<p className="text-xs text-slate-400">Đang hiển thị trích đoạn trực tiếp. Phần diễn giải chưa tạo được; bạn vẫn có thể đọc và tải dữ liệu có nguồn.</p>}</section>}
  </div>;
}

