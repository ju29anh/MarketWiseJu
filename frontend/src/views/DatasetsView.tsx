import { viLabel } from '../utils/locale';
import { DatasetUpload } from '../components/common/DatasetUpload';
import { ErrorNotice } from '../components/common/ErrorNotice';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { errorMessage } from '../utils/errors';
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Upload,
  PlusCircle,
  Loader2
} from '../components/icons';
import { DatasetMeta, DataValidation } from '../types';
import { apiClient } from '../api/client';

interface DatasetsViewProps {
  onStartAnalysisWithDataset: (category: string, datasetFilename: string) => void;
}

export const DatasetsView: React.FC<DatasetsViewProps> = ({ onStartAnalysisWithDataset }) => {
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [revision, setRevision] = useState(0);
  const inspectController = useRef<AbortController | null>(null);
  const uploadController = useRef<AbortController | null>(null);
  useEffect(() => () => { inspectController.current?.abort(); uploadController.current?.abort(); }, []);
  const [datasets, setDatasets] = useState<DatasetMeta[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<DatasetMeta | null>(null);
  const [validation, setValidation] = useState<DataValidation | null>(null);
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);

  // Upload custom dataset state
  const [customFile, setCustomFile] = useState<File | null>(null);
  const [customCategory, setCustomCategory] = useState('Custom Category');
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);

  const inspectDataset = useCallback(async (filename: string) => {
    inspectController.current?.abort();
    const controller = new AbortController(); inspectController.current = controller;
    setValidation(null); setError(null);
    setValidating(true);
    try {
      const val = await apiClient.validateDataset(filename, controller.signal);
      if (!controller.signal.aborted) setValidation(val);
    } catch (err) {
      if (!controller.signal.aborted) setError(errorMessage(err));
    } finally {
      if (!controller.signal.aborted) setValidating(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    async function loadData() {
      try {
        const list = await apiClient.getDatasets(controller.signal);
        if (controller.signal.aborted) return;
        setDatasets(list);
        if (list.length > 0) {
          setSelectedDataset(list[0]);
          void inspectDataset(list[0].filename);
        }
      } catch (err) {
        if (!controller.signal.aborted) setError(errorMessage(err));
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    loadData();
    return () => controller.abort();
  }, [revision, inspectDataset]);

  const handleSelectDataset = (ds: DatasetMeta) => {
    setSelectedDataset(ds);
    void inspectDataset(ds.filename);
  };

  const handleUploadCustom = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customFile) return;
    uploadController.current?.abort();
    const controller = new AbortController(); uploadController.current = controller;
    setProgress(0); setError(null);
    setUploading(true);
    setUploadMessage(null);
    try {
      const res = await apiClient.uploadDataset(customFile, customCategory, setProgress, controller.signal);
      if (controller.signal.aborted) return;
      setUploadMessage(`Đã tải lên và kiểm định thành công! Quality Score: ${res.validation.quality_score}/100`);
      const updatedList = await apiClient.getDatasets(controller.signal);
      if (controller.signal.aborted) return;
      setDatasets(updatedList);
      const newDs = updatedList.find(d => d.filename === res.filename) || updatedList[0];
      setSelectedDataset(newDs);
      setValidation(res.validation);
      setCustomFile(null);
    } catch (err) {
      if (!controller.signal.aborted) setError(errorMessage(err));
    } finally {
      if (!controller.signal.aborted) setUploading(false);
    }
  };

  return (
    <div className="space-y-10 py-4 max-w-7xl mx-auto">
      {error && <ErrorNotice message={error} retry={() => { setLoading(true); setError(null); setRevision(v => v + 1); }} />}
      {loading && <LoadingSkeleton />}
      {/* Header */}
      <div className="glass-panel p-8 rounded-3xl border border-slate-800">
        <div className="max-w-3xl">
          <span className="text-xs font-bold uppercase tracking-wider text-blue-400">Trung tâm kiểm định dữ liệu</span>
          <h1 className="text-3xl font-extrabold text-white mt-1 mb-2">Kho Dữ Liệu & Trung Tâm Kiểm Định Chất Lượng</h1>
          <p className="text-sm text-slate-300 leading-relaxed">
            Xem xét chi tiết từng bộ dữ liệu thị trường, kiểm tra ma trận tương quan, phát hiện ngoại lai (Outliers) và xác thực tính toàn vẹn trước khi phân tích.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Datasets List & Upload form */}
        <div className="space-y-6">
          <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Danh sách bộ dữ liệu</h3>
            <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">
              {datasets.map((ds) => {
                const isSelected = selectedDataset?.id === ds.id;
                return (
                  <div
                    key={ds.id}
                    role="button" tabIndex={0} onKeyDown={event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); handleSelectDataset(ds); } }}
                    onClick={() => handleSelectDataset(ds)}
                    className={`p-3 rounded-xl border cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-blue-600/20 border-blue-500 text-white shadow-md'
                        : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-bold truncate">{viLabel(ds.title)}</span>
                      <span className="text-emerald-400 font-mono font-semibold">{ds.quality_score}/100</span>
                    </div>
                    <div className="text-[11px] text-slate-400 flex items-center justify-between">
                      <span>{viLabel(ds.category)}</span>
                      <span className="font-mono">{ds.total_rows} dòng</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Upload Custom CSV Form */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
              <Upload className="w-4 h-4 text-blue-400" />
              <span>Tải lên bộ dữ liệu CSV / XLSX</span>
            </h3>

            <form onSubmit={handleUploadCustom} className="space-y-3">
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Ngành hàng / Lĩnh vực:</label>
                <input
                  type="text" aria-label="Ngành của bộ dữ liệu" maxLength={120}
                  value={customCategory}
                  onChange={(e) => setCustomCategory(e.target.value)}
                  placeholder="Ví dụ: E-commerce, Gaming, EdTech..."
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white text-xs"
                />
              </div>

              <DatasetUpload key={uploadMessage || 'upload'} file={customFile} onChange={setCustomFile} disabled={uploading} />
              {uploading && <div role="status" className="text-xs text-blue-200">
                <p>{progress < 100 ? `Đang tải file: ${progress}%` : 'Đang kiểm định dữ liệu…'}</p>
                <progress value={progress} max={100} aria-label="Tiến trình tải bộ dữ liệu" className="w-full accent-blue-500" />
              </div>}

              <button
                type="submit"
                disabled={!customFile || uploading}
                className="w-full py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white transition-colors disabled:opacity-50"
              >
                {uploading ? 'Đang kiểm định và tải lên...' : 'Tải Lên & Kiểm Định'}
              </button>

              {uploadMessage && (
                <p role="status" className="text-[11px] text-slate-300 bg-slate-950 p-2 rounded border border-slate-800">
                  {uploadMessage}
                </p>
              )}
            </form>
          </div>
        </div>

        {/* Right: Validation & Summary Statistics View */}
        <div className="lg:col-span-2 space-y-6">
          {selectedDataset && (
            <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
                <div>
                  <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    {viLabel(selectedDataset.category)}
                  </span>
                  <h2 className="text-2xl font-bold text-white mt-2">{viLabel(selectedDataset.title)}</h2>
                  <p className="text-xs text-slate-400 mt-1">Nguồn khai báo: {selectedDataset.source}. Chưa xác minh độc lập; kiểm định độ sạch không chứng minh tính đúng sự thật.</p>
                </div>

                <div className="text-right">
                  <span className="text-xs text-slate-500 block">CHẤT LƯỢNG DỮ LIỆU</span>
                  <span className="text-3xl font-black text-emerald-400 font-mono">
                    {validation?.quality_score || selectedDataset.quality_score}/100
                  </span>
                </div>
              </div>

              {/* Action trigger */}
              <div className="flex justify-end">
                <button
                  onClick={() => onStartAnalysisWithDataset(selectedDataset.category, selectedDataset.filename)}
                  className="flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-600/20 transition-all"
                >
                  <PlusCircle className="w-4 h-4" />
                  <span>Tiến Hành Phân Tích với bộ dữ liệu này</span>
                </button>
              </div>

              {/* Validation Inspection */}
              {validating ? (
                <div className="p-12 text-center text-slate-400 flex flex-col items-center">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-400 mb-2" />
                  <span>Đang phân tích cấu trúc cột và kiểm tra ngoại lai IQR...</span>
                </div>
              ) : validation ? (
                <div className="space-y-6">
                  {/* Quality KPIs */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
                      <span className="text-[10px] text-slate-500 block">Tổng dòng</span>
                      <span className="text-base font-bold text-white font-mono">{validation.total_rows}</span>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
                      <span className="text-[10px] text-slate-500 block">Giá trị thiếu</span>
                      <span className="text-base font-bold text-emerald-400 font-mono">{validation.missing_pct}%</span>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
                      <span className="text-[10px] text-slate-500 block">Trùng lặp</span>
                      <span className="text-base font-bold text-white font-mono">{validation.duplicate_pct}%</span>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
                      <span className="text-[10px] text-slate-500 block">Ngoại lai IQR</span>
                      <span className="text-base font-bold text-amber-400 font-mono">{validation.outlier_pct}%</span>
                    </div>
                  </div>

                  {/* Outlier & Summary Stats Table */}
                  {validation.outlier_details && Object.keys(validation.outlier_details).length > 0 && (
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">Thống Kê Mô Tả & Phát Hiện Ngoại Lai (IQR):</h4>
                      <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Bảng dữ liệu — cuộn ngang để xem thêm">
                        <table className="w-full text-xs text-left border-collapse bg-slate-950/60 rounded-xl border border-slate-800">
                          <thead>
                            <tr className="border-b border-slate-800 text-slate-400 text-[11px]">
                              <th className="py-2.5 px-3">Cột Đặc Trưng</th>
                              <th className="py-2.5 px-3 font-mono">Min</th>
                              <th className="py-2.5 px-3 font-mono">Max</th>
                              <th className="py-2.5 px-3 font-mono">Trung bình</th>
                              <th className="py-2.5 px-3 font-mono">Ngưỡng ngoại lai</th>
                              <th className="py-2.5 px-3 font-mono">Ngoại lai</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800/80">
                            {Object.entries(validation.outlier_details).map(([col, stats]) => (
                              <tr key={col} className="hover:bg-slate-800/20">
                                <td className="py-2 px-3 font-semibold text-slate-200">{col}</td>
                                <td className="py-2 px-3 font-mono text-slate-400">{stats.min}</td>
                                <td className="py-2 px-3 font-mono text-slate-400">{stats.max}</td>
                                <td className="py-2 px-3 font-mono text-slate-300 font-bold">{stats.mean}</td>
                                <td className="py-2 px-3 font-mono text-slate-400">[{stats.lower_bound}, {stats.upper_bound}]</td>
                                <td className="py-2 px-3 font-mono">
                                  {stats.count > 0 ? (
                                    <span className="text-amber-400 font-bold">{stats.count}</span>
                                  ) : (
                                    <span className="text-emerald-400">0</span>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Sample Raw Data Table */}
                  {validation.sample_data && validation.sample_data.length > 0 && (
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">Xem Trước 5 Dòng Dữ Liệu Thực Tế:</h4>
                      <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Bảng dữ liệu — cuộn ngang để xem thêm">
                        <table className="w-full text-[11px] text-left border-collapse bg-slate-950/60 rounded-xl border border-slate-800">
                          <thead>
                            <tr className="border-b border-slate-800 text-slate-400">
                              {Object.keys(validation.sample_data[0]).map((h, i) => (
                                <th key={i} className="py-2 px-2.5 whitespace-nowrap">{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800/80 font-mono text-slate-300">
                            {validation.sample_data.map((row, rIdx) => (
                              <tr key={rIdx} className="hover:bg-slate-800/20">
                                {Object.values(row).map((val, cIdx) => (
                                  <td key={cIdx} className="py-1.5 px-2.5 whitespace-nowrap">{String(val)}</td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
