export function LoadingSkeleton() {
  return <div role="status" aria-label="Đang tải dữ liệu" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 py-6">
    <span className="sr-only">Đang tải dữ liệu, vui lòng chờ.</span>
    {[0, 1, 2, 3].map(i => <div key={i} aria-hidden="true" className="rounded-2xl border border-slate-700 bg-slate-900 p-6 animate-pulse">
      <div className="h-4 w-2/3 rounded bg-slate-700 mb-5" /><div className="h-9 w-1/2 rounded bg-slate-800" />
    </div>)}
  </div>;
}
