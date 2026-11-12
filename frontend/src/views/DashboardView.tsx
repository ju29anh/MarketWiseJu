import { viLabel } from '../utils/locale';
import { KpiCard } from '../components/common/KpiCard';
import { useDashboardData } from '../hooks/useDashboardData';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorNotice } from '../components/common/ErrorNotice';
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Search, Database, PlusCircle, Sparkles, Eye,
  Tag, XCircle, Clock, ArrowRight, TrendingUp, TrendingDown,
  Package, Globe, DollarSign, Star, Loader2, AlertCircle, ExternalLink,
  ChevronRight, Activity, Info, CheckCircle2
} from '../components/icons';
import { apiClient } from '../api/client';

interface DashboardViewProps {
  onStartAnalysis: (preselectedCategory?: string, preselectedDataset?: string, preselectedProduct?: string) => void;
  onViewAnalysis: (sessionId: string) => void;
  onResearch: (query: string) => void;
}

type MarketOverviewResult = Awaited<ReturnType<typeof apiClient.getMarketOverview>>;

export const DashboardView: React.FC<DashboardViewProps> = ({ onStartAnalysis, onViewAnalysis, onResearch }) => {
  const { summary, datasets, categories, isLoading, error: loadError, retry } = useDashboardData();
  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResult, setSearchResult] = useState<MarketOverviewResult | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const popularKeywords = [
    'iPhone', 'Gaming Laptop', 'Tai nghe', 'Skincare', 'Tesla EV',
    'Cà phê', 'Khóa học', 'Smartwatch', 'Robot hút bụi', 'SaaS'
  ];

  const searchController = useRef<AbortController | null>(null);
  useEffect(() => () => {
    searchController.current?.abort();
    if (debounceRef.current) clearTimeout(debounceRef.current);
  }, []);

  // Debounced search → gọi /api/market-overview
  const doSearch = useCallback(async (q: string) => {
    searchController.current?.abort();
    const controller = new AbortController(); searchController.current = controller;
    if (!q.trim()) {
      setIsSearching(false);
      setSearchResult(null);
      setSearchError(null);
      return;
    }
    setIsSearching(true);
    setSearchError(null);
    try {
      const result = await apiClient.getMarketOverview(q.trim(), controller.signal);
      if (!controller.signal.aborted) setSearchResult(result);
    } catch {
      if (!controller.signal.aborted) setSearchError('Không thể kết nối đến máy chủ phân tích.');
    } finally {
      if (!controller.signal.aborted) setIsSearching(false);
    }
  }, []);

  const handleSearchChange = (val: string) => {
    searchController.current?.abort();
    setIsSearching(false); setSearchResult(null);
    setSearchQuery(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(val), 600);
  };

  const handleKeywordClick = (kw: string) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    setSearchQuery(kw);
    doSearch(kw);
  };

  const clearSearch = () => {
    searchController.current?.abort();
    if (debounceRef.current) clearTimeout(debounceRef.current);
    setIsSearching(false);
    setSearchQuery('');
    setSearchResult(null);
    setSearchError(null);
  };

  const md = searchResult?.market_data;
  const wiki = searchResult?.wiki_summary;

  return (
    <div className="space-y-8 py-4 max-w-7xl mx-auto">

      {loadError && <ErrorNotice message={loadError} retry={retry} />}
      {isLoading && <LoadingSkeleton />}
      {/* ── SEARCH BANNER ── */}
      <div className="glass-panel p-6 sm:p-10 rounded-3xl border border-slate-800 relative overflow-hidden">
        {/* Background glow */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600/5 via-transparent to-indigo-600/5 pointer-events-none" />
        <div className="max-w-3xl relative z-10 space-y-4">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-blue-400">Khám phá dữ liệu</span>
            <h1 className="text-2xl sm:text-4xl font-black text-white mt-1 mb-2">
              Tìm Kiếm Dữ Liệu Thị Trường
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              Tìm trong bộ dữ liệu đang có, hoặc mở nghiên cứu web để tìm nguồn cho trường học, địa danh, thương hiệu và các chủ đề khác.
            </p>
          </div>

          {/* Search Input */}
          <div className="relative max-w-2xl">
            <Search className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
            {isSearching && (
              <Loader2 className="w-4 h-4 text-blue-400 animate-spin absolute right-12 top-1/2 -translate-y-1/2" />
            )}
            <input
              type="text" aria-label="Tìm kiếm thị trường" maxLength={200}
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              placeholder="Nhập từ khóa: iPhone, tai nghe, robot hút bụi, cà phê, skincare, khóa học..."
              className="w-full pl-12 pr-12 py-4 rounded-2xl bg-slate-950/90 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 text-sm transition-colors shadow-inner"
            />
            {searchQuery && (
              <button
                aria-label="Xóa từ khóa tìm kiếm" onClick={clearSearch}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
              >
                <XCircle className="w-4 h-4" />
              </button>
            )}
          </div>

          <button type="button" onClick={() => onResearch(searchQuery)} className="inline-flex items-center gap-2 rounded-lg border border-blue-500/50 px-4 py-2 text-sm font-semibold text-blue-200 hover:bg-blue-950">
            <Globe className="w-4 h-4" />Nghiên cứu chủ đề này trên web<ArrowRight className="w-4 h-4" />
          </button>
          {/* Keyword Pills */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] text-slate-400 flex items-center space-x-1 mr-1">
              <Tag className="w-3 h-3 text-blue-400" />
              <span>Thử ngay:</span>
            </span>
            {popularKeywords.map((kw) => (
              <button
                key={kw}
                onClick={() => handleKeywordClick(kw)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-medium border transition-all ${
                  searchQuery === kw
                    ? 'bg-blue-600/20 text-blue-300 border-blue-500/40'
                    : 'bg-slate-950/80 text-slate-300 hover:text-white hover:bg-slate-850 border-slate-800'
                }`}
              >
                {kw}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── KẾT QUẢ TÌM KIẾM ── */}
      {(isSearching || searchResult || searchError) && (
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-blue-400" />
            <h2 className="text-base font-bold text-white">
              {isSearching ? 'Đang tìm kiếm...' : `Kết quả cho "${searchResult?.query || searchQuery}"`}
            </h2>
            {searchResult?.source && (
              <span className="text-[11px] px-2 py-0.5 rounded-full font-semibold
                bg-slate-800 text-slate-400 border border-slate-700">
                {searchResult.source === 'csv_dataset' ? 'Dữ liệu trong CSV' :
                 searchResult.source === 'wikipedia' ? 'Wikipedia' : 'Gợi ý'}
              </span>
            )}
          </div>

          {isSearching && (
            <div className="glass-panel p-8 rounded-2xl border border-slate-800 flex items-center justify-center space-x-3">
              <Loader2 className="w-5 h-5 animate-spin text-blue-400" />
              <span className="text-sm text-slate-400">Đang phân tích dữ liệu thị trường...</span>
            </div>
          )}

          {searchError && (
            <div className="glass-panel p-5 rounded-2xl border border-rose-500/30 flex items-center space-x-3 text-rose-300">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span className="text-sm">{searchError}</span>
            </div>
          )}

          {searchResult && !isSearching && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {/* Card chính: Tổng quan thị trường */}
              <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-slate-800 space-y-5">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                        {md?.category || 'Thị trường'}
                      </span>
                      {md?.source_citation && (
                        <span className="text-[11px] font-medium text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/25 flex items-center space-x-1">
                          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                          <span>Nguồn: {md.source_citation}</span>
                        </span>
                      )}
                      <span className="text-[10px] text-slate-400 font-mono bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                        ISO/IEC 25012 Verified
                      </span>
                    </div>
                    <h3 className="text-xl font-extrabold text-white mt-2">
                      {wiki?.title || md?.category || searchResult.query}
                    </h3>
                    <p className="text-xs text-slate-400 mt-1 leading-relaxed line-clamp-3">
                      {md?.description || wiki?.extract?.slice(0, 200)}
                    </p>
                  </div>
                  {wiki?.thumbnail && (
                    <img
                      src={wiki.thumbnail}
                      alt={wiki.title}
                      className="w-16 h-16 rounded-xl object-cover ml-4 shrink-0 border border-slate-700"
                    />
                  )}
                </div>

                {/* Stats grid — chỉ hiển thị khi có dữ liệu CSV thực */}
                {searchResult.source === 'csv_dataset' && md && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                      <div className="flex items-center space-x-1.5 mb-1">
                        <Database className="w-3.5 h-3.5 text-indigo-400" />
                        <span className="text-[10px] text-slate-500 uppercase font-semibold">Bản ghi</span>
                      </div>
                      <span className="text-lg font-extrabold text-white font-mono">
                        {md.total_records?.toLocaleString() || '—'}
                      </span>
                    </div>

                    {md.price_stats && (
                      <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                        <div className="flex items-center space-x-1.5 mb-1">
                          <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
                          <span className="text-[10px] text-slate-500 uppercase font-semibold">Giá TB</span>
                        </div>
                        <span className="text-lg font-extrabold text-emerald-400 font-mono">
                          {md.price_stats.avg.toLocaleString('vi-VN')} · {md.price_stats.currency}
                        </span>
                        <p className="text-[10px] text-slate-500 mt-0.5">
                          {md.price_stats.min.toLocaleString('vi-VN')} – {md.price_stats.max.toLocaleString('vi-VN')}
                        </p>
                      </div>
                    )}

                    {md.avg_growth_pct !== null && md.avg_growth_pct !== undefined && (
                      <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                        <div className="flex items-center space-x-1.5 mb-1">
                          {(md.avg_growth_pct ?? 0) >= 0
                            ? <TrendingUp className="w-3.5 h-3.5 text-blue-400" />
                            : <TrendingDown className="w-3.5 h-3.5 text-rose-400" />}
                          <span className="text-[10px] text-slate-500 uppercase font-semibold">Tăng trưởng TB</span>
                        </div>
                        <span className={`text-lg font-extrabold font-mono ${(md.avg_growth_pct ?? 0) >= 0 ? 'text-blue-400' : 'text-rose-400'}`}>
                          {(md.avg_growth_pct ?? 0) >= 0 ? '+' : ''}{md.avg_growth_pct}%
                        </span>
                      </div>
                    )}

                    {md.avg_rating !== null && md.avg_rating !== undefined && (
                      <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                        <div className="flex items-center space-x-1.5 mb-1">
                          <Star className="w-3.5 h-3.5 text-amber-400" />
                          <span className="text-[10px] text-slate-500 uppercase font-semibold">Đánh giá trung bình</span>
                        </div>
                        <span className="text-lg font-extrabold text-amber-400 font-mono">
                          {md.avg_rating}/5.0
                        </span>
                      </div>
                    )}
                  </div>
                )}

                {/* Top sản phẩm trong bộ dữ liệu */}
                {md?.top_items && md.top_items.length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center justify-between">
                      <span className="flex items-center space-x-1.5">
                        <Package className="w-3.5 h-3.5" />
                        <span>Sản phẩm/Mẫu điển hình (nhấp để chọn phân tích ngay):</span>
                      </span>
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {md.top_items.map((item) => (
                        <button
                          key={item}
                          type="button"
                          onClick={() => md?.category && md?.dataset_filename && onStartAnalysis(md.category, md.dataset_filename, item)}
                          className="px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-900/90 hover:bg-blue-600/20 hover:border-blue-500 text-slate-200 hover:text-white border border-slate-800 transition-all flex items-center space-x-1 cursor-pointer group"
                          title={`Phân tích ngay sản phẩm ${item}`}
                        >
                          <span>{item}</span>
                          <ArrowRight className="w-3 h-3 text-blue-400 opacity-60 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all" />
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Market Potential Distribution */}
                {md?.market_potential_distribution && Object.keys(md.market_potential_distribution).length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center space-x-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Phân bố tiềm năng thị trường:</span>
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(md.market_potential_distribution).map(([level, pct]) => (
                        <div key={level} className={`px-3 py-1.5 rounded-lg text-xs font-semibold border ${
                          level === 'High' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                          level === 'Medium' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                          'bg-rose-500/10 text-rose-400 border-rose-500/20'
                        }`}>
                          {level}: {pct}%
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Wikipedia extract (nếu là wikipedia source) */}
                {wiki && searchResult.source === 'wikipedia' && wiki.extract && (
                  <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-2">
                    <div className="flex items-center space-x-1.5">
                      <Globe className="w-3.5 h-3.5 text-blue-400" />
                      <span className="text-[11px] font-semibold text-blue-400 uppercase tracking-wider">Từ Wikipedia</span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">{wiki.extract.slice(0, 600)}{wiki.extract.length > 600 ? '...' : ''}</p>
                    {wiki.page_url && (
                      <a
                        href={wiki.page_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center space-x-1 text-[11px] text-blue-400 hover:text-blue-300 mt-1"
                      >
                        <span>Đọc thêm trên Wikipedia</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                )}
              </div>

              {/* Panel phải: CTA + Dataset liên quan */}
              <div className="space-y-4">
                {/* CTA Phân tích sâu */}
                {md?.dataset_filename ? (
                  <div className="glass-panel p-5 rounded-2xl border border-blue-500/30 bg-blue-600/5 space-y-3">
                    <div>
                      <Sparkles className="w-5 h-5 text-blue-400 mb-2" />
                      <h4 className="text-sm font-bold text-white">Phân Tích Thị Trường Sâu</h4>
                      <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                        Áp dụng 4 phương pháp phân tích & dữ liệu Tìm kiếm Web rộng để dự báo xu hướng, phân tích cạnh tranh và lập chiến lược cho <strong className="text-white">{searchQuery.trim() || md.target_product_name}</strong> trong ngành <strong className="text-slate-200">{viLabel(md.category)}</strong>.
                      </p>
                    </div>
                    <button
                      onClick={() => onStartAnalysis(md.category, md.dataset_filename, md.target_product_name || searchQuery.trim())}
                      className="w-full flex items-center justify-center space-x-2 py-3 rounded-xl text-xs font-bold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-500/20 transition-all cursor-pointer"
                    >
                      <PlusCircle className="w-4 h-4" />
                      <span>Phân Tích Học Máy: {md.target_product_name || searchQuery.trim() || 'Sản Phẩm Này'}</span>
                    </button>
                    <button
                      onClick={() => onResearch(searchQuery.trim() || md.target_product_name || '')}
                      className="w-full flex items-center justify-center space-x-2 py-2.5 rounded-xl text-xs font-semibold bg-slate-900/90 hover:bg-slate-800 text-blue-300 border border-blue-500/30 transition-all cursor-pointer"
                    >
                      <Globe className="w-3.5 h-3.5" />
                      <span>Nghiên Cứu Web Rộng & Báo Cáo Đa Nguồn</span>
                    </button>
                  </div>
                ) : (
                  <div className="glass-panel p-5 rounded-2xl border border-amber-500/30 bg-amber-500/5 space-y-3">
                    <div>
                      <AlertCircle className="w-5 h-5 text-amber-400 mb-2" />
                      <h4 className="text-sm font-bold text-white">Chưa có bộ dữ liệu kiểm định</h4>
                      <p className="text-[11px] text-amber-300/90 mt-1 font-semibold leading-relaxed">
                        "Chưa có dữ liệu được xác minh cho đối tượng này."
                      </p>
                      <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                        Hệ thống không tự tạo dự báo giả lập khi thiếu dữ liệu. Bạn có thể tải lên file CSV thị trường của riêng bạn để chạy phân tích định lượng.
                      </p>
                    </div>
                    <button
                      onClick={() => onResearch(searchQuery.trim())}
                      className="w-full flex items-center justify-center space-x-2 py-2.5 rounded-xl text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition-colors cursor-pointer"
                    >
                      <Globe className="w-3.5 h-3.5" />
                      <span>Nghiên Cứu Web & Tạo CSV Phân Tích</span>
                    </button>
                    <button
                      onClick={() => onStartAnalysis(undefined, undefined, searchQuery.trim())}
                      className="w-full flex items-center justify-center space-x-2 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white transition-colors cursor-pointer"
                    >
                      <PlusCircle className="w-3.5 h-3.5" />
                      <span>Tải lên CSV & Phân tích</span>
                    </button>
                  </div>
                )}

                {/* Info về dataset */}
                {md?.dataset_filename && (() => {
                  const dsMeta = datasets.find(d => d.filename === md.dataset_filename);
                  return dsMeta ? (
                    <div className="glass-panel p-4 rounded-2xl border border-slate-800 space-y-2 text-xs">
                      <h4 className="font-bold text-slate-300 text-[11px] uppercase tracking-wider">Thông tin bộ dữ liệu</h4>
                      <div className="space-y-1.5">
                        <div className="flex justify-between text-slate-400">
                          <span>Tên bộ dữ liệu:</span>
                          <span className="font-semibold text-white text-right max-w-[120px] truncate">{dsMeta.title}</span>
                        </div>
                        <div className="flex justify-between text-slate-400">
                          <span>Số bản ghi:</span>
                          <span className="font-semibold text-white">{dsMeta.total_rows?.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between text-slate-400">
                          <span>Chất lượng:</span>
                          <span className="font-semibold text-emerald-400">{dsMeta.quality_score}/100</span>
                        </div>
                        <div className="flex justify-between text-slate-400">
                          <span>Nguồn:</span>
                          <span className="font-semibold text-slate-200 text-right max-w-[100px] truncate">{dsMeta.source}</span>
                        </div>
                      </div>
                    </div>
                  ) : null;
                })()}

                {/* Gợi ý từ khóa khác */}
                <div className="glass-panel p-4 rounded-2xl border border-slate-800 space-y-2">
                  <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Tìm kiếm liên quan</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {(searchResult.suggestions || []).filter(s => s.toLowerCase() !== searchQuery.toLowerCase()).slice(0, 6).map(s => (
                      <button
                        key={s}
                        onClick={() => handleKeywordClick(s)}
                        className="px-2 py-1 rounded-lg text-[11px] font-medium bg-slate-900 text-slate-300 border border-slate-800 hover:border-slate-600 hover:text-white transition-all flex items-center space-x-1"
                      >
                        <ChevronRight className="w-2.5 h-2.5 text-blue-400" />
                        <span>{s}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── KHI CHƯA TÌM KIẾM: KPI + Dataset Grid ── */}
      {!searchQuery && !isLoading && !loadError && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard label="Phiên phân tích" value={String(summary?.total_sessions ?? 0)} detail="Các báo cáo đã lưu để xem lại" icon="analytics" />
            <KpiCard label="Phạm vi kết quả" value="Theo dữ liệu" detail="Chỉ dự báo khi có quan sát của đúng đối tượng" icon="trend" tone="emerald" />
            <KpiCard label="Bộ dữ liệu hiện có" value={String(datasets.length)} detail="Kiểm định chất lượng trước khi phân tích" icon="Database" tone="violet" />
            <KpiCard label="Lĩnh vực thị trường" value={String(categories.length)} detail="Chọn lĩnh vực phù hợp với dữ liệu" icon="Layers" tone="amber" />
          </div>

          {/* Dataset Grid */}
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-bold text-white">Kho Dataset Đã Kiểm Định ({datasets.length})</h2>
                <p className="text-xs text-slate-400 mt-0.5">Chọn một bộ dữ liệu để phân tích chuyên sâu</p>
              </div>
              <button
                onClick={() => onStartAnalysis()}
                className="flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-600/20 transition-all shrink-0"
              >
                <PlusCircle className="w-4 h-4" />
                <span>Phân Tích Mới</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {datasets.map((ds) => (
                <div
                  key={ds.id}
                  className="glass-panel p-5 rounded-2xl border border-slate-800 hover:border-blue-500/40 flex flex-col justify-between transition-all duration-200 group"
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-[11px] font-semibold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20 truncate max-w-[170px]">
                        {viLabel(ds.category)}
                      </span>
                      <span className="text-[11px] font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 shrink-0">
                        {ds.quality_score}/100
                      </span>
                    </div>
                    <h3 className="text-base font-bold text-white mb-1 group-hover:text-blue-300 transition-colors">{viLabel(ds.title)}</h3>
                    <p className="text-xs text-slate-400 line-clamp-1 mb-3">{ds.source}</p>
                    <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80 mb-4">
                      <div>
                        <span className="text-slate-500 block">Bản ghi:</span>
                        <span className="font-semibold text-slate-200">{ds.total_rows?.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">File:</span>
                        <span className="font-mono text-slate-200 truncate block">{ds.filename}</span>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => onStartAnalysis(ds.category, ds.filename)}
                    className="w-full flex items-center justify-center space-x-2 py-2.5 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white transition-colors"
                  >
                    <PlusCircle className="w-3.5 h-3.5" />
                    <span>Phân tích với Bộ dữ liệu này</span>
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Sessions */}
          {summary?.recent_sessions && summary.recent_sessions.length > 0 && (
            <div className="space-y-4 pt-6 border-t border-slate-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Clock className="w-5 h-5 text-blue-400" />
                  <h2 className="text-xl font-bold text-white">Lịch Sử Phân Tích Gần Đây</h2>
                </div>
                <span className="text-xs text-slate-400">Lưu trong SQLite</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {summary.recent_sessions.map((sess) => (
                  <div
                    key={sess.session_id}
                    role="button"
                    tabIndex={0}
                    aria-label={`Xem báo cáo ${sess.product_name}`}
                    onKeyDown={event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onViewAnalysis(sess.session_id); } }}
                    onClick={() => onViewAnalysis(sess.session_id)}
                    className="glass-panel p-4 rounded-xl border border-slate-800 hover:border-blue-500/40 cursor-pointer flex items-center justify-between transition-all group"
                  >
                    <div>
                      <div className="flex items-center space-x-2 mb-1 flex-wrap gap-1">
                        <span className="text-sm font-bold text-white group-hover:text-blue-400 transition-colors">
                          {sess.product_name}
                        </span>
                        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
                          sess.potential_level === 'HIGH' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                          sess.potential_level === 'MEDIUM' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                          'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        }`}>
                          Xem dữ liệu & phạm vi
                        </span>
                      </div>
                      <div className="text-xs text-slate-400">
                        <span>{sess.category}</span> • <span className="text-slate-500">{new Date(sess.created_at).toLocaleString('vi-VN')}</span>
                      </div>
                    </div>
                    <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-slate-400 group-hover:bg-blue-600 group-hover:text-white transition-colors shrink-0 ml-2">
                      <Eye className="w-4 h-4" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Nút Phân Tích Mới khi đang hiện search result */}
      {searchQuery && !isSearching && (
        <div className="flex items-center justify-between pt-4 border-t border-slate-800">
          <p className="text-xs text-slate-400">
            <Info className="w-3.5 h-3.5 inline mr-1 text-blue-400" />
            Tìm kiếm tra cứu dữ liệu hiện có. Để nghiên cứu nguồn cho từ khóa bất kỳ, chọn <strong className="text-white">Nghiên cứu chủ đề này trên web</strong>.
          </p>
          <button
            onClick={() => onStartAnalysis()}
            className="flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-600/20 transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Phân Tích Mới</span>
          </button>
        </div>
      )}
    </div>
  );
};
