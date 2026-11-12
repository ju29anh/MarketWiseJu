import { friendlyStatus } from '../utils/errors';

// Use the configured backend, or the same-origin /api proxy.
export const API_BASE = `${(import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')}/api`;

function extractErrorDetail(rawText: string, status: number): string {
  try {
    const parsed = JSON.parse(rawText);
    if (typeof parsed?.detail === 'string' && parsed.detail.trim()) return parsed.detail.trim();
  } catch {
    // Proxies may return an HTML error page.
  }
  return friendlyStatus(status);
}

export async function safeFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const requestSignal = init?.signal ?? (input instanceof Request ? input.signal : undefined);
  const rawUrl = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
  const timeout = AbortSignal.timeout(/\/research\/(search|compare|context|tts|ask|chat)(?:\?|$)/.test(rawUrl) ? 120_000 : 45_000);
  const signal = requestSignal ? AbortSignal.any([requestSignal, timeout]) : timeout;
  let response: Response;
  try {
    response = await fetch(input, { ...init, signal });
  } catch (error) {
    if (requestSignal?.aborted) throw error;
    throw new Error(timeout.aborted
      ? 'Máy chủ xử lý quá lâu. Vui lòng thử lại sau.'
      : 'Không kết nối được máy chủ. Hãy kiểm tra kết nối rồi thử lại.');
  }
  // Do not replay a POST or substitute generated results after a connection failure.
  if (!response.ok) throw new Error(extractErrorDetail(await response.text().catch(() => ''), response.status));
  if (response.headers.get('content-type')?.includes('text/html')) {
    throw new Error('Chưa nhận được dữ liệu từ dịch vụ. Hãy thử lại sau.');
  }
  return response;
}

export function uploadFile<T>(endpoint: string, file: File, category: string,
  onProgress?: (value: number) => void, signal?: AbortSignal): Promise<T> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) { reject(new DOMException('Aborted', 'AbortError')); return; }
    const xhr = new XMLHttpRequest();
    const abort = () => xhr.abort();
    const clean = () => signal?.removeEventListener('abort', abort);
    xhr.open('POST', `${API_BASE}${endpoint}`);
    xhr.timeout = 45_000;
    xhr.upload.onprogress = event => {
      if (event.lengthComputable && !signal?.aborted) onProgress?.(Math.round(event.loaded / event.total * 100));
    };
    xhr.onload = () => {
      clean();
      if (signal?.aborted) { reject(new DOMException('Aborted', 'AbortError')); return; }
      if (xhr.status >= 200 && xhr.status < 300) {
        try { resolve(JSON.parse(xhr.responseText)); }
        catch { reject(new Error('Máy chủ trả về dữ liệu không hợp lệ. Hãy thử lại sau.')); }
      } else reject(new Error(extractErrorDetail(xhr.responseText, xhr.status)));
    };
    xhr.onerror = () => { clean(); reject(new Error('Không tải được file lên máy chủ. Hãy kiểm tra kết nối rồi thử lại.')); };
    xhr.ontimeout = () => { clean(); reject(new Error('Tải file quá thời gian chờ. Vui lòng thử lại.')); };
    xhr.onabort = () => { clean(); reject(new DOMException('Aborted', 'AbortError')); };
    signal?.addEventListener('abort', abort, { once: true });
    const body = new FormData();
    body.append('file', file);
    body.append('category', category);
    xhr.send(body);
  });
}

export async function downloadDatasetCsv(datasetId: string, event?: { preventDefault: () => void }): Promise<void> {
  event?.preventDefault();
  const response = await safeFetch(`${API_BASE}/research/datasets/${encodeURIComponent(datasetId)}/csv`);
  if (!response.headers.get('content-type')?.includes('text/csv')) {
    throw new Error('Máy chủ chưa trả về file CSV hợp lệ. Vui lòng thử lại.');
  }
  const url = URL.createObjectURL(await response.blob());
  const a = document.createElement('a');
  a.href = url;
  a.download = `du-lieu-phan-tich-${datasetId.slice(0, 12)}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}

