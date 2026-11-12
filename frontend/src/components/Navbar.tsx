import React, { useEffect, useState } from 'react';
import {
  TrendingUp,
  BarChart3,
  Database,
  FileText,
  PlusCircle,
  Search,
  Menu,
  X,
  UserCheck,
  Sun,
  Moon
} from './icons';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onNewAnalysis: () => void;
  theme?: 'light' | 'dark';
  onToggleTheme?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  onNewAnalysis,
  theme = 'dark',
  onToggleTheme
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const close = (event: KeyboardEvent) => { if (event.key === 'Escape') setMobileMenuOpen(false); };
    window.addEventListener('keydown', close);
    return () => window.removeEventListener('keydown', close);
  }, []);

  const startAnalysis = () => { setMobileMenuOpen(false); onNewAnalysis(); };

  const navItems = [
    { id: 'landing', label: 'Trang chủ', icon: FileText },
    { id: 'research', label: 'Nghiên cứu & So sánh', icon: Search },
    { id: 'dashboard', label: 'Tổng Quan & Tìm Kiếm', icon: BarChart3 },
    { id: 'datasets', label: 'Kho Dữ Liệu & Kiểm Định', icon: Database },
  ];

  const handleNavClick = (id: string) => {
    setActiveTab(id);
    setMobileMenuOpen(false);
  };

  return (
    <header className="site-header sticky top-0 z-50 glass-panel border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between gap-3 min-h-20">
          {/* Logo */}
          <div role="button" tabIndex={0} aria-label="MarketWise - Trang chủ" onKeyDown={event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); handleNavClick('landing'); } }}
            onClick={() => handleNavClick('landing')}
            className="brand-logo flex items-center space-x-3 cursor-pointer group shrink-0"
          >
            <div className="brand-mark w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center shadow-md group-hover:scale-105 transition-transform duration-200">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="brand-wordmark font-medium text-lg tracking-wider text-white">MARKET<span className="text-blue-400">WISE</span></span>
                <span className="hidden min-[1800px]:inline px-1.5 py-0.5 text-[9px] font-bold tracking-wide uppercase bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded">
                  Tra cứu đa nguồn
                </span>
              </div>
              <p className="brand-credit text-[10px] text-slate-400 leading-none">Bản quyền © Ju • Nguyễn Hoàng Anh</p>
            </div>
          </div>

          {/* Desktop Navigation Links */}
          <nav className="hidden 2xl:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  aria-current={isActive ? 'page' : undefined}
                  onClick={() => handleNavClick(item.id)}
                  className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all duration-200 ${
                    isActive
                      ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30 shadow-sm'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right Action & Theme Toggle & Author Badge */}
          <div className="hidden 2xl:flex items-center space-x-2.5">
            {onToggleTheme && (
              <button
                onClick={onToggleTheme}
                title={theme === 'light' ? 'Chuyển sang Chế độ Nền Tối' : 'Chuyển sang Chế độ Nền Sáng'}
                aria-label={theme === 'light' ? 'Chuyển sang Chế độ Nền Tối' : 'Chuyển sang Chế độ Nền Sáng'}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border border-slate-700 bg-slate-900/90 text-slate-200 hover:border-blue-500/50 transition-all"
              >
                {theme === 'light' ? (
                  <>
                    <Sun className="w-3.5 h-3.5 text-amber-400" />
                    <span>Nền Sáng</span>
                  </>
                ) : (
                  <>
                    <Moon className="w-3.5 h-3.5 text-blue-400" />
                    <span>Nền Tối</span>
                  </>
                )}
              </button>
            )}

            {/* Author Credit Badge */}
            <div className="hidden min-[1800px]:flex items-center space-x-1.5 text-xs text-slate-400 bg-slate-900/80 px-3 py-1.5 rounded-full border border-slate-800">
              <UserCheck className="w-3.5 h-3.5 text-blue-400" />
              <span>Tác giả: <strong className="text-slate-200">Nguyễn Hoàng Anh</strong></span>
            </div>

            <button
              onClick={startAnalysis}
              className="flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/25 transition-all duration-200 active:scale-95 shrink-0"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Phân Tích Mới</span>
            </button>
          </div>

          {/* Mobile Hamburger Button */}
          <div className="mobile-actions flex items-center space-x-2 2xl:hidden">
            {onToggleTheme && (
              <button
                onClick={onToggleTheme}
                aria-label="Đổi chế độ Sáng/Tối"
                className="p-2 rounded-lg border border-slate-700 bg-slate-900 text-slate-200"
              >
                {theme === 'light' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-blue-400" />}
              </button>
            )}
            <button
              onClick={startAnalysis}
              className="flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-bold bg-blue-600 text-white shadow-sm"
              aria-label="Phân tích mới"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span className="hidden min-[400px]:inline">Phân tích</span>
            </button>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 focus:outline-none"
              aria-label={mobileMenuOpen ? 'Đóng menu điều hướng' : 'Mở menu điều hướng'} aria-expanded={mobileMenuOpen} aria-controls="mobile-navigation"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div id="mobile-navigation" className="2xl:hidden border-t border-slate-800 bg-slate-950/95 px-4 pt-3 pb-5 space-y-2 animate-fade-in shadow-2xl">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                aria-current={isActive ? 'page' : undefined}
                onClick={() => handleNavClick(item.id)}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-semibold text-left transition-all ${
                  isActive
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                    : 'text-slate-300 hover:bg-slate-900 hover:text-white'
                }`}
              >
                <Icon className="w-4 h-4 text-blue-400" />
                <span>{item.label}</span>
              </button>
            );
          })}

          <div className="pt-3 border-t border-slate-800/80 text-xs text-slate-400 space-y-1">
            <p><strong>Tác giả:</strong> Nguyễn Hoàng Anh</p>
            <p><strong>Bản quyền:</strong> © Ju</p>
          </div>
        </div>
      )}
    </header>
  );
};
