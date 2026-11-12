import React from 'react';
import { TrendingUp, ShieldAlert, Cpu, UserCheck, ExternalLink } from './icons';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-slate-800 bg-slate-950/95 text-slate-400 py-12 mt-20 no-print">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
          {/* Col 1: Brand & Project */}
          <div className="md:col-span-2 space-y-4">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold shadow-md shadow-blue-600/30">
                <TrendingUp className="w-4 h-4" />
              </div>
              <span className="font-extrabold text-white text-lg tracking-wider">MARKET<span className="text-blue-400">WISE</span></span>
            </div>
            <p className="text-sm text-slate-400 leading-relaxed max-w-md">
              Nền tảng nghiên cứu đa nguồn, so sánh đối tượng và phân tích dữ liệu phục vụ lập kế hoạch.
            </p>
            <div className="flex items-center space-x-2 text-xs text-slate-500">
              <Cpu className="w-4 h-4 text-blue-400" />
              <span>Tra cứu nguồn công khai • Kiểm định dữ liệu • Phân tích và so sánh</span>
            </div>
          </div>

          {/* Col 2: Author & Copyright */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">Thông Tin Tác Giả & Bản Quyền</h4>
            <div className="space-y-1.5 text-xs text-slate-300">
              <p className="flex items-center space-x-1.5">
                <UserCheck className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                <span>Tác giả: <strong className="text-white">Nguyễn Hoàng Anh</strong></span>
              </p>
              <p className="text-emerald-400 font-semibold">Bản quyền thuộc về Ju</p>
              <p className="text-slate-400">Đồ án môn học & Nghiên cứu ứng dụng IT</p>
            </div>
          </div>

          {/* Col 3: Contact Links */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">Kênh Liên Hệ</h4>
            <div className="space-y-2">
              <a
                href="https://www.facebook.com/Ju2974"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center space-x-2 text-xs text-blue-400 hover:text-blue-300 bg-slate-900 hover:bg-slate-850 p-2 rounded-xl border border-slate-800 transition-colors group"
              >
                <span className="font-semibold">Facebook: Ju2974</span>
                <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-blue-400 ml-auto" />
              </a>

              <a
                href="https://www.instagram.com/ju.here_/"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center space-x-2 text-xs text-pink-400 hover:text-pink-300 bg-slate-900 hover:bg-slate-850 p-2 rounded-xl border border-slate-800 transition-colors group"
              >
                <span className="font-semibold">Instagram: @ju.here_</span>
                <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-pink-400 ml-auto" />
              </a>
            </div>
          </div>
        </div>

        <p className="text-xs text-slate-400 mb-6">Biểu tượng: <a href="https://lucide.dev/license" target="_blank" rel="noopener noreferrer" className="underline text-blue-300">Lucide (ISC)</a> · Tham khảo phong cách: <a href="https://www.flaticon.com/free-icons/web" target="_blank" rel="noopener noreferrer" className="underline text-blue-300">Flaticon Web Icons</a></p>
        {/* Disclaimer bar */}
        <div className="pt-6 border-t border-slate-800/80 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center space-x-2 text-amber-400/90">
            <ShieldAlert className="w-4 h-4 shrink-0" />
            <span>Kết quả hỗ trợ nghiên cứu và ra quyết định. Độ sạch của dữ liệu không xác nhận tính đúng sự thật; cần kiểm tra nguồn và thời điểm công bố.</span>
          </div>
          <div className="text-center md:text-right md:max-w-64 shrink-0">
            <span>© {new Date().getFullYear()} MARKETWISE • Bản quyền thuộc về Ju</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
