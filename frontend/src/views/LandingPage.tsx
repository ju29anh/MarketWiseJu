import React from 'react';
import {
  ArrowRight,
  BarChart3,
  Sparkles,
  Zap,
  Laptop,
  Smartphone,
  Shirt,
  Coffee,
  Car,
  BookOpen,
  Activity,
  Home,
  Cloud
} from '../components/icons';

interface LandingPageProps {
  onStartAnalysis: (category?: string) => void;
  onExploreDatasets: () => void;
  onResearch?: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onStartAnalysis, onExploreDatasets, onResearch }) => {
  const sectors = [
    { category: 'Technology & Gaming', title: 'Công nghệ & Máy tính', subtitle: 'Máy tính chơi game và phần cứng', icon: Laptop },
    { category: 'Smartphones & Mobile', title: 'Điện thoại & Di động', subtitle: 'Thiết bị cao cấp và tầm trung', icon: Smartphone },
    { category: 'Fashion & E-Commerce', title: 'Thời trang & Thương mại điện tử', subtitle: 'Thời trang thường ngày và thể thao', icon: Shirt },
    { category: 'Food & Beverage', title: 'Ẩm thực & Đồ uống', subtitle: 'Cà phê và đồ uống pha sẵn', icon: Coffee },
    { category: 'Beauty & Skincare', title: 'Mỹ phẩm & Chăm sóc da', subtitle: 'Tinh chất dưỡng da và kem chống nắng', icon: Sparkles },
    { category: 'Electric Vehicles', title: 'Xe điện', subtitle: 'Các dòng xe điện trên thế giới', icon: Car },
    { category: 'Education & EdTech', title: 'Giáo dục & Công nghệ giáo dục', subtitle: 'Khóa học công nghệ và chứng chỉ', icon: BookOpen },
    { category: 'Healthcare & Fitness', title: 'Sức khỏe & Thể chất', subtitle: 'Đồng hồ và vòng theo dõi sức khỏe', icon: Activity },
    { category: 'Smart Home & IoT', title: 'Nhà thông minh & Thiết bị kết nối', subtitle: 'Robot hút bụi và camera an ninh', icon: Home },
    { category: 'Digital Services & SaaS', title: 'Dịch vụ số & Phần mềm', subtitle: 'Công cụ viết nội dung và dịch vụ đám mây', icon: Cloud },
  ];

  const steps = [
    { num: '01', title: 'Xác định đối tượng & dữ liệu', desc: 'Nhập từ khóa để tra cứu đa nguồn, so sánh hai đối tượng hoặc tải lên dữ liệu CSV / XLSX của bạn.' },
    { num: '02', title: 'Kiểm định & Tiền xử lý', desc: 'Đo lường điểm chất lượng dữ liệu (0–100), rà soát giá trị thiếu, trùng lặp, ngoại lai IQR và chuẩn hóa đặc trưng.' },
    { num: '03', title: 'Phân tích dữ liệu đủ điều kiện', desc: 'Ước lượng xu hướng, phân nhóm quan sát và báo cáo sai số kiểm định trên dữ liệu phù hợp.' },
    { num: '04', title: 'Chiến lược & Báo cáo', desc: 'Đọc phân tích thị trường, phương án giá hoặc học phí khi phù hợp, rủi ro và kế hoạch 30–60–90 ngày với KPI.' }
  ];

  return (
    <div className="landing-page space-y-24 py-8">
      {/* Hero Section */}
      <section className="hero-section relative overflow-hidden pt-12 pb-16">
        <div className="hero-orb" aria-hidden="true">
          <svg viewBox="0 0 600 600" focusable="false">
            {[0, 30, 60, 90, 120, 150].map(angle => (
              <ellipse key={angle} cx="300" cy="300" rx="250" ry="100" transform={`rotate(${angle} 300 300)`} />
            ))}
            {Array.from({ length: 420 }, (_, index) => {
              const y = 1 - (index / 419) * 2;
              const radius = Math.sqrt(1 - y * y);
              const angle = index * Math.PI * (3 - Math.sqrt(5));
              const depth = Math.sin(angle) * radius;
              return <circle key={index} cx={300 + Math.cos(angle) * radius * 250} cy={300 + y * 250} r={depth > 0 ? 1.6 : .8} opacity={.35 + (depth + 1) * .3} />;
            })}
          </svg>
        </div>

        <div className="hero-content max-w-5xl mx-auto text-center px-4 sm:px-6">
          <div className="hero-eyebrow inline-flex items-center gap-2 text-xs uppercase mb-6 animate-fade-in">
            <Zap className="w-3.5 h-3.5 text-blue-400" />
            <span>Nghiên cứu đa nguồn & hỗ trợ ra quyết định</span>
          </div>

          <h1 className="hero-title text-white mb-6">
            Hiểu rõ thị trường.<br />
            <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-emerald-400 bg-clip-text text-transparent">
              Nhận diện xu hướng.
            </span><br />
            Chủ động bước tiếp theo.
          </h1>

          <p className="hero-description mx-auto mb-10 leading-relaxed font-normal">
            Phân tích thị trường, xây dựng phương án giá và nhận diện rủi ro từ dữ liệu có nguồn. Nhận dự báo khi dữ liệu đủ điều kiện và kế hoạch hành động với mục tiêu, người phụ trách và thời hạn.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={() => onResearch ? onResearch() : onStartAnalysis()}
              className="w-full sm:w-auto flex items-center justify-center space-x-3 px-8 py-4 rounded-xl text-base font-bold bg-blue-600 hover:bg-blue-500 text-white shadow-xl shadow-blue-600/30 hover:shadow-blue-600/45 transition-all duration-200 active:scale-95"
            >
              <span>Phân tích từ khóa & lập kế hoạch</span>
              <ArrowRight className="w-5 h-5" />
            </button>
            <button
              onClick={onExploreDatasets}
              className="w-full sm:w-auto flex items-center justify-center space-x-2.5 px-7 py-4 rounded-xl text-base font-semibold bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 hover:border-slate-600 transition-all duration-200"
            >
              <BarChart3 className="w-5 h-5 text-blue-400" />
              <span>Khám phá Dữ liệu Mẫu</span>
            </button>
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-10 max-w-2xl"><h2 className="text-xs uppercase tracking-widest text-blue-300 mb-3">Từ nguồn đến quyết định</h2><p className="text-3xl font-medium text-white">Biết rõ dữ liệu nói gì.</p><p className="text-sm text-slate-400 mt-3">Mỗi kết quả đi cùng phạm vi quan sát, nguồn tham khảo và những giới hạn cần xem xét.</p></div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {[
            {title:'Tra cứu đa nguồn',desc:'Tìm tài liệu về đúng đối tượng, xem trích đoạn và mở nguồn gốc để đối chiếu.'},
            {title:'So sánh trực tiếp',desc:'Nhập hai tên bất kỳ, đối chiếu theo các tiêu chí liên quan mà không cần báo cáo có sẵn.'},
            {title:'Kiểm tra dữ liệu',desc:'Phân biệt tài liệu, số liệu trích nguồn và dữ liệu định lượng đủ điều kiện dự báo.'},
            {title:'Xuất kết quả rõ ràng',desc:'Báo cáo dễ đọc, bảng số liệu có đơn vị, thời kỳ và đường dẫn nguồn cho từng quan sát.'},
          ].map((item,index)=><article key={item.title} className="glass-panel rounded-2xl p-6"><p className="step-number text-3xl mb-6">0{index+1}</p><h3 className="text-lg text-white mb-3">{item.title}</h3><p className="text-sm text-slate-400 leading-relaxed">{item.desc}</p></article>)}
        </div>
      </section>

      {/* Core User Flow Steps */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="glass-panel-glow p-8 sm:p-12 rounded-3xl border border-blue-500/20 bg-slate-900/90">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <h2 className="text-xs font-bold uppercase tracking-widest text-blue-400 mb-2">Luồng Nghiệp vụ Chuẩn</h2>
            <p className="text-2xl sm:text-3xl font-extrabold text-white">Quy trình từ dữ liệu đến quyết định</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {steps.map((step, idx) => (
              <div key={idx} className="relative p-5 rounded-2xl bg-slate-950/60 border border-slate-800/80">
                <div className="step-number text-3xl mb-2 font-mono">{step.num}</div>
                <h4 className="text-base font-bold text-white mb-2">{step.title}</h4>
                <p className="text-xs text-slate-400 leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Verified Market Sectors Showcase */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between mb-10 gap-4">
          <div>
            <h2 className="text-xs font-bold uppercase tracking-widest text-emerald-400 mb-1">Dữ liệu Chuẩn hóa</h2>
            <p className="text-2xl sm:text-3xl font-extrabold text-white">Các lĩnh vực thị trường tiêu biểu</p>
          </div>
          <button
            onClick={onExploreDatasets}
            className="text-sm font-semibold text-blue-400 hover:text-blue-300 flex items-center space-x-1"
          >
            <span>Xem chi tiết toàn bộ bộ dữ liệu</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {sectors.map((sector) => {
            const Icon = sector.icon;
            return (
              <button
                type="button"
                key={sector.category}
                onClick={() => onStartAnalysis(sector.category)}
                className="sector-card group glass-panel p-6 rounded-2xl border border-slate-800 hover:border-blue-500/40 cursor-pointer transition-colors duration-200"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400 group-hover:scale-110 transition-transform">
                    <Icon className="w-6 h-6" />
                  </div>
                  <div className="text-right">
                    <span className="text-[11px] font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      Dữ liệu tham khảo
                    </span>
                    <p className="text-[11px] text-slate-500 mt-1">Xem dữ liệu trong kho</p>
                  </div>
                </div>
                <h3 className="text-lg font-bold text-white group-hover:text-blue-400 transition-colors">{sector.title}</h3>
                <p className="text-xs text-slate-400 mt-1 mb-4">{sector.subtitle}</p>
                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <span>Xem và kiểm tra dữ liệu nguồn</span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:translate-x-1 transition-transform" />
                </div>
              </button>
            );
          })}
        </div>
      </section>
    </div>
  );
};
