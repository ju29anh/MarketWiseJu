import { useEffect, useRef, useState } from 'react';
import { API_BASE, uploadFile, safeFetch } from '../../api/http';
import type { DatasetPreview } from '../../types/jobs';
import { errorMessage } from '../../utils/errors';
import { AppIcon } from '../icons';
import { ErrorNotice } from './ErrorNotice';

export function DatasetUpload({
  file,
  onChange,
  onPreview,
  disabled,
}: {
  file: File | null;
  onChange: (file: File | null) => void;
  onPreview?: (preview: DatasetPreview) => void;
  disabled: boolean;
}) {
  const input = useRef<HTMLInputElement>(null);
  const request = useRef<AbortController | null>(null);
  const [dragging, setDragging] = useState(false);
  const [preview, setPreview] = useState<DatasetPreview | null>(null);
  const [progress, setProgress] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [candidate, setCandidate] = useState<File | null>(file);
  const [maxUploadMb, setMaxUploadMb] = useState(20);
  useEffect(() => {
    const controller = new AbortController();
    safeFetch(`${API_BASE}/config`, { signal: controller.signal })
      .then(r => r.json())
      .then(data => {
        if (!controller.signal.aborted && Number.isFinite(data.max_upload_mb) && data.max_upload_mb > 0)
          setMaxUploadMb(data.max_upload_mb);
      })
      .catch(() => {});
    return () => controller.abort();
  }, []);
  useEffect(() => () => request.current?.abort(), []);
  async function select(next: File) {
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    onChange(null);
    setCandidate(next);
    setPreview(null);
    setError(null);
    setProgress(0);
    setBusy(false);
    if (!/\.(csv|xlsx)$/i.test(next.name)) {
      setError('Chỉ nhận định dạng .csv và .xlsx.');
      return;
    }
    if (next.size > maxUploadMb * 1024 * 1024 || next.size === 0) {
      setError(`Chọn file có dữ liệu, dung lượng tối đa ${maxUploadMb} MB.`);
      return;
    }
    setBusy(true);
    try {
      const data = await uploadFile<DatasetPreview>('/datasets/preview', next, '', setProgress, controller.signal);
      if (!controller.signal.aborted) {
        setPreview(data);
        onChange(next);
        onPreview?.(data);
      }
    } catch (err) {
      if (!controller.signal.aborted) setError(errorMessage(err));
    } finally {
      if (!controller.signal.aborted) setBusy(false);
    }
  }
  return (
    <div className="space-y-3 min-w-0">
      <div
        onDragOver={event => {
          event.preventDefault();
          if (!disabled) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={event => {
          event.preventDefault();
          setDragging(false);
          if (!disabled && event.dataTransfer.files[0]) void select(event.dataTransfer.files[0]);
        }}
        className={`rounded-2xl border-2 border-dashed p-5 text-center transition-colors ${dragging ? 'border-blue-400 bg-blue-500/20' : 'border-slate-600 bg-slate-950/60'}`}
      >
        <AppIcon name="upload" size={32} className="mx-auto text-blue-300 mb-3" />
        <p className="text-sm font-semibold">Kéo thả bộ dữ liệu vào đây</p>
        <p className="text-xs text-slate-400 my-2">CSV UTF-8 hoặc XLSX · tối đa {maxUploadMb} MB · xem trước 5 dòng</p>
        <input
          ref={input}
          type="file"
          accept=".csv,.xlsx"
          className="sr-only"
          aria-label="Chọn bộ dữ liệu CSV hoặc XLSX"
          disabled={disabled}
          onChange={event => {
            const next = event.target.files?.[0];
            if (next) void select(next);
            event.target.value = '';
          }}
        />
        <button
          type="button"
          disabled={disabled}
          onClick={() => input.current?.click()}
          className="bg-blue-600 hover:bg-blue-500 rounded-lg px-4 py-2 text-sm font-semibold disabled:opacity-50"
        >
          Chọn file
        </button>
        <a href={`${API_BASE}/datasets/template`} className="block mt-3 text-xs text-blue-300 underline" download>
          Tải file mẫu CSV
        </a>
      </div>
      {candidate && (
        <p className="text-xs text-slate-300 break-all">
          {candidate.name} · {(candidate.size / 1024).toLocaleString('vi-VN', { maximumFractionDigits: 1 })} KB
        </p>
      )}
      {busy && (
        <div role="status" className="space-y-2 text-xs text-blue-200">
          <p>{progress < 100 ? `Đang tải bản xem trước: ${progress}%` : 'Đã tải xong, đang đọc dữ liệu…'}</p>
          <progress aria-label="Tiến trình tải bản xem trước" value={progress} max={100} className="w-full accent-blue-500" />
        </div>
      )}
      {error && <ErrorNotice message={error} retry={candidate ? () => void select(candidate) : undefined} />}
      {preview && (
        <div className="rounded-xl border border-slate-700 overflow-hidden">
          <p className="p-3 text-xs text-emerald-300">
            {preview.total_rows.toLocaleString('vi-VN')} dòng · {preview.columns.length} cột · Sẵn sàng kiểm định
          </p>
          <div className="overflow-x-auto max-h-52" tabIndex={0} role="region" aria-label="Xem trước dữ liệu">
            <table className="text-xs text-left w-full">
              <caption className="sr-only">Năm dòng dữ liệu đầu tiên</caption>
              <thead className="bg-slate-800">
                <tr>
                  {preview.columns.map(col => (
                    <th key={col} scope="col" className="p-2 whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.rows.map((row, index) => (
                  <tr key={index} className="border-t border-slate-800">
                    {preview.columns.map(col => (
                      <td key={col} className="p-2 whitespace-nowrap max-w-52 truncate">
                        {String(row[col] ?? '—')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
