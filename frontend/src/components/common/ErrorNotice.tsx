import { API_BASE } from '../../api/http';
import { AppIcon } from '../icons';

export function ErrorNotice({ message, retry }: { message: string; retry?: () => void }) {
  return <div role="alert" className="rounded-2xl border border-rose-400/40 bg-rose-950/30 p-4 text-sm text-rose-100">
    <p className="flex items-start gap-2"><AppIcon name="AlertCircle" size={20} className="shrink-0" />{message}</p>
    <div className="mt-3 flex flex-wrap gap-3">
      {retry && <button type="button" onClick={retry} className="rounded-lg bg-slate-800 px-4 py-2 text-white hover:bg-slate-700">Thử lại</button>}
      <a href={`${API_BASE}/datasets/template`} download className="rounded-lg px-4 py-2 text-blue-200 underline">Tải file mẫu CSV</a>
    </div>
  </div>;
}
