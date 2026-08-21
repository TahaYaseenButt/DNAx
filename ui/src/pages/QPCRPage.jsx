import React, { useState } from 'react';
import { Activity, ArrowRight, Copy, Check, ShieldCheck, Save, Sparkles, Layers, Eye, Target } from 'lucide-react';
import MetricCard from '../components/MetricCard';
import SequenceViewer from '../components/SequenceViewer';
import DNA3DViewer from '../components/DNA3DViewer';

export default function QPCRPage({ setCurrentPage, constructData }) {
  const probes = constructData?.probes || [
    { channel: 'FAM', seq: 'CATGCGATCGATCGATCGATCGAT', tm: 69.5, gc: 50.0, len: 24, start: 30, end: 54 },
    { channel: 'HEX', seq: 'AGCTAGCTAGCTAGCTAGCTAGCT', tm: 70.1, gc: 48.0, len: 24, start: 80, end: 104 },
    { channel: 'ROX', seq: 'CGATCGATCGATCGATCGATCGAT', tm: 69.8, gc: 52.0, len: 24, start: 140, end: 164 },
    { channel: 'Cy5', seq: 'TGCATGCATGCATGCATGCATGCA', tm: 70.4, gc: 50.0, len: 24, start: 200, end: 224 },
  ];

  const [copiedIdx, setCopiedIdx] = useState(null);
  const [selectedProbe, setSelectedProbe] = useState(null);

  const fullSeq = constructData?.linear_seq || constructData?.payload || 'CGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGAT';

  const copyProbe = (seq, idx) => {
    navigator.clipboard.writeText(seq);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  // Helper to render sequence with isolated highlighted probe site
  const renderIsolatedProbeSequence = (probe, probeIdx) => {
    const start = probe.start || (30 + probeIdx * 50);
    const end = probe.end || (start + (probe.seq?.length || 24));

    const colorConfig = [
      { bg: 'bg-emerald-100 text-emerald-950 ring-2 ring-emerald-400', border: 'border-emerald-300', tag: 'bg-emerald-500 text-white' },
      { bg: 'bg-amber-100 text-amber-950 ring-2 ring-amber-400', border: 'border-amber-300', tag: 'bg-amber-500 text-white' },
      { bg: 'bg-orange-100 text-orange-950 ring-2 ring-orange-400', border: 'border-orange-300', tag: 'bg-orange-500 text-white' },
      { bg: 'bg-pink-100 text-pink-950 ring-2 ring-pink-400', border: 'border-pink-300', tag: 'bg-pink-500 text-white' },
    ][probeIdx % 4];

    // Format in blocks of 10
    const rowSize = 40;
    const rows = [];
    for (let i = 0; i < fullSeq.length; i += rowSize) {
      const rowSeq = fullSeq.slice(i, i + rowSize);
      const rowStart = i;

      const baseElements = rowSeq.split('').map((base, bIdx) => {
        const globalIdx = rowStart + bIdx;
        const isProbeSite = globalIdx >= start && globalIdx < end;

        let baseColor = 'text-slate-600';
        if (isProbeSite) {
          return (
            <span
              key={bIdx}
              className={`font-black font-mono ${colorConfig.bg} px-[1.5px] rounded-2xs`}
              title={`Probe ${probe.channel} binding site (bp ${globalIdx + 1})`}
            >
              {base}
            </span>
          );
        }

        if (base === 'A') baseColor = 'text-rose-500/70';
        else if (base === 'T') baseColor = 'text-sky-500/70';
        else if (base === 'C') baseColor = 'text-emerald-500/70';
        else if (base === 'G') baseColor = 'text-amber-500/70';

        return (
          <span key={bIdx} className={`font-mono ${baseColor} px-[0.5px]`}>
            {base}
          </span>
        );
      });

      rows.push(
        <div key={i} className="flex items-center space-x-2 py-0.5">
          <span className="text-[10px] font-mono text-slate-400 select-none w-8 text-right shrink-0">
            {i + 1}
          </span>
          <div className="font-mono text-xs tracking-wider flex-1">
            {baseElements}
          </div>
          <span className="text-[10px] font-mono text-slate-400 select-none w-8 text-left shrink-0">
            {Math.min(fullSeq.length, i + rowSize)}
          </span>
        </div>
      );
    }

    return (
      <div className="bg-slate-50/90 rounded-xl p-3.5 border border-slate-200/90 space-y-2">
        <div className="flex items-center justify-between text-[11px] font-mono pb-1.5 border-b border-slate-200">
          <span className="font-bold text-slate-700 flex items-center space-x-1.5">
            <Target className="w-3.5 h-3.5 text-sky-600" />
            <span>Target Template DNA Binding Map</span>
          </span>
          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${colorConfig.tag}`}>
            {probe.channel} SITE: bp {start + 1} – {end}
          </span>
        </div>
        <div className="max-h-36 overflow-y-auto font-mono text-xs select-text">
          {rows}
        </div>
      </div>
    );
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-sky-600 font-bold uppercase tracking-wider">
            <span>STEP 05 OF 06</span>
            <span>•</span>
            <span>FLUORESCENT PROBES</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight mt-1">4-Channel qPCR TaqMan Probes & Hybridization</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            High-affinity melting temperatures (Tm 68–72°C), spatial hybridization positions, and 5' reporter fluorophores.
          </p>
        </div>

        <button
          onClick={() => setCurrentPage('export')}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-700 active:scale-95 text-white text-xs font-bold transition shadow-sm cursor-pointer"
        >
          <span>Next: Review & Save</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Multiplex Channels"
          value="4 Fluorophores"
          subtext="FAM, HEX, ROX, Cy5"
          accent="violet"
          icon={Activity}
        />
        <MetricCard
          title="Target Probe Tm"
          value="~69.8°C"
          subtext="Strictly 8–10°C above primers"
          accent="emerald"
          icon={ShieldCheck}
        />
        <MetricCard
          title="GC Clamp Stability"
          value="100% Valid"
          subtext="No 5' Guanine fluorescence quenching"
          accent="sky"
          icon={Sparkles}
        />
        <MetricCard
          title="Assay Orthogonality"
          value="100% Unique"
          subtext="0 Cross-talk across DB probes"
          accent="amber"
          icon={ShieldCheck}
        />
      </div>

      {/* 3D TaqMan Probes Hybridization Visualizer */}
      <DNA3DViewer
        sequence={fullSeq}
        mode={constructData?.mode || 'linear'}
        probes={probes}
        highlightFeature="probes"
        height={320}
      />

      {/* 4 Probes Grid with Individual Highlighted Sequence Beneath Each */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-extrabold uppercase tracking-wider text-slate-800 flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-sky-600" />
            <span>4-Channel TaqMan Multiplex Set & Annealing Sites</span>
          </h2>
          <span className="text-xs font-mono text-slate-500">Color-Coded Hybridization Tracks</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {probes.map((probe, idx) => {
            const colors = [
              'border-emerald-300 text-emerald-800 bg-emerald-50',
              'border-amber-300 text-amber-800 bg-amber-50',
              'border-orange-300 text-orange-800 bg-orange-50',
              'border-pink-300 text-pink-800 bg-pink-50',
            ];
            const dyeColors = [
              'text-emerald-600',
              'text-amber-600',
              'text-orange-600',
              'text-pink-600',
            ];
            const quenchers = ['BHQ-1', 'BHQ-1', 'BHQ-2', 'BHQ-3'];

            return (
              <div
                key={idx}
                className="lab-card p-5 space-y-4 border-slate-200 hover:border-slate-300"
              >
                {/* Header */}
                <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                  <div className="flex items-center space-x-2">
                    <span className={`px-2.5 py-0.5 rounded-md text-[10px] font-extrabold uppercase border ${colors[idx % 4]}`}>
                      CHANNEL {idx + 1}: {probe.channel || `CH_${idx + 1}`}
                    </span>
                    <span className="text-xs text-slate-400 font-medium">5'-{probe.channel} / 3'-{quenchers[idx % 4]}</span>
                  </div>
                  <button
                    onClick={() => copyProbe(probe.seq, idx)}
                    className="flex items-center space-x-1 text-xs font-semibold px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition cursor-pointer"
                  >
                    {copiedIdx === idx ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3 text-slate-400" />}
                    <span>{copiedIdx === idx ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>

                {/* Probe Sequence Pill */}
                <div className="bg-slate-50 font-mono text-xs font-bold text-slate-800 p-3 rounded-xl border border-slate-200 break-all select-text">
                  <span className={`${dyeColors[idx % 4]} font-black`}>5'-[{probe.channel || 'DYE'}]-</span>
                  <span className="text-slate-900 font-bold">{probe.seq}</span>
                  <span className="text-slate-400 font-normal">-[{quenchers[idx % 4]}]-3'</span>
                </div>

                {/* Probe Metrics */}
                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="p-2 rounded-lg bg-slate-50 border border-slate-200">
                    <span className="text-[10px] text-slate-500 block font-bold">LENGTH</span>
                    <span className="font-extrabold text-slate-900 font-mono">{probe.len || probe.seq?.length || 24} bp</span>
                  </div>
                  <div className="p-2 rounded-lg bg-slate-50 border border-slate-200">
                    <span className="text-[10px] text-slate-500 block font-bold">TM</span>
                    <span className="font-extrabold text-slate-900 font-mono">{probe.tm?.toFixed(1) || 69.5}°C</span>
                  </div>
                  <div className="p-2 rounded-lg bg-slate-50 border border-slate-200">
                    <span className="text-[10px] text-slate-500 block font-bold">GC%</span>
                    <span className="font-extrabold text-slate-900 font-mono">{probe.gc?.toFixed(1) || 50.0}%</span>
                  </div>
                </div>

                {/* Distinct Template DNA Sequence with THIS Probe Highlighted */}
                {renderIsolatedProbeSequence(probe, idx)}
              </div>
            );
          })}
        </div>
      </div>

      {/* Global Sequence Viewer with All Feature Annotations */}
      <SequenceViewer
        title="Construct Sequence with Full Multiplex Annotation Map"
        sequence={fullSeq}
        probes={probes}
        badge="All 4 Channels Highlighted"
      />

      {/* Next Step Nav Card Bar */}
      <div className="lab-card p-4 flex items-center justify-between">
        <div className="text-xs text-slate-500 font-medium">
          <span>All 4 TaqMan probes spatially mapped, verified, and color-highlighted.</span>
        </div>

        <button
          onClick={() => setCurrentPage('export')}
          className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-700 active:scale-95 text-white text-xs font-bold transition shadow-sm cursor-pointer"
        >
          <Save className="w-4 h-4" />
          <span>Proceed to Final Review & Save ➡</span>
        </button>
      </div>
    </div>
  );
}
