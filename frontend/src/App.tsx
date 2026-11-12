import { LoadingSkeleton } from './components/common/LoadingSkeleton';
import { ErrorNotice } from './components/common/ErrorNotice';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { errorMessage } from './utils/errors';
import { useState, useEffect, useRef, lazy, Suspense } from 'react';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
const LandingPage = lazy(() => import('./views/LandingPage').then(module => ({ default: module.LandingPage })));
const DashboardView = lazy(() => import('./views/DashboardView').then(module => ({ default: module.DashboardView })));
const AnalysisWizardView = lazy(() => import('./views/AnalysisWizardView').then(module => ({ default: module.AnalysisWizardView })));
const AnalysisResultView = lazy(() => import('./views/AnalysisResultView').then(module => ({ default: module.AnalysisResultView })));
const DatasetsView = lazy(() => import('./views/DatasetsView').then(module => ({ default: module.DatasetsView })));
const ResearchView = lazy(() => import('./views/ResearchView').then(module => ({ default: module.ResearchView })));
import { AnalysisPayload } from './types';
import { apiClient } from './api/client';
import { API_BASE, safeFetch } from './api/http';

export function App() {
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [lastSession, setLastSession] = useState('');
  const [activeTab, setActiveTab] = useState<string>('landing');
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisPayload | null>(null);
  const [researchQuery, setResearchQuery] = useState('');
  const [publicDemo, setPublicDemo] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    safeFetch(`${API_BASE}/config`, {signal: controller.signal}).then(r=>r.json()).then(config=>{if(!controller.signal.aborted) setPublicDemo(config.public_demo===true);}).catch(()=>{});
    return ()=>controller.abort();
  }, []);

  // Auros is dark by default; retain the user's explicit theme preference.
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    try {
      const saved = window.localStorage.getItem('mw_auros_theme');
      if (saved === 'dark' || saved === 'light') return saved;
    } catch {
      // ignore storage error
    }
    return 'dark';
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'light') {
      root.classList.add('light-theme');
    } else {
      root.classList.remove('light-theme');
    }
    try {
      window.localStorage.setItem('mw_auros_theme', theme);
    } catch {
      // ignore storage error
    }
  }, [theme]);

  const handleToggleTheme = () => {
    setTheme(prev => (prev === 'light' ? 'dark' : 'light'));
  };

  // Wizard state
  const [isWizardOpen, setIsWizardOpen] = useState<boolean>(false);
  const [wizardPreselectedCategory, setWizardPreselectedCategory] = useState<string | undefined>();
  const [wizardPreselectedDataset, setWizardPreselectedDataset] = useState<string | undefined>();
  const [wizardPreselectedProduct, setWizardPreselectedProduct] = useState<string | undefined>();
  const [isLoadingSession, setIsLoadingSession] = useState<boolean>(false);
  const sessionController = useRef<AbortController | null>(null);
  useEffect(() => () => sessionController.current?.abort(), []);

  const cancelSessionLoad = () => {
    sessionController.current?.abort();
    setIsLoadingSession(false);
    setSessionError(null);
  };

  useEffect(() => { window.scrollTo({ top: 0, behavior: 'instant' }); }, [activeTab, isWizardOpen]);

  const handleStartNewAnalysis = (category?: string, datasetFilename?: string, productName?: string) => {
    cancelSessionLoad();
    setWizardPreselectedCategory(category);
    setWizardPreselectedDataset(datasetFilename);
    setWizardPreselectedProduct(productName);
    setIsWizardOpen(true);
  };

  const handleViewAnalysis = async (sessionId: string) => {
    sessionController.current?.abort();
    const controller = new AbortController();
    sessionController.current = controller;
    setIsLoadingSession(true); setSessionError(null); setLastSession(sessionId);
    try {
      const data = await apiClient.getAnalysisById(sessionId, controller.signal);
      if (controller.signal.aborted) return;
      setCurrentAnalysis(data);
      setIsWizardOpen(false);
      setActiveTab('result');
    } catch (err) {
      if (!controller.signal.aborted) setSessionError(errorMessage(err));
    } finally {
      if (!controller.signal.aborted) setIsLoadingSession(false);
    }
  };

  const handleAnalysisCompleted = (payload: AnalysisPayload) => {
    setCurrentAnalysis(payload);
    setIsWizardOpen(false);
    setActiveTab('result');
  };

  return (
    <div className="app-shell min-h-screen flex flex-col font-sans antialiased">
      <a href="#main-content" className="skip-link">Đi đến nội dung chính</a>
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={(tab) => {
          cancelSessionLoad();
          setIsWizardOpen(false);
          setActiveTab(tab);
        }}
        onNewAnalysis={() => handleStartNewAnalysis()}
        theme={theme}
        onToggleTheme={handleToggleTheme}
      />

      {/* Main Content Body */}
      <main id="main-content" className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {publicDemo && <p role="status" className="mb-5 rounded-2xl border border-slate-700 bg-slate-950 p-4 text-xs text-slate-300 no-print">Bản demo công khai: dữ liệu và báo cáo có thể được dùng chung, mất khi máy chủ khởi động lại. Chỉ dùng dữ liệu mẫu hoặc công khai; tải báo cáo cần giữ về máy.</p>}
        {!isWizardOpen && activeTab !== 'research' && activeTab !== 'result' && (
          <div className="research-banner mb-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-700 p-4 text-sm">
            <div className="flex items-center gap-2.5">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-600/15 text-blue-400 border border-blue-500/30">
                Tra cứu & đối chiếu nguồn
              </span>
              <p className="text-slate-200 font-medium">
                Nghiên cứu trường đại học, thương hiệu, địa danh hoặc sản phẩm với dữ liệu Web uy tín thời gian thực.
              </p>
            </div>
            <button onClick={() => setActiveTab('research')} className="text-blue-400 font-bold underline underline-offset-4 hover:text-blue-300">
              Mở Nghiên cứu & So sánh →
            </button>
          </div>
        )}
        {sessionError && <ErrorNotice message={sessionError} retry={() => void handleViewAnalysis(lastSession)} />}
        {isLoadingSession && <LoadingSkeleton />}
        <ErrorBoundary><Suspense fallback={<LoadingSkeleton />}>
        {/* Wizard Modal / Full Screen Flow */}
        {isWizardOpen ? (
          <AnalysisWizardView
            initialCategory={wizardPreselectedCategory}
            initialDataset={wizardPreselectedDataset}
            initialProductName={wizardPreselectedProduct}
            onCancel={() => setIsWizardOpen(false)}
            onAnalysisComplete={handleAnalysisCompleted}
            onResearch={(query) => { setResearchQuery(query); setIsWizardOpen(false); setActiveTab('research'); }}
          />
        ) : (
          <>
            {activeTab === 'research' && (
              <ResearchView
                key={researchQuery}
                initialQuery={researchQuery}
                onStartAnalysis={(cat, ds, prod) => handleStartNewAnalysis(cat, ds, prod)}
                onViewAnalysis={handleViewAnalysis}
              />
            )}
            {activeTab === 'landing' && (
              <LandingPage
                onStartAnalysis={(category) => handleStartNewAnalysis(category)}
                onExploreDatasets={() => setActiveTab('datasets')}
                onResearch={() => { setResearchQuery(''); setActiveTab('research'); }}
              />
            )}

            {activeTab === 'dashboard' && (
              <DashboardView
                onStartAnalysis={(cat, ds, prod) => handleStartNewAnalysis(cat, ds, prod)}
                onViewAnalysis={handleViewAnalysis}
                onResearch={(query) => { setResearchQuery(query.trim()); setActiveTab('research'); }}
              />
            )}

            {activeTab === 'result' && currentAnalysis && (
              <AnalysisResultView
                data={currentAnalysis}
                onBackToDashboard={() => setActiveTab('dashboard')}
                onNewAnalysis={() => handleStartNewAnalysis()}
                onUploadData={() => handleStartNewAnalysis(currentAnalysis.category, undefined, currentAnalysis.product_name)}
                onResearch={(query) => { setResearchQuery(query); setActiveTab('research'); }}
              />
            )}

            {activeTab === 'datasets' && (
              <DatasetsView
                onStartAnalysisWithDataset={(cat, ds) => handleStartNewAnalysis(cat, ds)}
              />
            )}
          </>
        )}
        </Suspense></ErrorBoundary>
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}

export default App;
