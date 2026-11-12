import { useEffect, useRef, useState, type FormEvent } from 'react';
import { MessageCircle, Send, Square, RotateCcw, Download, ExternalLink } from 'lucide-react';
import { API_BASE, safeFetch } from '../api/http';
import { ASSISTANT_NAME, advisorMarkdown, type AdvisorReply } from '../utils/advisor';

const button = 'inline-flex items-center justify-center gap-2 rounded-xl border border-slate-600 px-3 py-2.5 text-sm text-slate-200 hover:bg-slate-800 disabled:opacity-50';


export function AdvisorAnswer({reply:t}: {reply:AdvisorReply}) {
  return <div className="space-y-4 text-sm leading-relaxed">
    <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-400"><span className="text-blue-300">{ASSISTANT_NAME}</span><span>{new Date(t.generated_at).toLocaleString('vi-VN')}</span><span>{t.source_count} tài liệu đúng tên trong ngữ cảnh</span></div>
    {t.context_created_at&&<p className="text-xs text-slate-400">Ngữ cảnh báo cáo lúc {new Date(t.context_created_at).toLocaleString('vi-VN')}; câu trả lời chưa tra cứu web mới.</p>}
    <div><p className="text-xs uppercase tracking-wide text-blue-300 mb-2">Nhận định & đề xuất cần kiểm nghiệm</p><p className="text-slate-100 whitespace-pre-wrap">{t.answer}</p></div>
    {!!t.assumptions.length&&<div className="rounded-xl border border-amber-500/30 p-4"><h4 className="font-semibold text-amber-200 mb-2">Giả định đang dùng</h4><ul className="list-disc pl-5 space-y-1 text-slate-300">{t.assumptions.map((a,i)=><li key={i}>{a}</li>)}</ul></div>}
    {!!t.steps.length&&<div className="space-y-3"><h4 className="font-semibold text-white">Các bước có thể thực hiện</h4><p className="text-xs text-slate-400">Mốc thời gian, khoản chi thử và ngưỡng tiếp tục / dừng là đề xuất để bạn điều chỉnh; chưa phải chuẩn ngành hoặc kết quả đã kiểm chứng.</p>{t.steps.map((s,i)=><div key={i} className="rounded-xl border border-slate-700 bg-slate-950/50 p-4 space-y-2"><p className="text-xs text-blue-300">{i+1}. {s.when}</p><h5 className="font-semibold text-white">{s.title}</h5><p className="text-slate-200">{s.action}</p><p className="text-slate-300"><strong className="text-slate-100">Cần có sau bước này: </strong>{s.deliverable}</p><p className="text-slate-300"><strong className="text-slate-100">Điều kiện tiếp tục / dừng: </strong>{s.decision_rule}</p></div>)}</div>}
    {t.evidence.length?<details className="rounded-xl border border-slate-700 p-4"><summary className="cursor-pointer text-slate-200">Dẫn chứng đã đối chiếu văn bản nguồn · {t.evidence.length}</summary><p className="mt-3 text-xs text-slate-400">Trích dẫn khớp tài liệu đã thu thập. Điều này chưa xác nhận tài liệu đúng hoặc còn cập nhật.</p><div className="mt-3 space-y-4">{t.evidence.map((e,i)=><div key={i} className="space-y-2"><a href={e.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-start gap-2 text-blue-300 underline">{e.source_id} · {e.title}<ExternalLink size={14} className="shrink-0 mt-1"/></a><blockquote className="border-l-2 border-slate-600 pl-3 text-slate-300">{e.quote}</blockquote><p className="text-xs text-slate-400">{e.published_at?`Ngày nguồn: ${e.published_at} · `:''}{e.content_status==='article'?'Nội dung trang đã đọc':'Trích đoạn kết quả tìm kiếm'}</p></div>)}</div></details>:<p className="text-xs text-amber-200">Câu trả lời này chưa có trích dẫn nguồn để đối chiếu. Hãy dùng các đề xuất làm phương án thử, chưa xem là kết luận thị trường.</p>}
    {!!t.questions.length&&<div><h4 className="font-semibold text-white mb-2">Thông tin giúp chỉnh kế hoạch sát hơn</h4><ul className="list-disc pl-5 space-y-1 text-slate-300">{t.questions.map((q,i)=><li key={i}>{q}</li>)}</ul></div>}
    {t.scope?.analysis_mode==='national_reference'&&<p className="text-xs text-amber-200">Dữ liệu ML đang đo: {t.scope.scope_label||'chỉ tiêu tham khảo quốc gia'}. Không dùng kết quả này để suy ra nhu cầu hay doanh số riêng của sản phẩm.</p>}
  </div>;
}

export function ReportAdvisor({query,analysisId,researchId}: {query:string;analysisId?:string;researchId?:string|null}) {
  const [draft,setDraft]=useState(''),[turns,setTurns]=useState<AdvisorReply[]>([]);
  const [busy,setBusy]=useState(false),[error,setError]=useState('');
  const controller=useRef<AbortController|null>(null);
  const textarea=useRef<HTMLTextAreaElement|null>(null),latest=useRef<HTMLDivElement|null>(null);
  useEffect(()=>()=>controller.current?.abort(),[]);
  const enabled=!!(analysisId||researchId);
  const suggestions=[`Giải thích kết quả về ${query} bằng ngôn ngữ dễ hiểu.`,
    'Lập kế hoạch thử nghiệm trong 14 ngày: làm gì trước, cần thu được gì và khi nào nên dừng?',
    'Kết luận nào có nguồn, điều gì mới là giả định? Tôi cần bổ sung dữ liệu gì?'];
  async function send(question=draft) {
    if(controller.current||!enabled||question.trim().length<2)return;
    const abort=new AbortController();controller.current=abort;setBusy(true);setError('');
    try {
      const response=await safeFetch(`${API_BASE}/research/chat`,{method:'POST',headers:{'Content-Type':'application/json'},signal:abort.signal,
        body:JSON.stringify({question:question.trim(),...(analysisId?{analysis_id:analysisId}:{research_id:researchId}),
          ...(turns.length?{conversation_id:turns[turns.length-1].conversation_id}:{})})});
      const reply:AdvisorReply=await response.json();
      if(abort.signal.aborted)return;
      setTurns(previous=>[...previous,reply]);setDraft('');
      requestAnimationFrame(()=>latest.current?.scrollIntoView({behavior:'smooth',block:'start'}));
    }catch(e){if(!abort.signal.aborted)setError(e instanceof Error?e.message:'Chưa nhận được câu trả lời. Hãy thử lại.');}
    finally{if(controller.current===abort){controller.current=null;setBusy(false);}}
  }
  function submit(event:FormEvent){event.preventDefault();void send();}
  function reset(){controller.current?.abort();controller.current=null;setBusy(false);setTurns([]);setDraft('');setError('');textarea.current?.focus();}
  function download(){const url=URL.createObjectURL(new Blob([advisorMarkdown(turns)],{type:'text/markdown;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='ke-hoach-trao-doi.md';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  return <section aria-label={`Trò chuyện về ${query}`} className="report-advisor rounded-2xl border border-blue-400/30 bg-slate-900/60 p-4 sm:p-6 space-y-5 min-w-0 break-words">
    <header className="flex flex-wrap items-start justify-between gap-4"><div className="space-y-2"><h3 className="text-xl font-semibold text-white flex items-center gap-2"><MessageCircle size={22}/>Trao đổi & lập kế hoạch với {ASSISTANT_NAME}</h3><p className="text-sm text-slate-300">Hỏi tiếp về <strong className="text-white">{query}</strong>. Nêu mục tiêu, vốn, địa bàn hoặc thời hạn để điều chỉnh từng bước.</p></div>{!!turns.length&&<div className="flex flex-wrap gap-2 no-print"><button type="button" onClick={download} className={button}><Download size={15}/>Tải cuộc trao đổi</button><button type="button" onClick={reset} disabled={busy} className={button}><RotateCcw size={15}/>Bắt đầu lại</button></div>}</header>
    {!turns.length&&<div className="space-y-3"><p className="text-sm text-slate-300">Bạn có thể yêu cầu giải thích báo cáo, lên kế hoạch hoặc sửa phương án theo điều kiện của mình.</p><div className="flex flex-wrap gap-2 no-print">{suggestions.map((s,i)=><button key={s} type="button" className={`${button} text-left`} disabled={!enabled||busy} onClick={()=>{setDraft(s);textarea.current?.focus();}}>{['Giải thích kết quả','Lập kế hoạch 14 ngày','Kiểm tra căn cứ'][i]}</button>)}</div><p className="text-xs text-slate-400">Ví dụ: “Tôi muốn thử bán sản phẩm này với vốn 5 triệu trong 14 ngày, ưu tiên kênh online. Hãy chia từng việc và cách đo kết quả.”</p></div>}
    <div className="space-y-6" role="log" aria-label="Lịch sử trao đổi">{turns.map((t,i)=><article ref={i===turns.length-1?latest:undefined} key={i} className="scroll-mt-24 space-y-4 border-t border-slate-700 pt-5"><div className="ml-auto max-w-3xl rounded-xl bg-blue-500/10 border border-blue-400/20 p-4"><p className="text-xs text-blue-300 mb-2">Bạn</p><p className="text-sm text-white whitespace-pre-wrap">{t.question}</p></div><AdvisorAnswer reply={t}/></article>)}</div>
    {!enabled&&<p role="alert" className="text-sm text-amber-200">Báo cáo này chưa có ngữ cảnh trò chuyện. Hãy tra cứu lại để dùng MarketWiseJu với dữ liệu nguồn.</p>}
    {error&&<p role="alert" className="text-sm text-rose-200 rounded-xl border border-rose-500/30 p-4">{error}</p>}
    {busy&&<p role="status" className="text-sm text-blue-300 animate-pulse">MarketWiseJu đang đọc báo cáo và soạn câu trả lời…</p>}
    <form onSubmit={submit} className="space-y-3 no-print"><label className="block space-y-2"><span className="text-sm font-medium text-white">Bạn muốn làm rõ hoặc điều chỉnh điều gì?</span><textarea ref={textarea} value={draft} onChange={e=>setDraft(e.target.value)} maxLength={1600} rows={3} disabled={!enabled||busy} placeholder="Nhập yêu cầu như khi trò chuyện với AI…" className="w-full min-w-0 resize-y rounded-xl border border-slate-600 bg-slate-950 p-3.5 text-sm text-white disabled:opacity-50"/></label><div className="flex flex-wrap items-center justify-between gap-3"><p className="text-xs text-slate-400">{draft.length}/1600 · Câu hỏi tiếp theo giữ ngữ cảnh cuộc trao đổi.</p>{busy?<button type="button" className={button} onClick={()=>{controller.current?.abort();controller.current=null;setBusy(false);}}><Square size={15}/>Dừng chờ</button>:<button type="submit" disabled={!enabled||draft.trim().length<2} className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-500 px-4 py-3 text-sm font-semibold text-white disabled:opacity-50"><Send size={16}/>Gửi yêu cầu</button>}</div></form>
    <details className="text-xs text-slate-400"><summary className="cursor-pointer">Căn cứ & giới hạn của câu trả lời</summary><p className="mt-3 leading-relaxed">MarketWiseJu nhận báo cáo và tài liệu đã thu thập từ máy chủ. Trích dẫn phải khớp văn bản nguồn; đề xuất và số liệu thử nghiệm chưa phải kết quả thực tế. Không chấm % chính xác. Thông tin thị trường mới cần được tra cứu lại. Lịch sử giữ trong bộ nhớ phiên hiện tại, tối đa 24 lượt; làm mới trang hoặc khởi động lại máy chủ sẽ cần bắt đầu lại.</p></details>
  </section>;
}
