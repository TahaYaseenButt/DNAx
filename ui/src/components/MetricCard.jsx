import React from 'react';

export default function MetricCard({ title, value, subtext, icon: Icon, accent = 'sky' }) {
  const iconAccents = {
    indigo: 'bg-indigo-50/80 text-indigo-600 border border-indigo-100',
    emerald: 'bg-emerald-50/80 text-emerald-600 border border-emerald-100',
    amber: 'bg-amber-50/80 text-amber-600 border border-amber-100',
    sky: 'bg-sky-50/80 text-sky-600 border border-sky-100',
    violet: 'bg-violet-50/80 text-violet-600 border border-violet-100',
    rose: 'bg-rose-50/80 text-rose-600 border border-rose-100',
  };

  return (
    <div className="glass-panel glass-panel-hover p-5 flex flex-col justify-between">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 font-mono">{title}</span>
        {Icon && (
          <div className={`p-2 rounded-xl ${iconAccents[accent] || iconAccents.sky}`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>
      <div className="mt-3">
        <div className="text-2xl font-black tracking-tight text-slate-900 font-sans">{value}</div>
        {subtext && <div className="text-xs text-slate-500 mt-1 font-medium">{subtext}</div>}
      </div>
    </div>
  );
}
