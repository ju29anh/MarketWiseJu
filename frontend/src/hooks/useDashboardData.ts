import { useEffect, useState } from 'react';
import { apiClient } from '../api/client';
import type { Category, DashboardSummary, DatasetMeta } from '../types';
import { errorMessage } from '../utils/errors';

export function useDashboardData() {
  const [data, setData] = useState<{ summary: DashboardSummary | null; datasets: DatasetMeta[]; categories: Category[] }>({ summary: null, datasets: [], categories: [] });
  const [isLoading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    Promise.all([apiClient.getDashboardSummary(controller.signal), apiClient.getDatasets(controller.signal), apiClient.getCategories(controller.signal)])
      .then(([summary, datasets, categories]) => { if (!controller.signal.aborted) setData({ summary, datasets, categories }); })
      .catch(err => { if (!controller.signal.aborted) setError(errorMessage(err)); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [revision]);
  return {
    ...data,
    isLoading,
    error,
    retry: () => {
      setLoading(true);
      setError(null);
      setRevision(value => value + 1);
    }
  };
}
