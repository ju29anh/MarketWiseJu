import { viLabel } from '../utils/locale';
import { useAnalysis } from '../hooks/useAnalysis';
import { DatasetUpload } from '../components/common/DatasetUpload';
import { ErrorNotice } from '../components/common/ErrorNotice';
import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Upload,
  Brain,
  Loader2,
  Search,
  Package
} from '../components/icons';
import { DatasetMeta, Category, DataValidation, AnalysisPayload } from '../types';
import { apiClient } from '../api/client';

interface AnalysisWizardViewProps {
  initialCategory?: string;
  initialDataset?: string;
  initialProductName?: string;
  onCancel: () => void;
  onAnalysisComplete: (payload: AnalysisPayload) => void;
  onResearch?: (query: string) => void;
}

export const AnalysisWizardView: React.FC<AnalysisWizardViewProps> = ({
  initialCategory,
  initialDataset,
  initialProductName,
  onCancel,
  onAnalysisComplete,
  onResearch
}) => {
  // 3 Steps: 1 = Chọn bộ dữ liệu + Sản phẩm, 2 = Kết quả Kiểm Định, 3 = Đang chạy ML
  const [currentStep, setCurrentStep] = useState<number>(1);
  useEffect(() => { window.scrollTo({ top: 0, behavior: 'instant' }); }, [currentStep]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [datasets, setDatasets] = useState<DatasetMeta[]>([]);

  // Step 1 state
  const [selectedCategory, setSelectedCategory] = useState(initialCategory || '');
  const [selectedDataset, setSelectedDataset] = useState(initialDataset || '');
  const [productsInDataset, setProductsInDataset] = useState<string[]>([]);
  const [isLoadingProducts, setIsLoadingProducts] = useState(true);
  const [productSearch, setProductSearch] = useState(initialProductName || '');
  const [selectedProduct, setSelectedProduct] = useState(initialProductName || '');
  const [productDescription, setProductDescription] = useState(
    initialProductName ? `Phân tích tiềm năng thị trường và xây dựng chiến lược tăng trưởng cho ${initialProductName}` : ''
  );
  const [uploadMode, setUploadMode] = useState<'sample' | 'custom'>(initialProductName && !initialDataset ? 'custom' : 'sample');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  // Step 2 state
  const [validation, setValidation] = useState<DataValidation | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Step 3 state
  const { run, job, error: mlError } = useAnalysis();
  const mlStepIndex = job?.step ?? 0;
  const [uploadProgress, setUploadProgress] = useState(0);
  const validationController = useRef<AbortController | null>(null);
  const productsController = useRef<AbortController | null>(null);
  const productSearchRef = useRef(productSearch);
  useEffect(() => { productSearchRef.current = productSearch; }, [productSearch]);
  useEffect(() => () => { validationController.current?.abort(); productsController.current?.abort(); }, []);

  const mlPipelineSteps = [
    'Kiểm định cấu trúc và độ đầy đủ của dữ liệu...',
    'Làm sạch dữ liệu và kiểm tra đúng đối tượng...',
    'Ước lượng xu hướng và sai số dự báo...',
    'Phân loại các quan sát trong dữ liệu...',
    'Tìm nhóm quan sát tương đồng và ngoại lai...',
    'Tổng hợp chỉ tiêu của bộ dữ liệu...',
    'Chuẩn bị báo cáo và giới hạn kết quả...'
  ];

  // Load categories + datasets
  useEffect(() => {
    const controller = new AbortController();
    async function loadMeta() {
      try {
        const [catList, dataList] = await Promise.all([
          apiClient.getCategories(controller.signal),
          apiClient.getDatasets(controller.signal)
        ]);
        if (controller.signal.aborted) return;
        setCategories(catList);
        setDatasets(dataList);
        const initCat = initialCategory || (catList.length > 0 ? catList[0].name : '');
        setSelectedCategory(initCat);
        if (initialDataset) {
          setSelectedDataset(initialDataset);
        } else if (dataList.length > 0) {
          const matching = dataList.find(ds =>
            ds.category.toLowerCase().includes(initCat.toLowerCase()) ||
            initCat.toLowerCase().includes(ds.category.toLowerCase())
          );
          setSelectedDataset((matching || dataList[0]).filename);
        }
      } catch {
        if (controller.signal.aborted) return;
        setValidationError('Không tải được danh mục. Hãy kiểm tra máy chủ rồi tải lại trang.');
      }
    }
    loadMeta();
    return () => controller.abort();
  }, [initialCategory, initialDataset]);

  // Lọc datasets theo category hiện tại
  const datasetsForCategory = useMemo(() => {
    if (!selectedCategory || datasets.length === 0) return datasets;
    const filtered = datasets.filter(ds =>
      ds.category.toLowerCase().includes(selectedCategory.toLowerCase()) ||
      selectedCategory.toLowerCase().includes(ds.category.toLowerCase())
    );
    return filtered.length > 0 ? filtered : datasets;
  }, [selectedCategory, datasets]);

  // Khi đổi dataset (sample mode) → tải sản phẩm
  useEffect(() => {
    if (!selectedDataset || uploadMode !== 'sample') return;
    productsController.current?.abort();
    const controller = new AbortController();
    productsController.current = controller;
    apiClient.getDatasetProducts(selectedDataset, controller.signal)
      .then(res => {
        if (controller.signal.aborted) return;
        const prods = res.products || [];
        setProductsInDataset(prods);
        if (initialProductName) {
          const q = initialProductName.toLowerCase();
          const found = prods.find(p => p.toLowerCase() === q)
            || prods.find(p => p.toLowerCase().includes(q) || q.includes(p.toLowerCase()));
          if (found) {
            setSelectedProduct(found);
            setProductSearch('');
          } else {
            setSelectedProduct(initialProductName);
            setProductSearch(initialProductName);
          }
        } else if (!productSearchRef.current.trim() && prods.length > 0) {
          setSelectedProduct(prev => prev || prods[0]);
        }
      })
      .catch(() => {
        if (controller.signal.aborted) return;
        setProductsInDataset([]);
        if (initialProductName) {
          setSelectedProduct(initialProductName);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoadingProducts(false);
      });
    return () => controller.abort();
  }, [selectedDataset, uploadMode, initialProductName]);

  const getCatLabel = (name: string) =>
    name === 'Education & EdTech' ? 'Giáo dục & đào tạo' : categories.find(c => c.name === name)?.name_vi || name;

  const filteredProducts = productsInDataset.filter(p =>
    p.toLowerCase().includes(productSearch.toLowerCase())
  );

  const productName = selectedProduct.trim() || productSearch.trim();
  const isUploadedDataset = selectedDataset.startsWith('upload_');
  const canProceed = productName.length >= 2 &&
    (uploadMode === 'sample'
      ? !!selectedDataset && (isUploadedDataset || productsInDataset.length === 0 || productsInDataset.some(p => p.toLocaleLowerCase() === productName.toLocaleLowerCase()))
      : !!uploadedFile);

  const selectedDatasetMeta = datasets.find(d => d.filename === selectedDataset);

  // Step 1 → 2: Validate
  const handleValidate = async () => {
    validationController.current?.abort();
    const controller = new AbortController(); validationController.current = controller;
    if (!canProceed) { setValidationError('Hãy chọn bộ dữ liệu và nhập tên sản phẩm trước khi tiếp tục.'); return; }
    setUploadProgress(0);
    setIsValidating(true);
    setValidationError(null);
    try {
      if (uploadMode === 'custom' && uploadedFile) {
        const res = await apiClient.uploadDataset(uploadedFile, selectedCategory, setUploadProgress, controller.signal);
        if (controller.signal.aborted) return;
        setSelectedDataset(res.filename);
        setValidation(res.validation);
      } else {
        const targetDs = selectedDataset;
        const valRes = await apiClient.validateDataset(targetDs, controller.signal);
        if (controller.signal.aborted) return;
        if (!valRes.valid) throw new Error('Dữ liệu chưa đủ để phân tích. Hãy chọn file mẫu hoặc bổ sung các cột số.');
        setValidation(valRes);
      }
      setCurrentStep(2);
    } catch (err) {
      if (controller.signal.aborted) return;
      setValidationError(err instanceof Error ? err.message : 'Lỗi khi kiểm định dữ liệu');
    } finally {
      if (!controller.signal.aborted) setIsValidating(false);
    }
  };

  // Step 2 → 3: Run ML
  const handleExecuteML = async () => {
    setCurrentStep(3);
    const result = await run({ product_name: productName, category: selectedCategory,
      description: productDescription, dataset_name: selectedDataset });
    if (result) onAnalysisComplete(result);
  };

  return (
    <div className="max-w-4xl mx-auto py-6">
      {/* Wizard Header */}
      <div className="flex flex-wrap gap-4 items-center justify-between mb-8">
        <div>
          <button
            onClick={onCancel}
            className="flex items-center space-x-1.5 text-xs text-slate-400 hover:text-white transition-colors mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Quay lại tổng quan</span>
          </button>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Phân tích dữ liệu & lập chiến lược</h1>
        </div>
        <div className="flex items-center space-x-2 text-xs font-semibold">
          {[1, 2, 3].map(step => (
            <div
              key={step}
              className={`w-8 h-8 rounded-full flex items-center justify-center font-mono transition-all ${
                currentStep === step
                  ? 'bg-blue-600 text-white ring-4 ring-blue-600/20'
                  : currentStep > step
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-slate-800 text-slate-500'
              }`}
            >
              {currentStep > step ? <CheckCircle2 className="w-4 h-4" /> : step}
            </div>
          ))}
        </div>
      </div>

      {/* ── STEP 1: Chọn Thị Trường + Dataset + Sản Phẩm ── */}
      {currentStep === 1 && (
        <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 space-y-6 animate-fade-in">
          <div className="border-b border-slate-800 pb-4">
            <h2 className="text-lg font-bold text-white">Bước 1: Chọn Thị Trường & Sản Phẩm Cần Phân Tích</h2>
            <p className="text-xs text-slate-400 mt-1">
              Hệ thống sẽ phân tích xu hướng thị trường và dự báo tiềm năng của sản phẩm bạn chọn dựa trên dữ liệu thực tế.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Cột trái: Chọn ngành + dataset */}
            <div className="space-y-4">
              {/* 1. Chọn ngành */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
                  1. Lĩnh Vực Thị Trường <span className="text-rose-400">*</span>
                </label>
                <select aria-label="Lĩnh vực thị trường"
                  value={selectedCategory}
                  onChange={e => {
                    const nextCat = e.target.value;
                    setSelectedCategory(nextCat);
                    const matching = datasets.find(ds =>
                      ds.category.toLowerCase().includes(nextCat.toLowerCase()) ||
                      nextCat.toLowerCase().includes(ds.category.toLowerCase())
                    );
                    if (matching) {
                      setIsLoadingProducts(true);
                      setProductsInDataset([]);
                      setSelectedDataset(matching.filename);
                    }
                    setSelectedProduct('');
                    setProductSearch('');
                  }}
                  className="w-full px-4 py-3 rounded-xl bg-slate-950/80 border border-slate-700 text-white text-sm focus:outline-none focus:border-blue-500 cursor-pointer"
                >
                  {selectedCategory && !categories.some(cat => cat.name === selectedCategory) && <option value={selectedCategory}>{getCatLabel(selectedCategory)}</option>}
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.name}>{getCatLabel(cat.name)}</option>
                  ))}
                </select>
              </div>

              {/* 2. Chọn bộ dữ liệu */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
                  2. Bộ Dữ Liệu Thị Trường <span className="text-rose-400">*</span>
                </label>
                <div className="space-y-2 max-h-44 overflow-y-auto pr-1">
                  {datasetsForCategory.map(ds => (
                    <div
                      key={ds.id}
                      role="button" tabIndex={0} onKeyDown={event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); event.currentTarget.click(); } }}
                      onClick={() => {
                        setIsLoadingProducts(true);
                        setProductsInDataset([]);
                        setSelectedDataset(ds.filename);
                        setSelectedCategory(ds.category);
                        setSelectedProduct('');
                        setProductSearch('');
                      }}
                      className={`p-3 rounded-xl border cursor-pointer transition-all text-xs ${
                        selectedDataset === ds.filename
                          ? 'bg-blue-600/20 border-blue-500 text-white'
                          : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold truncate">{viLabel(ds.title)}</span>
                        <span className="text-emerald-400 font-mono shrink-0 ml-2">{ds.quality_score}/100</span>
                      </div>
                      <p className="text-slate-400 text-[11px] mt-0.5">{ds.total_rows} bản ghi trong bộ dữ liệu</p>
                    </div>
                  ))}
                </div>

                {/* Upload CSV riêng */}
                <div role="button" tabIndex={0} onKeyDown={event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); event.currentTarget.click(); } }}
                  onClick={() => {
                    const newMode = uploadMode === 'custom' ? 'sample' : 'custom';
                    setUploadMode(newMode);
                    setSelectedProduct('');
                    setProductSearch('');
                  }}
                  className={`mt-2 p-3 rounded-xl border cursor-pointer transition-all text-xs flex items-center space-x-2 ${
                    uploadMode === 'custom'
                      ? 'bg-blue-600/20 border-blue-500 text-white'
                      : 'bg-slate-950/60 border-dashed border-slate-700 text-slate-400 hover:border-slate-600'
                  }`}
                >
                  <Upload className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                  <span className="font-semibold">Hoặc tải lên file CSV / XLSX của bạn (dữ liệu riêng)</span>
                </div>

                {uploadMode === 'custom' && (
                  <DatasetUpload
                    file={uploadedFile}
                    onChange={setUploadedFile}
                    onPreview={(prev) => {
                      if (!selectedProduct.trim() && !productSearch.trim() && prev.rows && prev.rows.length > 0) {
                        const r0 = prev.rows[0];
                        const candidateCol = prev.columns.find(c =>
                          ['research_query', 'product_name', 'item_name', 'entity', 'name', 'title', 'model', 'observed_entity'].some(k => c.toLowerCase().includes(k))
                        );
                        const val = candidateCol ? String(r0[candidateCol] ?? '').trim() : '';
                        if (val && val.length >= 2) {
                          setSelectedProduct(val);
                          setProductSearch(val);
                        }
                      }
                    }}
                    disabled={isValidating}
                  />
                )}
                {isValidating && uploadMode === 'custom' && <div role="status" className="text-xs text-blue-200 space-y-2">
                  <p>{uploadProgress < 100 ? `Đang tải file: ${uploadProgress}%` : 'Đã tải xong, đang kiểm định dữ liệu…'}</p>
                  <progress value={uploadProgress} max={100} aria-label="Tiến trình tải bộ dữ liệu" className="w-full accent-blue-500" />
                </div>}
              </div>
            </div>

            {/* Cột phải: Danh sách sản phẩm thực từ bộ dữ liệu */}
            <div className="space-y-3">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
                3. Chọn Sản Phẩm Cụ Thể Cần Phân Tích <span className="text-rose-400">*</span>
              </label>

              {uploadMode === 'custom' ? (
                <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 text-center">
                  <Upload className="w-6 h-6 mx-auto mb-2 text-slate-500" />
                  <p className="text-xs text-slate-400">Sau khi tải lên dữ liệu, hãy nhập tên sản phẩm vào ô tìm kiếm bên dưới.</p>
                </div>
              ) : isLoadingProducts ? (
                <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-6 flex items-center justify-center space-x-2">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                  <span className="text-xs text-slate-400">Đang tải danh sách sản phẩm từ bộ dữ liệu...</span>
                </div>
              ) : uploadMode === 'sample' && !isLoadingProducts && productsInDataset.length === 0 && selectedDataset ? (
                <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 text-center">
                  <Package className="w-5 h-5 mx-auto mb-2 text-slate-500" />
                  <p className="text-xs text-slate-400">Bộ dữ liệu này không có cột sản phẩm rõ ràng.</p>
                  <p className="text-blue-400 text-[11px] mt-1">Hãy nhập tên sản phẩm trực tiếp vào ô tìm kiếm bên dưới.</p>
                </div>
              ) : null}

              {/* Search + list sản phẩm (hiển thị khi có products hoặc cần nhập tự do) */}
              <div className="space-y-2">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text" aria-label="Tên sản phẩm cần phân tích"
                    value={productSearch}
                    onChange={e => { setProductSearch(e.target.value); setSelectedProduct(''); }}
                    placeholder={
                      uploadMode === 'custom'
                        ? 'Nhập tên sản phẩm cần phân tích...'
                        : productsInDataset.length > 0
                          ? `Tìm trong ${productsInDataset.length} sản phẩm hoặc nhập tên mới...`
                          : 'Nhập tên sản phẩm cần phân tích...'
                    }
                    className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-blue-500"
                  />
                </div>

                {uploadMode === 'sample' && productsInDataset.length > 0 && (
                  <div className="max-h-48 overflow-y-auto space-y-1 pr-1">
                    {filteredProducts.slice(0, 20).map(prod => (
                      <div
                        key={prod}
                        role="button" tabIndex={0} onKeyDown={event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); event.currentTarget.click(); } }}
                        onClick={() => { setSelectedProduct(prod); setProductSearch(''); }}
                        className={`flex items-center space-x-2 p-2.5 rounded-xl border cursor-pointer transition-all text-xs ${
                          selectedProduct === prod
                            ? 'bg-blue-600/20 border-blue-500 text-white'
                            : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-600 hover:bg-slate-900/60'
                        }`}
                      >
                        <Package className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                        <span className="font-medium">{prod}</span>
                        {selectedProduct === prod && (
                          <CheckCircle2 className="w-3.5 h-3.5 text-blue-400 ml-auto shrink-0" />
                        )}
                      </div>
                    ))}
                    {filteredProducts.length === 0 && productSearch && (
                      <div className="p-3.5 text-left text-xs text-slate-300 bg-blue-950/30 border border-blue-500/30 rounded-xl space-y-1.5">
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-bold text-blue-300">Phân tích từ khóa mở rộng: &ldquo;{productSearch.trim()}&rdquo;</span>
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shrink-0">
                            Cần dữ liệu đúng đối tượng
                          </span>
                        </div>
                        <p className="text-slate-400 leading-relaxed">
                          Tên này chưa có trong bộ dữ liệu đã chọn. Hãy tra cứu ở mục Nghiên cứu &amp; So sánh hoặc chọn tải lên CSV / XLSX có quan sát của chính đối tượng. Dữ liệu cùng ngành không thay thế dữ liệu riêng.
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Sản phẩm đã chọn */}
              {productName && (
                <div className="flex items-center space-x-2 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <div className="text-xs">
                    <span className="text-slate-400">Sản phẩm sẽ phân tích: </span>
                    <strong className="text-white">{productName}</strong>
                  </div>
                </div>
              )}

              {/* Mô tả thêm */}
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1.5">
                  Định vị / Mô tả thêm <span className="text-slate-600">(tuỳ chọn)</span>
                </label>
                <textarea aria-label="Mô tả hoặc định vị sản phẩm"
                  rows={2}
                  value={productDescription}
                  onChange={e => setProductDescription(e.target.value)}
                  placeholder="Ví dụ: Nhắm tới phân khúc sinh viên, tập trung tính năng phù hợp khách hàng..."
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-950/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-blue-500 resize-none"
                />
              </div>
            </div>
          </div>

          {/* Summary bar */}
          {uploadMode === 'sample' && selectedDatasetMeta && (
            <div className="flex flex-wrap items-center gap-2 p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs">
              <span className="text-slate-500">Lựa chọn:</span>
              <span className="px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">{getCatLabel(selectedCategory)}</span>
              <span className="px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">{viLabel(selectedDatasetMeta.title)}</span>
              {productName && <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">{productName}</span>}
            </div>
          )}

          {validationError && <ErrorNotice message={validationError} retry={() => void handleValidate()} />}
          {onResearch && productName.trim() && <div className="rounded-2xl border border-blue-500/30 bg-slate-950 p-4 space-y-3">
            <p className="text-sm text-slate-300">Muốn phân tích từ khóa và nhận chiến lược ngay? Hệ thống sẽ thu thập nguồn, tạo hồ sơ dữ liệu riêng và dùng dữ liệu thống kê tham khảo khi chưa có chuỗi riêng của đối tượng.</p>
            <button type="button" className="primary-action px-5 py-3 text-sm" onClick={() => onResearch(productName.trim())}>Phân tích từ khóa & lập kế hoạch</button>
          </div>}

          <div className="pt-2 flex justify-end">
            <button
              onClick={handleValidate}
              disabled={!canProceed || isValidating}
              className="flex items-center space-x-2 px-6 py-3 rounded-xl font-bold text-sm bg-blue-600 hover:bg-blue-500 text-white transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {isValidating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Đang kiểm định dữ liệu...</span>
                </>
              ) : (
                <>
                  <span>Tiếp tục: Kiểm Định Dữ Liệu</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* ── STEP 2: Kết Quả Kiểm Định Chất Lượng Dữ Liệu ── */}
      {currentStep === 2 && validation && (
        <div className="glass-panel p-4 sm:p-8 rounded-3xl border border-slate-800 space-y-6 animate-fade-in">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <h2 className="text-lg font-bold text-white">Bước 2: Kết Quả Kiểm Định Chất Lượng Dữ Liệu</h2>
              <p className="text-xs text-slate-400 mt-1">
                Đánh giá độ sạch, tính toàn vẹn và tỷ lệ ngoại lai trước khi đưa vào phương pháp học máy.
              </p>
            </div>
            <div className="text-right">
              <div className="text-xs font-semibold text-slate-400">ĐIỂM CHẤT LƯỢNG DỮ LIỆU</div>
              <div className="text-3xl font-black text-emerald-400 font-mono">{validation.quality_score}/100</div>
            </div>
          </div>

          {/* Thông tin sản phẩm + dataset đã chọn */}
          <div className="flex flex-wrap items-center gap-2 p-3 rounded-xl bg-blue-600/10 border border-blue-500/30 text-xs">
            <CheckCircle2 className="w-4 h-4 text-blue-400 shrink-0" />
            <span className="text-slate-300">Sản phẩm: <strong className="text-white">{productName}</strong></span>
            <span className="text-slate-600">•</span>
            <span className="text-slate-300">Bộ dữ liệu: <strong className="text-slate-200">{viLabel(selectedDatasetMeta?.title || selectedDataset)}</strong></span>
          </div>

          {/* Quality Stats Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
              <span className="text-[11px] text-slate-500 block">Số dòng & Cột</span>
              <span className="text-sm font-bold text-white font-mono">{validation.total_rows} × {validation.total_columns}</span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
              <span className="text-[11px] text-slate-500 block">Giá trị thiếu</span>
              <span className="text-sm font-bold text-emerald-400 font-mono">{validation.missing_pct}% ({validation.missing_values_count} ô)</span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
              <span className="text-[11px] text-slate-500 block">Trùng Lặp</span>
              <span className="text-sm font-bold text-white font-mono">{validation.duplicate_pct}% ({validation.duplicate_rows_count} dòng)</span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
              <span className="text-[11px] text-slate-500 block">Ngoại Lai (IQR)</span>
              <span className="text-sm font-bold text-amber-400 font-mono">{validation.outlier_pct}% ({validation.outlier_count} điểm)</span>
            </div>
          </div>

          {/* Explanations */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">Chi Tiết Kiểm Định Tự Động:</h4>
            <div className="space-y-1.5 bg-slate-950/60 p-4 rounded-2xl border border-slate-800/80">
              {validation.explanations.map((exp, idx) => (
                <div key={idx} className="flex items-center space-x-2 text-xs text-slate-300">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>{exp}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Feature Roles */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">Ánh Xạ Vai Trò Đặc Trưng :</h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
              {[
                { label: 'Nhu cầu / Doanh số:', val: validation.column_roles.sales_col },
                { label: 'Giá bán:', val: validation.column_roles.price_col },
                { label: 'Tìm kiếm / Xu hướng tìm kiếm:', val: validation.column_roles.search_col },
                { label: 'Cạnh tranh / Thị phần:', val: validation.column_roles.competition_col },
                { label: 'Đánh giá / Chất lượng:', val: validation.column_roles.rating_col },
                { label: 'Tăng trưởng tháng/năm:', val: validation.column_roles.growth_col },
              ].map(({ label, val }) => (
                <div key={label} className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800">
                  <span className="text-slate-500 text-[10px] block">{label}</span>
                  <span className="font-semibold text-blue-400 truncate block">{val || 'Chưa nhận diện'}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 flex flex-wrap gap-3 items-center justify-between">
            <button
              onClick={() => setCurrentStep(1)}
              className="flex items-center space-x-1.5 px-5 py-2.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-white bg-slate-900 border border-slate-800"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Quay lại</span>
            </button>
            <button
              onClick={handleExecuteML}
              className="flex items-center space-x-2 px-7 py-3 rounded-xl font-bold text-sm bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-600/30 transition-all"
            >
              <Brain className="w-4 h-4" />
              <span>Chạy Phân Tích Học Máy & Lập Chiến Lược</span>
            </button>
          </div>
        </div>
      )}

      {/* ── STEP 3: Live ML Execution Progress ── */}
      {currentStep === 3 && (
        <div className="glass-panel-glow p-4 sm:p-10 rounded-3xl border border-blue-500/30 space-y-8 text-center animate-fade-in">
          <div className="w-16 h-16 rounded-2xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center mx-auto text-blue-400">
            <Brain className="w-8 h-8 animate-pulse" />
          </div>
          <div>
            <h2 className="text-2xl font-extrabold text-white mb-2">MarketWiseJu đang phân tích</h2>
            <p className="text-sm text-slate-400 max-w-md mx-auto">
              Hệ thống đang kiểm tra dữ liệu, tính toán dự báo và chuẩn bị đề xuất cho{' '}
              <span className="text-blue-400 font-semibold">{productName}</span>...
            </p>
          </div>

          <p role="status" aria-live="polite" className="text-blue-200">{mlError ? 'Phân tích tạm dừng' : job?.message || 'Đang gửi yêu cầu…'}</p>
          <div className="max-w-md mx-auto space-y-3 text-left">
            {mlPipelineSteps.map((stepDesc, idx) => {
              const isFinished = idx < mlStepIndex;
              const isCurrent = !mlError && job?.status === 'running' && idx === mlStepIndex;
              return (
                <div
                  key={idx}
                  className={`flex items-center space-x-3 p-3 rounded-xl text-xs transition-all ${
                    isCurrent
                      ? 'bg-blue-600/15 border border-blue-500/40 text-blue-300 font-semibold scale-[1.02]'
                      : isFinished
                      ? 'bg-slate-950/60 text-slate-300 border border-slate-800'
                      : 'text-slate-600'
                  }`}
                >
                  {isFinished ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  ) : isCurrent ? (
                    <Loader2 className="w-4 h-4 text-blue-400 animate-spin shrink-0" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-slate-700 shrink-0" />
                  )}
                  <span>{stepDesc}</span>
                </div>
              );
            })}
          </div>

          {mlError && (
            <div role="alert" className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center justify-between max-w-md mx-auto">
              <span>{mlError}</span>
              <button
                onClick={() => setCurrentStep(2)}
                className="px-3 py-1 bg-slate-900 hover:bg-slate-800 rounded font-semibold text-white ml-3 shrink-0"
              >
                Thử lại
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
