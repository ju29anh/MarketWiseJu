import { useEffect, useRef, useState } from 'react';
import { apiClient } from '../api/client';
import { API_BASE, safeFetch } from '../api/http';
import type { AnalysisJob, AnalysisRequest } from '../types/jobs';
import type { AnalysisPayload } from '../types';
import { errorMessage } from '../utils/errors';

function delay(signal: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    const abort = () => { clearTimeout(timer); reject(new DOMException('Aborted', 'AbortError')); };
    const timer = setTimeout(() => { signal.removeEventListener('abort', abort); resolve(); }, 700);
    signal.addEventListener('abort', abort, { once: true });
    if (signal.aborted) abort();
  });
}

export function useAnalysis() {
  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);

  async function run(payload: AnalysisRequest): Promise<AnalysisPayload | null> {
    controller.current?.abort();
    const current = new AbortController();
    controller.current = current;
    const { signal } = current;
    setError(null);
    setJob(null);
    try {
      let status: AnalysisJob = await (await safeFetch(`${API_BASE}/analysis/jobs`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload), signal,
      })).json();
      while (!signal.aborted) {
        setJob(status);
        if (status.status === 'failed') throw new Error(status.message);
        if (status.status === 'complete' && status.session_id) {
          const result = await apiClient.getAnalysisById(status.session_id, signal);
          return signal.aborted ? null : result;
        }
        await delay(signal);
        status = await (await safeFetch(`${API_BASE}/analysis/jobs/${status.job_id}`, { signal })).json();
      }
    } catch (err) {
      if (!signal.aborted) setError(errorMessage(err));
    }
    return null;
  }
  return { run, job, error };
}
