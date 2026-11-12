export interface AnalysisRequest {
  product_name: string;
  category: string;
  description: string;
  dataset_name: string;
  custom_roles?: Record<string, string | null>;
}

export interface AnalysisJob {
  job_id: string;
  status: 'queued' | 'running' | 'complete' | 'failed';
  step: number;
  message: string;
  session_id: string | null;
}

export interface DatasetPreview {
  columns: string[];
  rows: Record<string, unknown>[];
  total_rows: number;
}
