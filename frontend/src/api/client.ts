import {
  Category,
  DatasetMeta,
  DataValidation,
  AnalysisPayload,
  DashboardSummary
} from '../types';

import { API_BASE, safeFetch, uploadFile } from './http';
import type { DatasetPreview } from '../types/jobs';

export const apiClient = {
  async getCategories(signal?: AbortSignal): Promise<Category[]> {
    const res = await safeFetch(`${API_BASE}/categories`, { signal });
    const data = await res.json();
    return data.categories;
  },

  async getDatasets(signal?: AbortSignal): Promise<DatasetMeta[]> {
    const res = await safeFetch(`${API_BASE}/datasets`, { signal });
    const data = await res.json();
    return data.datasets;
  },

  async getDashboardSummary(signal?: AbortSignal): Promise<DashboardSummary> {
    const res = await safeFetch(`${API_BASE}/dashboard/stats`, { signal });
    return await res.json();
  },

  async validateDataset(dataset_name: string, signal?: AbortSignal): Promise<DataValidation> {
    const res = await safeFetch(`${API_BASE}/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dataset_name }),
      signal
    });
    return await res.json();
  },

  async uploadDataset(file: File, category: string, onProgress?: (value: number) => void, signal?: AbortSignal): Promise<{ filename: string; validation: DataValidation; preview: DatasetPreview }> {
    return uploadFile('/datasets/upload', file, category, onProgress, signal);
  },

  async getAnalysisById(sessionId: string, signal?: AbortSignal): Promise<AnalysisPayload> {
    const res = await safeFetch(`${API_BASE}/analysis/${encodeURIComponent(sessionId)}`, { signal });
    return await res.json();
  },

  async synthesizeTTS(text: string, voice: string = 'Kore', signal?: AbortSignal): Promise<{
    audio_base64: string | null;
    mime_type: string | null;
    assistant_name: string;
    fallback_browser_tts: boolean;
    clean_text: string;
  }> {
    const res = await safeFetch(`${API_BASE}/research/tts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, voice }),
      signal
    });
    return await res.json();
  },

  async getDatasetProducts(filename: string, signal?: AbortSignal): Promise<{ products: string[]; item_col: string | null }> {
    const res = await safeFetch(`${API_BASE}/datasets/${encodeURIComponent(filename)}/products`, { signal });
    return await res.json();
  },

  async getMarketOverview(q: string, signal?: AbortSignal): Promise<{
    query: string;
    found: boolean;
    source: 'csv_dataset' | 'wikipedia' | 'fallback_nearest' | null;
    market_data: {
      category: string;
      dataset_filename?: string;
      dataset_title?: string;
      source_citation?: string;
      total_records?: number;
      top_items?: string[];
      target_product_name?: string;
      custom_query_name?: string;
      is_exact_product?: boolean;
      price_stats?: { avg: number; min: number; max: number; currency: string };
      avg_growth_pct?: number;
      avg_rating?: number;
      total_demand?: number;
      market_potential_distribution?: Record<string, number>;
      matched_keyword?: string;
      description?: string;
    } | null;
    wiki_summary: { title: string; extract: string; page_url: string; thumbnail: string | null } | null;
    suggestions: string[];
  }> {
    const res = await safeFetch(`${API_BASE}/market-overview?q=${encodeURIComponent(q)}`, { signal });
    return await res.json();
  }
};
