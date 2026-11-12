import { useState } from 'react';
import { ArrowLeft, Download, Printer, ExternalLink, ChevronDown, Info, CheckCircle2, Database, ArrowUpRight, Search } from 'lucide-react';
import { csvCell } from '../utils/csv';
import type { AnalysisPayload, ForecastPoint } from '../types';
import { buildAnalysisReadout, formatMeasure, analysisSummaryMarkdown } from '../utils/analysisReadout';
import { viLabel } from '../utils/locale';
import { ReportAdvisor } from '../components/ReportAdvisor';

function save(name: string, text: string, mime: string) {
  const url = URL.createObjectURL(new Blob([text], { type: mime }));
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

const action = 'inline-flex items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-slate-200';

const fmtNum = (val: number | null | undefined, digits = 2) =>
  val == null || !Number.isFinite(val)
    ? '—'
    : val.toLocaleString('vi-VN', { maximumFractionDigits: digits });

function ForecastSvgChart({ points, targetVariable, unit }: { points: ForecastPoint[]; targetVariable: string; unit: string | null }) {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  if (!points || points.length === 0) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-8 text-center text-sm text-slate-400">
        Chưa có dữ liệu chuỗi thời gian để hiển thị biểu đồ.
      </div>
    );
  }

  const numericValues: number[] = [];
  for (const p of points) {
    if (p.actual != null && Number.isFinite(p.actual)) numericValues.push(p.actual);
    if (p.predicted != null && Number.isFinite(p.predicted)) numericValues.push(p.predicted);
    if (p.lower_bound != null && Number.isFinite(p.lower_bound)) numericValues.push(p.lower_bound);
    if (p.upper_bound != null && Number.isFinite(p.upper_bound)) numericValues.push(p.upper_bound);
  }

  const rawMin = numericValues.length ? numericValues.reduce((a,b) => Math.min(a,b), Infinity) : 0;
  const rawMax = numericValues.length ? numericValues.reduce((a,b) => Math.max(a,b), -Infinity) : 100;
  const rawSpan = rawMax - rawMin || Math.abs(rawMax) * 0.15 || 10;
  const pad = rawSpan * 0.1;
  const minVal = rawMin >= 0 ? Math.max(0, rawMin - pad) : rawMin - pad;
  const maxVal = rawMax + pad;
  const span = maxVal - minVal || 1;

  const leftX = 86;
  const rightX = 964;
  const topY = 28;
  const bottomY = 276;
  const width = rightX - leftX;
  const height = bottomY - topY;

  const getX = (idx: number) =>
    points.length <= 1 ? leftX + width / 2 : leftX + (idx / (points.length - 1)) * width;
  const getY = (val: number) => bottomY - ((val - minVal) / span) * height;

  const actualPoints = points
    .map((p, idx) => (p.actual != null && Number.isFinite(p.actual) ? { idx, x: getX(idx), y: getY(p.actual), val: p.actual, period: p.period } : null))
    .filter((x): x is NonNullable<typeof x> => x !== null);

  const predictedPoints = points
    .map((p, idx) => (p.predicted != null && Number.isFinite(p.predicted) ? { idx, x: getX(idx), y: getY(p.predicted), val: p.predicted, period: p.period } : null))
    .filter((x): x is NonNullable<typeof x> => x !== null);

  const bandPoints = points
    .map((p, idx) =>
      p.lower_bound != null && p.upper_bound != null && Number.isFinite(p.lower_bound) && Number.isFinite(p.upper_bound)
        ? { idx, x: getX(idx), yLow: getY(p.lower_bound), yHigh: getY(p.upper_bound) }
        : null
    )
    .filter((x): x is NonNullable<typeof x> => x !== null);

  const firstFutureIdx = points.findIndex(p => p.actual == null && p.predicted != null);

  // Pick up to 8 readable X-axis tick indices
  const tickIndices = new Set<number>([0, points.length - 1]);
  if (firstFutureIdx > 0) {
    tickIndices.add(firstFutureIdx - 1);
    tickIndices.add(firstFutureIdx);
  }
  const step = Math.max(1, Math.floor(points.length / 7));
  for (let i = 0; i < points.length; i += step) {
    tickIndices.add(i);
  }
  const sortedTicks = Array.from(tickIndices).sort((a, b) => a - b);

  const activeIdx = hoverIdx !== null && points[hoverIdx] ? hoverIdx : firstFutureIdx >= 0 ? firstFutureIdx : points.length - 1;
  const activePoint = points[activeIdx];

  return (
    <div className="space-y-3">
      {/* Interactive data readout bar */}
      {activePoint && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-800 bg-slate-950/90 px-4 py-2.5 text-xs">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-blue-300">Kỳ: {activePoint.period}</span>
            <span className="rounded-md bg-slate-800 px-2 py-0.5 text-[11px] text-slate-300">
              {activePoint.actual != null ? 'Dữ liệu lịch sử' : 'Kỳ dự báo tương lai'}
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <span className="text-slate-200">
              Quan sát đầu vào: <strong className="text-blue-300">{formatMeasure(activePoint.actual,unit)}</strong>
            </span>
            <span className="text-slate-200">
              Ước lượng & dự báo: <strong className="text-blue-300">{formatMeasure(activePoint.predicted,unit)}</strong>
            </span>
            {activePoint.lower_bound != null && activePoint.upper_bound != null && (
              <span className="text-slate-400">
                Khoảng tham khảo: [{formatMeasure(activePoint.lower_bound,unit)} – {formatMeasure(activePoint.upper_bound,unit)}]
              </span>
            )}
          </div>
        </div>
      )}

      <div className="rounded-xl border border-slate-800/80 bg-slate-950/50 p-3 sm:p-4">
        <svg
          viewBox="0 0 1000 325"
          className="w-full h-auto block select-none"
          role="img"
          aria-label={`Biểu đồ quan sát thực tế và dự báo cho chỉ tiêu ${targetVariable}`}
          onMouseLeave={() => setHoverIdx(null)}
        >
          {/* Forecast zone highlight */}
          {firstFutureIdx > 0 && (
            <g>
              <rect
                x={getX(firstFutureIdx - 1)}
                y={topY}
                width={rightX - getX(firstFutureIdx - 1)}
                height={height}
                fill="var(--chart-predicted)"
                fillOpacity="0.05"
              />
              <line
                x1={getX(firstFutureIdx - 1)}
                x2={getX(firstFutureIdx - 1)}
                y1={topY}
                y2={bottomY}
                stroke="var(--chart-predicted)"
                strokeOpacity="0.45"
                strokeDasharray="4 4"
                strokeWidth="1.5"
              />
              <text
                x={Math.min(rightX - 10, getX(firstFutureIdx - 1) + 8)}
                y={topY + 14}
                fill="var(--chart-predicted)"
                fontSize="11"
                fontWeight="600"
              >
                Vùng dự báo ({points[firstFutureIdx].period} → {points[points.length - 1].period})
              </text>
            </g>
          )}

          {/* Horizontal grid lines & Y-axis labels */}
          {[0, 1, 2, 3, 4].map(t => {
            const yPos = topY + (t * height) / 4;
            const val = maxVal - (t * span) / 4;
            return (
              <g key={t}>
                <line
                  x1={leftX}
                  x2={rightX}
                  y1={yPos}
                  y2={yPos}
                  stroke="rgba(167, 215, 209, 0.14)"
                  strokeDasharray="3 3"
                />
                <text
                  x={leftX - 10}
                  y={yPos + 4}
                  textAnchor="end"
                  fill="var(--color-slate-400)"
                  fontSize="11"
                >
                  {formatMeasure(val)}
                </text>
              </g>
            );
          })}

          {/* Confidence interval band */}
          {bandPoints.length >= 2 && (
            <polygon
              points={[
                ...bandPoints.map(p => `${p.x},${p.yHigh}`),
                ...bandPoints.slice().reverse().map(p => `${p.x},${p.yLow}`),
              ].join(' ')}
              fill="var(--chart-predicted)"
              fillOpacity="0.18"
              stroke="var(--chart-predicted)"
              strokeOpacity="0.3"
              strokeWidth="1"
            />
          )}

          {/* Historical Actual Line */}
          {actualPoints.length >= 2 && (
            <polyline
              points={actualPoints.map(p => `${p.x},${p.y}`).join(' ')}
              fill="none"
              stroke="var(--chart-actual)"
              strokeWidth="2.75"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Predicted & Forecast Line */}
          {predictedPoints.length >= 2 && (
            <polyline
              points={predictedPoints.map(p => `${p.x},${p.y}`).join(' ')}
              fill="none"
              stroke="var(--chart-predicted)"
              strokeWidth="2.5"
              strokeDasharray="7 5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Active hover vertical guideline */}
          {activePoint && (
            <line
              x1={getX(activeIdx)}
              x2={getX(activeIdx)}
              y1={topY}
              y2={bottomY}
              stroke="var(--chart-actual)"
              strokeOpacity="0.35"
              strokeWidth="1"
            />
          )}

          {/* Actual data nodes */}
          {actualPoints.map(p => (
            <circle
              key={`act-${p.idx}`}
              cx={p.x}
              cy={p.y}
              r={activeIdx === p.idx ? 5.5 : 3.2}
              fill="var(--chart-actual)"
              stroke="var(--color-bg)"
              strokeWidth="1.5"
            />
          ))}

          {/* Predicted/Forecast data nodes */}
          {predictedPoints.map(p => (
            <circle
              key={`pred-${p.idx}`}
              cx={p.x}
              cy={p.y}
              r={activeIdx === p.idx ? 5.5 : 3.2}
              fill="var(--chart-predicted)"
              stroke="var(--color-bg)"
              strokeWidth="1.5"
            />
          ))}

          {/* X-axis labels */}
          {sortedTicks.map(idx => {
            const pt = points[idx];
            if (!pt) return null;
            return (
              <text
                key={`tick-${idx}`}
                x={getX(idx)}
                y={bottomY + 26}
                textAnchor="middle"
                fill={pt.actual == null ? 'var(--chart-predicted)' : 'var(--color-slate-400)'}
                fontSize="11"
                fontWeight={pt.actual == null ? '600' : '400'}
              >
                {pt.period}
              </text>
            );
          })}

          {/* Invisible hover columns for smooth point selection */}
          {points.map((p, idx) => {
            const colWidth = width / Math.max(1, points.length);
            return (
              <rect
                key={`hit-${p.period}-${idx}`}
                x={getX(idx) - colWidth / 2}
                y={topY}
                width={colWidth}
                height={height}
                fill="transparent"
                className="cursor-pointer"
                onMouseEnter={() => setHoverIdx(idx)}
                onClick={() => setHoverIdx(idx)}
              />
            );
          })}
        </svg>

        {/* Legend */}
        <div className="mt-3 flex flex-wrap items-center justify-center gap-6 border-t border-slate-800/70 pt-3 text-xs text-slate-300">
          <span className="inline-flex items-center gap-2">
            <span className="inline-block h-0.5 w-6 bg-[var(--chart-actual)]" />
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-[var(--chart-actual)]" />
            Quan sát đầu vào (Thực tế)
          </span>
          <span className="inline-flex items-center gap-2">
            <span className="inline-block h-0.5 w-6 border-b-2 border-dashed border-[var(--chart-predicted)]" />
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-[var(--chart-predicted)]" />
            Ước lượng & dự báo (Học máy)
          </span>
          <span className="inline-flex items-center gap-2">
            <span className="inline-block h-3 w-5 rounded-sm border border-[var(--chart-predicted)]/40 bg-[var(--chart-predicted)]/20" />
            Khoảng tham khảo từ sai số mô hình
          </span>
        </div>
      </div>
    </div>
  );
}

export function AnalysisResultView({
  data, onBackToDashboard, onNewAnalysis, onUploadData, onResearch,
}: {
  data: AnalysisPayload;
  onBackToDashboard: () => void;
  onNewAnalysis: () => void;
  onUploadData?: () => void;
  onResearch?: (query: string) => void;
}) {
  const [forecastOpen, setForecastOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const readout = buildAnalysisReadout(data);
  const r = data.regression, v = data.data_validation;
  const sourceArticles = data.web_research?.sources || [];
  const measured = (value: number | null | undefined) => formatMeasure(value, readout.unit);
  const chartPoints = r.chart_data.map(p => {
    const futureIndex = r.future_forecast.findIndex(f => f.period === p.period);
    return p.actual == null && futureIndex >= 0 ? { ...p, period: readout.time.labels[futureIndex] } : p;
  });
  const exportCsv = () => save('du-bao.csv', '\uFEFF' + [
    ['period', 'display_period', 'actual', 'predicted', 'lower_bound', 'upper_bound', 'indicator', 'unit', 'scope', 'observed_entity', 'forecast_use'],
    ...r.chart_data.map((p,i) => [p.period, chartPoints[i].period, p.actual ?? '', p.predicted ?? '', p.lower_bound ?? '', p.upper_bound ?? '',
      readout.metric, readout.unit || 'Chưa xác định', readout.scope, readout.observedName, readout.qualityLabel]),
  ].map(row => row.map(csvCell).join(',')).join('\r\n'), 'text/csv;charset=utf-8');
  const downloadTemplate = () => save('mau-du-lieu-can-bo-sung.csv', '\uFEFF' + readout.guide.fields.map(csvCell).join(',') + '\r\n', 'text/csv;charset=utf-8');
  const exportJson = () => save('bao-cao.json', JSON.stringify({
    subject: data.product_name, category: data.category, dataset: data.dataset_name,
    evidence_scope: data.evidence_scope, data_context: data.data_context,
    interpretation: { conclusion: readout.title, explanation: readout.summary, metric: readout.metric, unit: readout.unit,
      observed_entity: readout.observedName, model_use: readout.qualityLabel, validation_explanation: readout.qualityReason,
      facts: readout.facts, next_steps: readout.actions },
    forecast: readout.legacy ? null : r,
    quality_score: data.quality_score, potential_score: data.potential_score,
    strategy_recommendation: data.strategy_recommendation,
    sources: sourceArticles, provenance_review_required: readout.legacy,
  }, null, 2), 'application/json');
  const national = readout.scope === 'national';
  const uncertain = readout.scope !== 'entity' || readout.quality !== 'supported' || readout.legacy;

  return (
    <div className="analysis-report analysis-readout space-y-7 py-3">
      <header className="space-y-5">
        <button type="button" onClick={onBackToDashboard} className="inline-flex items-center gap-2 text-sm text-slate-300 hover:text-white no-print">
          <ArrowLeft size={16}/> Quay lại tổng quan
        </button>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0 space-y-2">
            <p className="text-[11px] uppercase tracking-widest text-blue-300">Kết quả phân tích · {viLabel(data.category)}</p>
            <h1 className="text-3xl sm:text-4xl text-white break-words">{data.product_name}</h1>
            <p className="text-sm text-slate-400">Kết luận trước, căn cứ sau, rồi đến việc cần làm.</p>
          </div>
          <div className="flex flex-wrap gap-2 no-print">
            <button type="button" onClick={()=>save('tom-tat-phan-tich.md',analysisSummaryMarkdown(data,readout),'text/markdown;charset=utf-8')} className={action}><Download size={15}/>Tải bản tóm tắt</button>
            <button type="button" onClick={()=>window.print()} className={action}><Printer size={15}/>In / Lưu PDF</button>
          </div>
        </div>
      </header>

      <section id="analysis-conclusion" aria-labelledby="analysis-conclusion-title" className={`readout-conclusion rounded-2xl border p-5 sm:p-7 space-y-5 ${uncertain?'border-amber-500/35':'border-blue-400/40'}`}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="readout-eyebrow">01 · Kết luận cho lần phân tích này</p>
          <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs border ${uncertain?'border-amber-500/30 text-amber-200':'border-blue-400/30 text-blue-300'}`}>
            {uncertain?<Info size={14}/>:<CheckCircle2 size={14}/>}
            {readout.legacy?'Cần phân tích lại':national?'Dữ liệu cấp quốc gia':readout.scope==='dataset'?'Cần xác nhận đối tượng':readout.qualityLabel}
          </span>
        </div>
        <h2 id="analysis-conclusion-title" className="max-w-4xl text-2xl sm:text-3xl text-white leading-snug">{readout.title}</h2>
        <p className="max-w-4xl text-sm sm:text-base leading-relaxed text-slate-200">{readout.summary}</p>
        <div className="flex flex-wrap gap-3 no-print">
          {onUploadData&&<button type="button" onClick={onUploadData} className="primary-action inline-flex items-center justify-center gap-2 px-4 py-3 text-sm"><Database size={16}/>{readout.scope==='entity'?'Cập nhật dữ liệu của đối tượng':'Bổ sung dữ liệu đúng đối tượng'}<ArrowUpRight size={16}/></button>}
          {onResearch&&<button type="button" onClick={()=>onResearch(data.product_name)} className={action}><Search size={16}/>Tìm hiểu đối tượng qua nguồn web</button>}
        </div>
      </section>

      <div className="no-print"><ReportAdvisor key={data.session_id} query={data.product_name} analysisId={data.session_id}/></div>

      {!readout.legacy&&<section aria-label="Ba căn cứ chính" className="grid md:grid-cols-3 gap-4">
        {readout.facts.map((fact,index)=><article key={fact.label} className="glass-panel rounded-2xl p-5 sm:p-6 space-y-3">
          <p className="text-xs text-slate-400">{fact.label}</p>
          <h3 className={`${index===1?'text-2xl sm:text-3xl tabular-nums':'text-lg sm:text-xl'} text-white leading-snug`}>{fact.value}</h3>
          <p className="text-xs leading-relaxed text-slate-300">{fact.note}</p>
        </article>)}
      </section>}

      {!!readout.subjectSources.length&&<section aria-labelledby="analysis-subject-title" className="space-y-4">
        <div className="space-y-2"><h2 id="analysis-subject-title" className="text-xl text-white">Các tài liệu nói gì về {data.product_name}?</h2><p className="text-xs text-slate-400">Trích đoạn tìm thấy cho đúng tên đã nhập; cần mở nguồn để đối chiếu. Những nội dung này tách biệt với chuỗi số liệu dự báo.</p></div>
        <div className="grid lg:grid-cols-3 gap-4">{readout.subjectSources.map(source=><article key={source.url} className="rounded-xl border border-slate-700 p-5 space-y-3"><p className="text-[11px] text-slate-400">{new URL(source.url).hostname}</p><a href={source.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-start gap-2 text-sm font-semibold text-blue-300 hover:underline">{source.title}<ExternalLink size={14} className="shrink-0 mt-0.5"/></a><blockquote className="text-xs leading-relaxed text-slate-300">{source.excerpt.length>300?source.excerpt.slice(0,300).replace(/\s+\S*$/,'')+'…':source.excerpt||'Mở tài liệu gốc để đọc nội dung.'}</blockquote></article>)}</div>
      </section>}

      <section aria-labelledby="analysis-actions-title" className="space-y-5">
        <div className="space-y-2"><p className="readout-eyebrow">02 · Từ kết quả đến hành động</p>
          <h2 id="analysis-actions-title" className="text-2xl text-white">Bạn nên làm gì tiếp theo?</h2>
          <p className="text-sm text-slate-400">{readout.scope==='entity'?'Ưu tiên việc giúp kiểm tra dự báo bằng kết quả thực tế.':`Muốn đánh giá riêng ${data.product_name}, cần hoàn thành ba việc sau.`}</p>
        </div>
        <div className="grid lg:grid-cols-3 gap-4">
          {readout.actions.map((step,index)=><article key={step.title} className="glass-panel rounded-2xl p-5 sm:p-6 flex flex-col gap-4">
            <div className="flex items-start gap-3"><span className="readout-step shrink-0">{String(index+1).padStart(2,'0')}</span><h3 className="text-base text-white leading-snug">{step.title}</h3></div>
            <p className="text-sm leading-relaxed text-slate-300">{step.description}</p>
            <div className="mt-auto border-t border-slate-700 pt-4 space-y-1.5"><p className="text-[11px] uppercase tracking-wider text-blue-300">Kết quả cần có</p><p className="text-xs leading-relaxed text-slate-200">{step.deliverable}</p></div>
          </article>)}
        </div>
        <div className="rounded-xl border border-slate-700 bg-slate-950 p-4 flex flex-wrap items-center justify-between gap-3 no-print">
          <p className="text-xs text-slate-300 max-w-2xl">Mẫu CSV chỉ chứa tên cột. Điền số liệu thật của từng kỳ, ghi rõ đơn vị trước khi tải lên.</p>
          <button type="button" onClick={downloadTemplate} className="inline-flex items-center gap-2 text-sm text-blue-300 underline underline-offset-4"><Download size={15}/>Tải mẫu cột dữ liệu</button>
        </div>
      </section>

      {!readout.legacy&&<section className="glass-panel rounded-2xl p-5 sm:p-6 space-y-5">
        <button type="button" aria-expanded={forecastOpen} aria-controls="analysis-forecast-content" onClick={()=>setForecastOpen(!forecastOpen)} className="flex items-start justify-between w-full gap-4 text-left">
          <span className="space-y-2"><span className="readout-eyebrow block">03 · Đối chiếu số liệu</span><span className="text-xl text-white block">Xem dữ liệu & đường dự báo</span><span className="text-xs text-slate-400 block">{readout.history.length} quan sát · {readout.time.range} · {r.future_forecast.length} bước dự báo từ cuối chuỗi</span></span>
          <ChevronDown size={20} className={`shrink-0 mt-2 transition-transform ${forecastOpen?'rotate-180':''}`}/>
        </button>
        <div id="analysis-forecast-content" className={forecastOpen?'space-y-5':'print-only space-y-5'}>
          <div className="rounded-xl border border-slate-700 bg-slate-950 p-4 space-y-2">
            <p className="text-sm text-white">{readout.metric}{readout.unit?` · ${readout.unit}`:' · Chưa ghi rõ đơn vị'}</p>
            <p className="text-xs text-slate-300">{readout.qualityReason}</p>
            <p className="text-xs text-slate-400">{readout.time.cadence==='period'?'Mỗi bước là một lần tiến của mô hình; dữ liệu chưa đủ để gắn chắc với lịch ngày/tháng/năm.':`Chuỗi kết thúc ở ${readout.time.last}. Các mốc ${readout.time.labels[0]}–${readout.time.labels.at(-1)} là ước lượng tính từ mốc này, chưa phải số liệu đã xảy ra.`}</p>
            {readout.time.gaps&&<p className="text-xs text-amber-200">Chuỗi có kỳ thiếu hoặc trùng; cần chuẩn hóa thời gian trước khi sử dụng dự báo.</p>}
          </div>
          <ForecastSvgChart points={chartPoints} targetVariable={readout.metric} unit={readout.unit}/>
          <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Bảng giá trị dự báo có đơn vị">
            <table className="w-full text-left text-sm"><thead><tr className="border-b border-slate-700">{['Mốc dự báo','Ước lượng','Khoảng tham khảo từ','Đến'].map(h=><th className="p-3" scope="col" key={h}>{h}</th>)}</tr></thead>
              <tbody>{r.future_forecast.map((p,i)=><tr key={p.period} className="border-b border-slate-800"><th scope="row" className="p-3 font-medium text-white">{readout.time.labels[i]}</th><td className="p-3 text-blue-300" title={`${fmtNum(p.forecast_value)} ${readout.unit||''}`}>{measured(p.forecast_value)}</td><td className="p-3">{measured(p.lower_bound)}</td><td className="p-3">{measured(p.upper_bound)}</td></tr>)}</tbody>
            </table>
          </div>
          <p className="text-xs text-slate-400">Khoảng tham khảo được tính từ sai số mô hình; chưa bảo đảm một xác suất bao phủ cụ thể.</p>
          <button type="button" onClick={exportCsv} className={`${action} no-print`}><Download size={15}/>CSV kết quả dự báo</button>
        </div>
      </section>}

      <section id="analysis-data" className="glass-panel rounded-2xl p-5 sm:p-6 space-y-4" aria-labelledby="analysis-data-title">
        <div className="space-y-2"><p className="readout-eyebrow">Nguồn & phạm vi</p><h2 id="analysis-data-title" className="text-xl text-white">Các con số đến từ đâu?</h2></div>
        <dl className="readout-provenance grid sm:grid-cols-2 gap-x-8 gap-y-4 text-sm">
          <div><dt>Đối tượng được đo</dt><dd>{readout.observedName}</dd></div><div><dt>Chỉ tiêu</dt><dd>{readout.metric}</dd></div>
          <div><dt>Thời gian có dữ liệu</dt><dd>{readout.time.range} · {readout.history.length} quan sát được đưa vào dự báo</dd></div>
          <div><dt>Đơn vị</dt><dd>{readout.unitStatus==='mixed'?'Có nhiều đơn vị trong tệp; cần chuẩn hóa':readout.unit||'Chưa ghi rõ trong tệp'}</dd></div>
        </dl>
        {!!readout.sourceUrls.length&&<div className="border-t border-slate-700 pt-4 space-y-2">{readout.sourceUrls.map(url=><a key={url} href={url} target="_blank" rel="noopener noreferrer" className="inline-flex items-start gap-2 text-sm text-blue-300 underline"><ExternalLink size={14} className="shrink-0 mt-1"/>{url.includes('api.worldbank.org')?'Mở dữ liệu gốc trên World Bank':`Đối chiếu nguồn: ${new URL(url).hostname}`}</a>)}</div>}
        <p className="text-xs text-slate-400">{national?`Nguồn quốc gia giúp hiểu bối cảnh; cần thêm dữ liệu riêng để kết luận về ${data.product_name}.`:'Tên nguồn và độ sạch của tệp chưa thay thế việc đối chiếu từng quan sát với số liệu thực tế.'}</p>
      </section>

      <section className="rounded-2xl border border-slate-700 p-5 sm:p-6 space-y-4">
        <button type="button" aria-expanded={detailOpen} aria-controls="analysis-technical-content" onClick={()=>setDetailOpen(!detailOpen)} className="flex items-center justify-between gap-3 w-full text-left text-sm text-slate-300">Thông số kiểm định & dữ liệu báo cáo<ChevronDown size={18} className={detailOpen?'rotate-180':''}/></button>
        <div id="analysis-technical-content" className={detailOpen?'space-y-5':'print-only space-y-5'}>
          <dl className="readout-provenance grid sm:grid-cols-2 gap-4 text-xs">
            <div><dt>Bộ dữ liệu</dt><dd className="break-all">{data.dataset_name}</dd></div><div><dt>Mã báo cáo</dt><dd>{data.session_id}</dd></div>
            <div><dt>Cột đang dự báo</dt><dd>{r.target_variable}{readout.code?` · ${readout.code}`:''}</dd></div><div><dt>Độ sạch dữ liệu</dt><dd>{data.quality_score}/100 · thiếu {v.missing_pct}% · trùng {v.duplicate_pct}%</dd></div>
          </dl>
          {!readout.legacy&&<div className="rounded-xl bg-slate-950 p-4 space-y-3 text-xs">
            <p className="text-sm text-white">Sai số được hiểu thế nào?</p>
            <p><strong>MAE:</strong> {measured(r.metrics.mae)}. Trung bình độ lệch tuyệt đối giữa dự báo và số thực tế ở phần dữ liệu được đánh giá.</p>
            <p><strong>R²:</strong> {fmtNum(r.metrics.r2_score,4)}. {r.metrics.r2_score<0?'Giá trị âm nghĩa là mô hình kém hơn cách dùng trung bình của tập kiểm tra. Đây không phải phần trăm độ chính xác.':'Đo mức giải thích biến thiên trong phần dữ liệu được đánh giá; không phải phần trăm độ chính xác.'}</p>
            <p><strong>RMSE:</strong> {measured(r.metrics.rmse)}. Chỉ số này nhấn mạnh hơn các lần dự báo sai nhiều.</p>
            {r.validation?<p>{r.validation.mode==='heldout'?`Đã học từ ${r.validation.train_rows} dòng; kiểm tra trên ${r.validation.test_rows} dòng (${r.validation.test_start}–${r.validation.test_end}). Sai số khi giữ giá trị kỳ trước: ${measured(r.validation.baseline_mae)}.`:'Chỉ đánh giá trên dữ liệu đã dùng huấn luyện; chưa có phần kiểm tra độc lập.'}</p>:<p>Báo cáo đã lưu chưa có mốc chia dữ liệu và sai số của cách giữ kỳ trước. Phân tích lại để bổ sung thông tin này.</p>}
            <p>Kiểm định mô tả kết quả trên dữ liệu cũ; chưa xác nhận độ chính xác của từng kỳ dự báo tương lai.</p>
            <p><strong>Phân loại:</strong> {data.classification.current_market_classification}. <strong>Phân nhóm:</strong> {data.clustering.current_item_cluster.cluster_name}. Đây là nhóm quan sát trong tệp, chưa phải xếp hạng sản phẩm ngoài thực tế.</p>
            {readout.scope==='entity'&&<p>Điểm quy tắc của tập dữ liệu: {data.potential_score}/100. Điểm này không đo chất lượng sản phẩm hay xác suất thành công kinh doanh.</p>}
          </div>}
          {!!sourceArticles.length&&<div className="space-y-2"><p className="text-sm text-white">Tài liệu về từ khóa cần đối chiếu</p><p className="text-xs text-slate-400">Các bài viết này tách biệt với chuỗi số liệu dùng để huấn luyện.</p>{sourceArticles.slice(0,8).map(s=><a key={s.url} href={s.url} target="_blank" rel="noopener noreferrer" className="flex items-start gap-2 text-xs text-blue-300 underline"><ExternalLink size={13} className="shrink-0 mt-1"/>{s.title}</a>)}</div>}
          <button type="button" onClick={exportJson} className={`${action} no-print`}><Download size={15}/>Tải dữ liệu báo cáo (JSON)</button>
        </div>
      </section>
      <button type="button" onClick={onNewAnalysis} className="inline-flex items-center gap-2 text-sm text-blue-300 underline underline-offset-4 no-print">Phân tích một đối tượng khác<ArrowUpRight size={15}/></button>
    </div>
  );
}

