export interface Category {
  id: number;
  name: string;
  name_vi: string;
  icon: string;
  description: string;
}

export interface DatasetMeta {
  id: number;
  title: string;
  category: string;
  filename: string;
  filepath: string;
  source: string;
  total_rows: number;
  quality_score: number;
  created_at?: string;
}

export interface OutlierDetail {
  count: number;
  lower_bound: number;
  upper_bound: number;
  min: number;
  max: number;
  mean: number;
  std: number;
}

export interface ColumnRoles {
  sales_col?: string | null;
  price_col?: string | null;
  search_col?: string | null;
  rating_col?: string | null;
  growth_col?: string | null;
  competition_col?: string | null;
  date_col?: string | null;
  item_col?: string | null;
  target_col?: string | null;
}

export interface DataValidation {
  valid: boolean;
  quality_score: number;
  total_rows: number;
  total_columns: number;
  numeric_columns: string[];
  categorical_columns: string[];
  missing_values_count: number;
  missing_pct: number;
  duplicate_rows_count: number;
  duplicate_pct: number;
  outlier_count: number;
  outlier_pct: number;
  outlier_details: Record<string, OutlierDetail>;
  column_roles: ColumnRoles;
  explanations: string[];
  sample_data: Record<string, any>[];
  error?: string;
}

export interface ForecastPoint {
  period: string;
  actual?: number | null;
  predicted?: number | null;
  lower_bound?: number;
  upper_bound?: number;
  is_future?: boolean;
}

export interface RegressionModelComparison {
  name: string;
  type: string;
  r2_score: number;
  mae: number;
  rmse: number;
  mape?: number;
}

export interface RegressionResult {
  model_name: string;
  best_model_name?: string;
  supporting_models?: RegressionModelComparison[];
  target_variable: string;
  features_used: string[];
  metrics: {
    mae: number;
    rmse: number;
    r2_score: number;
    mape?: number;
  };
  validation?: {
    mode: 'heldout' | 'in_sample'; train_rows: number; test_rows: number;
    train_end: string; test_start: string | null; test_end: string | null;
    baseline_mae: number | null; beats_baseline: boolean | null;
  };
  coefficients: Record<string, number>;
  intercept: number;
  trend_direction: "Increasing" | "Decreasing";
  projected_growth_pct: number;
  chart_data: ForecastPoint[];
  future_forecast: {
    period: string;
    forecast_value: number;
    lower_bound: number;
    upper_bound: number;
  }[];
}

export interface ModelComparison {
  name: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  type: string;
}

export interface ClassificationResult {
  target_variable: string;
  classes: string[];
  current_market_classification: string;
  classification_confidence: number;
  best_classifier_name?: string;
  models_comparison: ModelComparison[];
  supporting_models?: ModelComparison[];
  confusion_matrix: {
    labels: string[];
    matrix: number[][];
  };
  feature_importances: Record<string, number>;
  human_rules: {
    feature: string;
    importance_pct: number;
    insight: string;
  }[];
  raw_tree_rules: string;
}

export interface ClusterProfile {
  cluster_id: number;
  cluster_name: string;
  sample_count: number;
  percentage: number;
  description: string;
  color: string;
  feature_averages: Record<string, number>;
}

export interface ScatterPoint {
  id: number;
  name: string;
  cluster: number;
  cluster_name: string;
  x: number;
  y: number;
  raw_values: Record<string, number>;
}

export interface ClusteringModelComparison {
  name: string;
  type: string;
  silhouette_score: number;
  clusters: number;
  status: string;
}

export interface ClusteringResult {
  model_name: string;
  supporting_models?: ClusteringModelComparison[];
  k_clusters: number;
  silhouette_score: number;
  features_used: string[];
  cluster_profiles: ClusterProfile[];
  current_item_cluster: {
    cluster_id: number;
    cluster_name: string;
    description: string;
  };
  scatter_points: ScatterPoint[];
  pca_variance_ratio: number[];
}

export interface PotentialComponent {
  column_name: string;
  current_value: number;
  weight_pct: number;
  component_score: number;
}

export interface PotentialData {
  potential_score: number;
  potential_level: "LOW" | "MEDIUM" | "HIGH";
  potential_level_vi: string;
  badge_color: string;
  components: Record<string, PotentialComponent>;
  formula_explanation: string;
}

export interface StrategyRoadmap {
  market_overview: string;
  trend_summary: string;
  potential_score_display: string;
  model_confidence?: string;
  opportunities: string[];
  risks: string[];
  target_segment: string;
  product_strategy: string;
  pricing_strategy: string;
  marketing_strategy: string;
  distribution_strategy?: string;
  recommended_action: string;
}

