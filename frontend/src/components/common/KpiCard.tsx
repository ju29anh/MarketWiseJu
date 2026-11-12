import { AppIcon, type IconName } from '../icons';

export function KpiCard({ label, value, detail, icon, tone = 'blue' }: {
  label: string; value: string; detail: string; icon: IconName; tone?: 'blue' | 'emerald' | 'amber' | 'violet';
}) {
  const colors = { blue: 'text-blue-300 bg-blue-500/15', emerald: 'text-emerald-300 bg-emerald-500/15', amber: 'text-amber-300 bg-amber-500/15', violet: 'text-violet-300 bg-violet-500/15' };
  return <article className="kpi-card">
    <div className="flex items-center gap-3 mb-4"><span className={`rounded-xl p-2 ${colors[tone]}`}><AppIcon name={icon} size={20} /></span><h3 className="text-sm text-slate-300">{label}</h3></div>
    <p className="kpi-value text-2xl sm:text-3xl tabular-nums tracking-tight">{value}</p>
    <p className="text-xs text-slate-400 mt-2 leading-relaxed">{detail}</p>
  </article>;
}
