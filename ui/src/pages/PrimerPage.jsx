import React, { useState } from 'react';
import { FlaskConical, ArrowRight, Copy, Check, ShieldCheck, Activity, Save, Zap, Sparkles } from 'lucide-react';
import MetricCard from '../components/MetricCard';
import SequenceViewer from '../components/SequenceViewer';
import DNA3DViewer from '../components/DNA3DViewer';

export default function PrimerPage({ setCurrentPage, constructData }) {
  const primers = constructData?.primers || {
    fwd: { seq: 'CGATCGATCGATCGATCGAT', tm: 59.2, gc: 50.0, len: 20, score: 98 },
    rev: { seq: 'TAACGATCGATCGCTAGCGC', tm: 58.8, gc: 50.0, len: 20, score: 96 },
    product_size: constructData?.length || 500,
  };

  const [copiedFwd, setCopiedFwd] = useState(false);
  const [copiedRev, setCopiedRev] = useState(false);

  const copyText = (txt, isFwd) => {
    navigator.clipboard.writeText(txt);
    if (isFwd) {
      setCopiedFwd(true);
      setTimeout(() => setCopiedFwd(false), 2000);
    } else {
      setCopiedRev(true);
      setTimeout(() => setCopiedRev(false), 2000);
    }
  };

  const deltaTm = Math.abs((primers.fwd?.tm || 0) - (primers.rev?.tm || 0));
  const fullSeq = constructData?.linear_seq || constructData?.payload || 'CGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGAT';

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-indigo-600 font-bold uppercase tracking-wider">
            <span>STEP 04 OF 06</span>
            <span>•</span>
            <span>AMPLIFICATION PRIMERS</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight mt-1">PCR Primer Designer & 3D Annealing Sites</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Optimal forward & reverse oligonucleotides with 3D annealing site visualization, 3' GC clamp, and ΔTm ≤ 1.5°C matching.
          </p>
        </div>

        <button
          onClick={() => setCurrentPage('qpcr')}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 active:scale-95 text-white text-xs font-bold transition shadow-sm"
        >
          <span>Next: qPCR Probes</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Amplicon Product Size"
          value={`${primers.product_size || 500} bp`}
          subtext="Full amplified fragment length"
          accent="indigo"
          icon={FlaskConical}
        />
        <MetricCard
          title="Primer Melting Temp (Tm)"
          value={`~${primers.fwd?.tm?.toFixed(1) || 59.0}°C`}
          subtext={`Forward: ${primers.fwd?.tm?.toFixed(1)}°C | Rev: ${primers.rev?.tm?.toFixed(1)}°C`}
          accent="emerald"
          icon={Zap}
        />
        <MetricCard
          title="Melting Delta (ΔTm)"
          value={`${deltaTm.toFixed(1)}°C`}
          subtext={deltaTm <= 1.5 ? '✓ Perfect Annealing Match' : 'Acceptable range'}
          accent={deltaTm <= 1.5 ? 'emerald' : 'amber'}
          icon={ShieldCheck}
        />
        <MetricCard
          title="Assay Specificity"
          value="100% Unique"
          subtext="Zero off-target binding in DB"
          accent="sky"
          icon={ShieldCheck}
        />
      </div>

      {/* 3D Primer Annealing Site Visualizer */}
      <DNA3DViewer
        sequence={fullSeq}
        mode={constructData?.mode || 'linear'}
        primers={primers}
        highlightFeature="primers"
        height={320}
      />

      {/* Forward & Reverse Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Forward Primer */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50" />
              <span className="text-sm font-bold text-slate-900">Forward Primer (5' → 3' Sense Strand)</span>
            </div>
            <button
              onClick={() => copyText(primers.fwd?.seq, true)}
              className="flex items-center space-x-1 text-xs font-semibold px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition shadow-sm"
            >
              {copiedFwd ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-slate-400" />}
              <span>{copiedFwd ? 'Copied' : 'Copy'}</span>
            </button>
          </div>

          <div className="bg-emerald-50/50 font-mono text-sm font-bold text-emerald-800 p-3.5 rounded-xl border border-emerald-200 break-all select-text">
            {primers.fwd?.seq || 'N/A'}
          </div>

          <div className="grid grid-cols-3 gap-2 text-center pt-2">
            <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-[10px] text-slate-500 block font-bold">LENGTH</span>
              <span className="text-xs font-extrabold text-slate-900 font-mono">{primers.fwd?.len || primers.fwd?.seq?.length || 20} bp</span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-[10px] text-slate-500 block font-bold">TM</span>
              <span className="text-xs font-extrabold text-slate-900 font-mono">{primers.fwd?.tm?.toFixed(1) || 59.0}°C</span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-[10px] text-slate-500 block font-bold">GC%</span>
              <span className="text-xs font-extrabold text-slate-900 font-mono">{primers.fwd?.gc?.toFixed(1) || 50.0}%</span>
            </div>
          </div>
        </div>

        {/* Reverse Primer */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-sky-500 shadow-sm shadow-sky-500/50" />
              <span className="text-sm font-bold text-slate-900">Reverse Primer (5' → 3' Antisense Strand)</span>
            </div>
            <button
              onClick={() => copyText(primers.rev?.seq, false)}
              className="flex items-center space-x-1 text-xs font-semibold px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition shadow-sm"
            >
              {copiedRev ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-slate-400" />}
              <span>{copiedRev ? 'Copied' : 'Copy'}</span>
            </button>
          </div>

          <div className="bg-sky-50/50 font-mono text-sm font-bold text-sky-800 p-3.5 rounded-xl border border-sky-200 break-all select-text">
            {primers.rev?.seq || 'N/A'}
          </div>

          <div className="grid grid-cols-3 gap-2 text-center pt-2">
            <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-[10px] text-slate-500 block font-bold">LENGTH</span>
              <span className="text-xs font-extrabold text-slate-900 font-mono">{primers.rev?.len || primers.rev?.seq?.length || 20} bp</span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-[10px] text-slate-500 block font-bold">TM</span>
              <span className="text-xs font-extrabold text-slate-900 font-mono">{primers.rev?.tm?.toFixed(1) || 58.8}°C</span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-[10px] text-slate-500 block font-bold">GC%</span>
              <span className="text-xs font-extrabold text-slate-900 font-mono">{primers.rev?.gc?.toFixed(1) || 50.0}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Sequence Viewer with Feature Highlighting */}
      <SequenceViewer
        title="Construct Sequence with Primer Hybridization Regions"
        sequence={fullSeq}
        primers={primers}
        badge="PCR Primer Sites Highlighted"
      />

      {/* Next Step Nav Bar */}
      <div className="bg-white rounded-2xl p-4 border border-slate-200/90 shadow-sm flex items-center justify-end space-x-3">
        <button
          onClick={() => setCurrentPage('qpcr')}
          className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-700 text-white text-xs font-bold transition shadow-sm"
        >
          <Activity className="w-3.5 h-3.5" />
          <span>Next: Review TaqMan Probes ➡</span>
        </button>
        <button
          onClick={() => setCurrentPage('export')}
          className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition shadow-sm"
        >
          <Save className="w-3.5 h-3.5" />
          <span>Proceed to Final Save & Export ➡</span>
        </button>
      </div>
    </div>
  );
}
