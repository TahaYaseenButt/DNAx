import React, { useState } from 'react';
import {
  Home,
  Ruler,
  Dna,
  Scale,
  FlaskConical,
  Activity,
  Save,
  Database,
  FileText,
  ShieldCheck,
  Sparkles
} from 'lucide-react';
import logoImg from '../assets/logo.png';

export default function Sidebar({ currentPage, setCurrentPage }) {
  const [isHovered, setIsHovered] = useState(false);

  const navSections = [
    {
      title: null,
      items: [
        { id: 'home', label: 'Command Dashboard', icon: Home },
      ]
    },
    {
      title: 'Assay Pipeline',
      items: [
        { id: 'size', label: '1. Physical Sizing', icon: Ruler, step: '01' },
        { id: 'dna', label: '2. DNA Synthesis', icon: Dna, step: '02' },
        { id: 'comparator', label: '3. BLAST Homology', icon: Scale, step: '03' },
        { id: 'primer', label: '4. PCR Primers', icon: FlaskConical, step: '04' },
        { id: 'qpcr', label: '5. qPCR Probes', icon: Activity, step: '05' },
        { id: 'export', label: '6. Review & Save', icon: Save, step: '06' },
      ]
    },
    {
      title: 'Repository',
      items: [
        { id: 'matrix_db', label: 'Sequence Library', icon: Database },
        { id: 'protocol', label: 'Standard SOPs', icon: FileText },
      ]
    }
  ];

  const isExpanded = isHovered;

  return (
    <aside
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`h-screen backdrop-blur-2xl bg-white/85 border-r border-slate-200/80 flex flex-col justify-between transition-all duration-300 ease-in-out select-none z-40 shadow-lg ${
        isExpanded ? 'w-64' : 'w-16'
      }`}
    >
      {/* 1. Brand Header */}
      <div>
        <div className="h-16 flex items-center px-3.5 border-b border-slate-200/60 bg-white/40 overflow-hidden">
          <div
            onClick={() => setCurrentPage('home')}
            className="flex items-center space-x-3 cursor-pointer overflow-hidden group min-w-0"
          >
            <img
              src={logoImg}
              alt="DNAx Logo"
              className="w-8 h-8 object-contain shrink-0 group-hover:scale-105 transition-transform drop-shadow-xs"
            />
            {isExpanded && (
              <div className="leading-tight truncate animate-fadeIn">
                <div className="flex items-center space-x-1.5">
                  <span className="font-extrabold text-sm tracking-tight text-slate-900">DNA<span className="gradient-text-sky-indigo font-black">x</span></span>
                  <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded-md bg-sky-100/80 text-sky-800 border border-sky-200/60">
                    PRO
                  </span>
                </div>
                <span className="text-[11px] text-slate-400 font-medium block">Assay Platform</span>
              </div>
            )}
          </div>
        </div>

        {/* 2. Navigation Items */}
        <div className="p-2.5 space-y-3 overflow-y-auto max-h-[calc(100vh-7rem)] overflow-x-hidden">
          {navSections.map((section, sIdx) => (
            <div key={sIdx} className="space-y-0.5">
              {section.title && isExpanded && (
                <div className="px-2.5 text-[10px] font-extrabold tracking-wider text-slate-400 uppercase mb-1 mt-2 animate-fadeIn truncate">
                  {section.title}
                </div>
              )}
              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive = currentPage === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setCurrentPage(item.id)}
                    className={`relative w-full flex items-center rounded-xl text-xs transition-all duration-150 cursor-pointer ${
                      !isExpanded ? 'justify-center p-2.5' : 'px-2.5 py-2 space-x-2.5'
                    } ${
                      isActive
                        ? 'bg-sky-500/10 text-sky-900 font-bold border border-sky-300/40 shadow-xs'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/60 font-medium'
                    }`}
                    title={!isExpanded ? item.label : undefined}
                  >
                    {/* Active Accent Left Bar Indicator */}
                    {isActive && isExpanded && (
                      <div className="absolute left-0 top-1.5 bottom-1.5 w-[3px] bg-gradient-to-b from-sky-500 to-indigo-600 rounded-r-full" />
                    )}

                    <Icon
                      className={`w-4 h-4 shrink-0 transition-colors ${
                        isActive ? 'text-sky-600 stroke-[2.2]' : 'text-slate-400 group-hover:text-slate-600'
                      }`}
                    />

                    {isExpanded && (
                      <div className="flex items-center justify-between w-full truncate animate-fadeIn">
                        <span className="truncate">{item.label}</span>
                        {item.step && (
                          <span className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded-md ${
                            isActive ? 'bg-sky-100 text-sky-900 border border-sky-200' : 'bg-slate-100/70 text-slate-400'
                          }`}>
                            {item.step}
                          </span>
                        )}
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* 3. Footer */}
      <div className="p-3 border-t border-slate-200/60 bg-white/30 text-xs text-slate-400 font-mono flex items-center justify-between overflow-hidden">
        {isExpanded ? (
          <div className="flex items-center justify-between w-full animate-fadeIn">
            <span className="flex items-center space-x-1.5 text-[11px] text-slate-500 font-medium">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>Engine Active</span>
            </span>
            <span className="text-[10px] text-slate-400 font-bold">v2.0</span>
          </div>
        ) : (
          <div className="w-full flex justify-center">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" title="Core Engine Active" />
          </div>
        )}
      </div>
    </aside>
  );
}
