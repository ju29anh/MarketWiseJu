import { ExternalLink } from 'lucide-react';

export type MarketReport = {
  dataset_id: string; query: string; status: string; entity_data_status: string; data_issue: string | null;
  provenance: { mode: string; scope_label: string; observed_entity: string; indicator_label: string; unit: string; source_name: string; source_url?: string; last_period?: string; retrieved_at?: string; cached?: boolean; selection_note?:string; geography_note?:string };
  training_data: {period:string;value:number;source_url:string;observed_entity:string}[];
  quantitative: null | {
    method:string; validation:{mae:number;baseline_mae:number;beats_baseline:boolean;r2:number|null;train_end:string;test_start:string;test_end:string;test_rows:number;note:string};
    forecast:{period:string;value:number;lower:number;upper:number}[];
    recent_change_pct:number|null;forecast_change_pct:number|null;
    classification:{status:string;accuracy:number|null;f1:number|null;next_direction:string|null};
    clustering:{status:string;silhouette:number|null;groups:{label:string;count:number;periods:string[]}[]};
  };
};
const number = (v:number|null|undefined) => v==null?'Chưa xác định':v.toLocaleString('vi-VN',{maximumFractionDigits:2});

export function TrendChart({report:r}:{report:MarketReport}) {
  const rows=r.training_data, future=r.quantitative?.forecast||[];
  if(!rows.length||!future.length)return null;
  const values=[...rows.map(p=>p.value),...future.flatMap(p=>[p.lower,p.upper])];
  const min=Math.min(...values),max=Math.max(...values),span=max-min||1;
  const start=Number(rows[0].period),end=Number(future[future.length-1].period);
  const x=(year:string)=>(Number(year)-start)/(end-start||1)*850+90;
  const y=(value:number)=>260-(value-min)/span*220;
  const path=(data:{period:string;value:number}[])=>data.map(p=>`${x(p.period)},${y(p.value)}`).join(' ');
  return <figure className="space-y-3"><svg viewBox="0 0 1000 320" className="w-full" role="img" aria-label={`Diễn biến ${r.provenance.indicator_label} và dự báo ba năm; phạm vi ${r.provenance.observed_entity}`}>
    {[0,1,2,3].map(t=><g key={t}><line x1="90" x2="940" y1={40+t*220/3} y2={40+t*220/3} stroke="var(--color-border)"/><text x="80" y={44+t*220/3} textAnchor="end" fill="var(--color-slate-400)" fontSize="12">{Intl.NumberFormat('vi-VN',{notation:'compact',maximumFractionDigits:1}).format(max-t*span/3)}</text></g>)}
    <polygon points={[...future.map(p=>`${x(p.period)},${y(p.lower)}`),...future.slice().reverse().map(p=>`${x(p.period)},${y(p.upper)}`)].join(' ')} fill="var(--color-blue-500)" opacity=".15"/>
    <polyline points={path(rows)} fill="none" stroke="var(--chart-actual)" strokeWidth="2.5"/>
    <polyline points={path([rows[rows.length-1],...future])} fill="none" stroke="var(--chart-predicted)" strokeWidth="3" strokeDasharray="7 5"/>
    {[rows[0].period,rows[Math.floor(rows.length/2)].period,rows[rows.length-1].period,future[future.length-1].period].map(period=><text key={period} x={x(period)} y="288" textAnchor="middle" fill="var(--color-slate-400)" fontSize="13">{period}</text>)}
  </svg><figcaption className="text-xs text-slate-400">Đường liền: số liệu nguồn · Đường đứt: dự báo · Vùng mờ: khoảng sai số thực nghiệm. Đơn vị: {r.provenance.unit}.</figcaption></figure>;
}

export function MarketReportPanel({report:r}:{report:MarketReport}) {
  const p=r.provenance,q=r.quantitative;
  return <article className="space-y-5" aria-label={`Dữ liệu tham khảo cho ${r.query}`}>
    <div className="rounded-xl border border-amber-500/30 p-4 text-sm text-amber-200 space-y-2"><p><strong>Phạm vi: </strong>{p.scope_label} · {p.observed_entity}</p><p>Chuỗi này mô tả {p.indicator_label.toLocaleLowerCase()}; chưa đo nhu cầu, giá bán hoặc doanh số riêng của {r.query}.</p></div>
    <dl className="grid sm:grid-cols-3 gap-4 text-sm"><div><dt className="text-slate-400">Chỉ tiêu</dt><dd className="text-white mt-1">{p.indicator_label}</dd></div><div><dt className="text-slate-400">Đơn vị</dt><dd className="text-white mt-1">{p.unit}</dd></div><div><dt className="text-slate-400">Số kỳ có dữ liệu</dt><dd className="text-white mt-1">{r.training_data.length}</dd></div></dl>
    {r.data_issue&&<p className="text-sm text-amber-200">{r.data_issue}</p>}
    <TrendChart report={r}/>
    {q&&<div className="rounded-xl border border-slate-700 p-4 text-sm space-y-2"><h4 className="font-semibold text-white">Dự báo có vượt cách đơn giản không?</h4><p className="text-slate-300">{q.validation.beats_baseline?'Sai số kiểm định thấp hơn cách giữ nguyên giá trị gần nhất.':'Chưa vượt cách giữ nguyên giá trị gần nhất; nên dùng dự báo để tham khảo.'}</p><p className="text-slate-400">Sai số tuyệt đối trung bình: {number(q.validation.mae)} {p.unit}. Cách đơn giản: {number(q.validation.baseline_mae)} {p.unit}.</p><p className="text-xs text-slate-400">{q.validation.note}</p></div>}
    {!!r.training_data.length&&<details className="rounded-xl border border-slate-700 p-4"><summary className="cursor-pointer text-sm text-slate-200">Xem các kỳ dữ liệu gốc</summary><div className="overflow-x-auto mt-3"><table className="w-full text-left text-sm"><thead><tr><th className="p-2">Kỳ</th><th className="p-2">Giá trị ({p.unit})</th></tr></thead><tbody>{r.training_data.map(row=><tr key={row.period} className="border-t border-slate-700"><td className="p-2 text-slate-300">{row.period}</td><td className="p-2 text-white">{number(row.value)}</td></tr>)}</tbody></table></div></details>}
    {p.source_url&&<a href={p.source_url} target="_blank" rel="noopener noreferrer" className="inline-flex gap-2 items-center text-sm text-blue-300 underline"><ExternalLink size={15}/>{p.source_name}</a>}
  </article>;
}