export interface WebSourceItem {
  title: string;
  url: string;
  excerpt: string;
  provider: string;
  identity_match?: boolean;
  verified?: boolean;
  credibility_score?: number;
  credibility_tier?: string;
  is_reputable?: boolean;
  domain?: string;
  match_status?: 'exact' | 'variant' | string;
}

export interface MarketAnalysisSynthesis {
  query: string;
  detected_category: string;
  detected_category_vi: string;
  recommended_dataset: string;
  matched_keyword: string;
  executive_summary: string;
  market_signals: {
    signal_score: number;
    signal_label: string;
    total_sources: number;
    reputable_sources_count?: number;
    avg_credibility_score?: number;
    news_count: number;
    web_count: number;
    knowledge_count: number;
    academic_count?: number;
    positive_signals: string[];
    risk_signals: string[];
    extracted_figures: string[];
    highlights: string[];
  };
  benchmark_metrics: {
    category: string;
    category_vi: string;
    dataset_filename: string;
    dataset_title: string;
    source_citation: string;
    potential_score: number;
    potential_level_vi: string;
    avg_growth_pct: number;
    avg_rating: number;
    total_records: number;
    price_stats: { avg: number; min: number; max: number; currency: string } | null;
    top_competitors: string[];
  };
  strategic_takeaways: string[];
}

export interface AnalysisPayload {
  session_id: string;
  product_name: string;
  category: string;
  description?: string;
  dataset_name: string;
  data_validation: DataValidation;
  data_context?: {
    target_column: string; indicator_label: string | null; indicator_code: string | null;
    unit: string | null; unit_status: 'known' | 'unknown' | 'mixed';
    source_urls: string[]; observed_entities: string[]; analyzed_rows: number;
  };
  quality_score: number;
  potential_score: number;
  potential_level: "LOW" | "MEDIUM" | "HIGH";
  potential_level_vi: string;
  badge_color: string;
  potential_breakdown: PotentialData;
  regression: RegressionResult;
  trend_direction: "Increasing" | "Decreasing";
  projected_growth_pct: number;
  regression_metrics: {
    mae: number;
    rmse: number;
    r2_score: number;
  };
  classification: ClassificationResult;
  classification_metrics: ModelComparison[];
  clustering: ClusteringResult;
  clustering_info: {
    cluster_id: number;
    cluster_name: string;
    description: string;
  };
  strategy_recommendation: StrategyRoadmap;
  supporting_models_summary?: {
    total_models_executed: number;
    ai_model_active: string;
    ai_configured: boolean;
    google_models_integrated?: string[];
    regression_models_count?: number;
    classification_models_count?: number;
    clustering_models_count?: number;
    regression_models: RegressionModelComparison[];
    classification_models: ModelComparison[];
    clustering_models: ClusteringModelComparison[];
    ai_models: { name: string; model_id?: string; category: string; status: string }[];
    web_synthesis_meta?: {
      is_web_grounded?: boolean;
      dataset_label?: string;
      reputable_sources_count?: number;
      total_web_sources?: number;
      avg_credibility_score?: number;
      data_quality_score?: number;
      synthesized_metrics?: {
        base_demand?: number;
        annual_growth_pct?: number;
        rating?: number;
        competition_index?: number;
        web_authority_score?: number;
      };
    } | null;
  };
  benchmark_dataset?: string;
  web_research?: {
    query: string;
    search_query: string;
    checked_at: string;
    sources: WebSourceItem[];
    market_analysis?: MarketAnalysisSynthesis;
  } | null;
  evidence_scope?: {
    matched_item?: boolean;
    rows?: number;
    source_verified?: boolean;
    analysis_mode?: string;
    scope_label?: string;
    observed_entities?: string[];
    dataset_rows?: number;
    web_sources_count?: number;
    reputable_sources_count?: number;
    avg_credibility_score?: number;
    benchmark_dataset?: string;
    ai_model_used?: string;
    total_models_count?: number;
  };
  disclaimer: string;
  created_at?: string;
}

export interface DashboardSummary {
  total_sessions: number;
  avg_market_potential: number;
  total_datasets: number;
  total_categories: number;
  recent_sessions: {
    session_id: string;
    product_name: string;
    category: string;
    potential_score: number;
    potential_level: string;
    trend_direction: string;
    created_at: string;
  }[];
}
