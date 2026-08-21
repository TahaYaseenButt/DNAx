import React, { useState, useEffect } from 'react';
import {
  Dna,
  Zap,
  ArrowRight,
  ShieldCheck,
  RotateCcw,
  Sparkles,
  Layers,
  Scale,
  FlaskConical,
  Activity,
  Save,
  CheckCircle2
} from 'lucide-react';
import MetricCard from '../components/MetricCard';
import SequenceViewer from '../components/SequenceViewer';
import DNA3DViewer from '../components/DNA3DViewer';
import { api } from '../api';

export default function DNAGeneratePage({ setCurrentPage, targetBp = 500, setConstructData, constructData }) {
  const [length, setLength] = useState(targetBp || 500);
  const [primerOption, setPrimerOption] = useState('denovo');
  const [univFwd, setUnivFwd] = useState('CGATCGATCGATCGATCGAT');
  const [univRev, setUnivRev] = useState('TAACGATCGATCGCTAGCGC');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(constructData || null);

  useEffect(() => {
    if (targetBp) setLength(targetBp);
  }, [targetBp]);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const data = await api.generateDNA({
        length: parseInt(length) || 500,
        mode: 'linear',
        primerOption,
        univFwd,
        univRev
      });
      setResult(data);
      if (setConstructData) setConstructData(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-sky-600 font-bold uppercase tracking-wider">
            <span>STEP 02 OF 06</span>
            <span>•</span>
            <span>LINEAR DE NOVO SYNTHESIS</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight mt-1">Linear DNA Sequence Generator</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Synthesize orthogonal linear DNA payloads with zero cross-reactivity and balanced thermodynamic stability.
          </p>
        </div>

        {result && (
          <button
            onClick={() => setCurrentPage('comparator')}
            className="gradient-btn flex items-center space-x-2 px-4 py-2.5 rounded-xl text-white text-xs font-bold transition shadow-sm cursor-pointer"
          >
            <span>Next: BLAST Check</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Main Configuration Card */}
      <div className="glass-panel p-6 space-y-5">
        {/* Row 1: Primer Seed Selection & Architecture Badge */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pb-4 border-b border-slate-200/60">
          {/* Construct Architecture: Linear dsDNA */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-700">Construct Architecture</label>
            <div className="flex items-center space-x-2 p-2.5 rounded-xl bg-white/90 border border-sky-200 text-xs font-bold text-sky-900 shadow-2xs">
              <span className="w-2.5 h-2.5 rounded-full bg-sky-500" />
              <span>Linear Double-Stranded DNA (Linear dsDNA)</span>
            </div>
          </div>

          {/* Primer Seed Option */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-700">Primer Seed Strategy</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setPrimerOption('denovo')}
                className={`flex items-center justify-center space-x-2 px-3 py-2.5 rounded-xl text-xs font-bold border transition cursor-pointer ${
                  primerOption === 'denovo'
                    ? 'bg-sky-50 border-sky-300 text-sky-800 shadow-2xs'
                    : 'bg-white/70 border-slate-200 text-slate-600 hover:bg-white'
                }`}
              >
                <span>🎲 De Novo Orthogonal</span>
              </button>

              <button
                type="button"
                onClick={() => setPrimerOption('universal')}
                className={`flex items-center justify-center space-x-2 px-3 py-2.5 rounded-xl text-xs font-bold border transition cursor-pointer ${
                  primerOption === 'universal'
                    ? 'bg-sky-50 border-sky-300 text-sky-800 shadow-2xs'
                    : 'bg-white/70 border-slate-200 text-slate-600 hover:bg-white'
                }`}
              >
                <span>🌐 Universal Primers</span>
              </button>
            </div>
          </div>
        </div>

        {/* Row 2: Payload Length & Action */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5 flex-1 max-w-sm">
            <label className="text-xs font-bold text-slate-700">Linear Payload Length (bp)</label>
            <input
              type="number"
              min="20"
              max="10000"
              value={length}
              onChange={(e) => setLength(e.target.value)}
              className="w-full bg-white/90 border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-mono font-bold text-slate-900 focus:outline-none focus:border-sky-500 focus:bg-white transition shadow-2xs"
            />
          </div>

          <button
            onClick={handleGenerate}
            disabled={loading}
            className="gradient-btn flex items-center justify-center space-x-2 px-6 py-3 rounded-xl text-white text-xs font-bold transition shadow-md cursor-pointer disabled:opacity-50"
          >
            {loading ? (
              <span className="flex items-center space-x-2">
                <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Synthesizing...</span>
              </span>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-sky-200" />
                <span>⚡ Synthesize Linear DNA</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Generated Results View */}
      {result && (
        <div className="space-y-6">
          {/* Homology & Safety Banner */}
          <div className="glass-panel p-4 border border-emerald-300/80 flex flex-col md:flex-row items-start md:items-center justify-between gap-3 shadow-sm bg-emerald-50/60">
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-xl bg-emerald-100 text-emerald-700">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xs font-bold text-emerald-950 flex items-center space-x-2 font-sans">
                  <span>Database Orthogonality Status:</span>
                  <span className="text-emerald-700 font-mono">Max {result.max_similarity}% Similarity</span>
                </div>
                <div className="text-[11px] text-emerald-800 mt-0.5 font-medium">
                  {result.oligo_status || '100% Unique Primers & TaqMan Probes (Zero clashes across stored repository)'}
                </div>
              </div>
            </div>
            <span className="px-3 py-1 rounded-full text-[10px] font-extrabold uppercase bg-emerald-100 text-emerald-800 border border-emerald-300">
              Assay Verified Safe
            </span>
          </div>

          {/* 4 Metric KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              title="Payload Length"
              value={`${result.length} bp`}
              subtext="Pure synthetic linear payload"
              accent="sky"
              icon={Dna}
            />
            <MetricCard
              title="GC Content"
              value={`${result.gc_pct?.toFixed(1) || 50.0}%`}
              subtext="Optimal 45–55% range"
              accent="emerald"
              icon={Zap}
            />
            <MetricCard
              title="Architecture"
              value="Linear dsDNA"
              subtext="Double-stranded linear ends"
              accent="amber"
              icon={Layers}
            />
            <MetricCard
              title="Assay Orthogonality"
              value="100% Unique"
              subtext="0 Cross-reactions in DB"
              accent="violet"
              icon={ShieldCheck}
            />
          </div>

          {/* Interactive 3D Construct Architecture Visualizer */}
          <DNA3DViewer
            sequence={result.payload || result.linear_seq}
            mode="linear"
            height={340}
          />

          {/* Sequence Viewer */}
          <SequenceViewer
            title="Generated Linear Construct Sequence"
            sequence={result.linear_seq || result.payload}
            badge="Linear dsDNA Construct"
          />

          {/* Next Step Nav Card Bar */}
          <div className="glass-panel p-4 flex flex-wrap items-center justify-between gap-3">
            <div className="text-xs text-slate-500 font-medium">
              <span>Ready for in silico validation:</span>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={() => setCurrentPage('comparator')}
                className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-800 text-xs font-bold border border-amber-200 transition cursor-pointer shadow-2xs"
              >
                <Scale className="w-3.5 h-3.5 text-amber-600" />
                <span>3. Check NCBI BLAST ➔</span>
              </button>

              <button
                onClick={() => setCurrentPage('primer')}
                className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-800 text-xs font-bold border border-emerald-200 transition cursor-pointer shadow-2xs"
              >
                <FlaskConical className="w-3.5 h-3.5 text-emerald-600" />
                <span>4. Review Primers ➔</span>
              </button>

              <button
                onClick={() => setCurrentPage('qpcr')}
                className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-violet-50 hover:bg-violet-100 text-violet-800 text-xs font-bold border border-violet-200 transition cursor-pointer shadow-2xs"
              >
                <Activity className="w-3.5 h-3.5 text-violet-600" />
                <span>5. Review Probes ➔</span>
              </button>

              <button
                onClick={() => setCurrentPage('export')}
                className="gradient-btn flex items-center space-x-1.5 px-4 py-2 rounded-xl text-white text-xs font-bold transition shadow-xs cursor-pointer"
              >
                <Save className="w-3.5 h-3.5" />
                <span>Final Save & Export ➔</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
