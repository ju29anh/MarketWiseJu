import { useEffect, useRef, useState } from 'react';
import { API_BASE, safeFetch } from '../api/http';
import { MarketReportPanel, type MarketReport } from './MarketReportPanel';

export function ResearchReference({ query, initialReport }: { query: string; initialReport?: MarketReport | null }) {
  const [loadedReport, setLoadedReport] = useState<{query:string;report:MarketReport} | null>(null);
  const report = initialReport || (loadedReport?.query === query ? loadedReport.report : null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), [query]);
  async function load() {
    controller.current?.abort();
    const abort = new AbortController();
    controller.current = abort;
    setBusy(true);
    setError('');
    try {
      const response = await safeFetch(`${API_BASE}/research/context`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
        signal: abort.signal,
      });
      const value = await response.json();
      if (!abort.signal.aborted) setLoadedReport({query,report:value});
    } catch (e) {
      if (!abort.signal.aborted) setError(e instanceof Error ? e.message : 'Chưa tải được bối cảnh.');
    } finally {
      if (!abort.signal.aborted) setBusy(false);
    }
  }
  return (
    <section className="rounded-2xl border border-slate-700 p-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg text-white">Bối cảnh định lượng cấp quốc gia</h3>
          <p className="text-sm text-slate-400">
            Chuỗi số liệu World Bank WDI và kiểm định dự báo. Để lập kế hoạch cho đối tượng đang nghiên cứu, mở mục Trao đổi & lập kế hoạch.
          </p>
        </div>
        {!report && (
          <button
            type="button"
            onClick={() => void load()}
            disabled={busy}
            className="rounded-xl border border-slate-600 px-4 py-3 text-sm text-blue-300 disabled:opacity-50"
          >
            {busy ? 'Đang tải chuỗi tham khảo…' : 'Xem dữ liệu tham khảo quốc gia'}
          </button>
        )}
      </div>
      {error && <p role="alert" className="text-sm text-amber-200">{error}</p>}
      {report && <MarketReportPanel report={report} />}
    </section>
  );
}
