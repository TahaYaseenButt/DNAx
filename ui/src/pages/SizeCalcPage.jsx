import React, { useState, useEffect } from 'react';
import { Ruler, ArrowRight, Zap, Copy, Check, Info, Layers } from 'lucide-react';
import MetricCard from '../components/MetricCard';
import { api } from '../api';

export default function SizeCalcPage({ setCurrentPage, setTargetBp }) {
  const [bpInput, setBpInput] = useState('500');
  const [metrics, setMetrics] = useState({
    linear_nm: 170,
    linear_um: 0.17,
    mw_da: 330000,
    mw_kda: 330,
    helical_turns: 47.6,
  });
  const [copied, setCopied] = useState(false);

  const calculate = async (val) => {
    const n = parseInt(val) || 0;
    if (n < 0) return;
    const res = await api.calculateSize(n);
    const helicalTurns = (n / 10.5).toFixed(1);
    setMetrics({ ...res, helical_turns: helicalTurns });
  };

  useEffect(() => {
    calculate(bpInput);
  }, [bpInput]);

  const handlePreset = (val) => {
    setBpInput(val.toString());
    calculate(val);
  };

  const handleUseInGen = () => {
    const n = parseInt(bpInput) || 500;
    if (setTargetBp) setTargetBp(n);
    setCurrentPage('dna');
  };

  const handleCopy = () => {
    const text = `Linear DNA Size & Biophysics (${bpInput} bp):\n• Physical Linear Length: ${metrics.linear_nm.toFixed(2)} nm (${metrics.linear_um.toFixed(4)} µm)\n• Helical B-DNA Turns: ${metrics.helical_turns} turns (10.5 bp/turn)\n• Molecular Weight: ${metrics.mw_da.toLocaleString()} Da (${metrics.mw_kda.toFixed(2)} kDa)\n• Mass Factor: 660.00 Da/bp (dsDNA)`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-sky-600 font-bold uppercase tracking-wider">
            <span>STEP 01 OF 06</span>
            <span>•</span>
            <span>LINEAR PHYSICAL SIZING</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight mt-1">Linear DNA Size & Mass Calculator</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Calculate physical length, helical pitch turns, and molecular mass for linear synthetic DNA taggants.
          </p>
        </div>

        <button
          onClick={handleUseInGen}
          className="gradient-btn flex items-center space-x-2 px-4 py-2.5 rounded-xl text-white text-xs font-bold transition shadow-sm cursor-pointer"
        >
          <span>Use in DNA Generator</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Input Configuration Card */}
      <div className="glass-panel p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5 flex-1 max-w-md">
            <label className="text-xs font-bold text-slate-700">Target Linear Length (Base Pairs)</label>
            <div className="relative">
              <input
                type="number"
                min="1"
                max="50000"
                value={bpInput}
                onChange={(e) => setBpInput(e.target.value)}
                placeholder="500"
                className="w-full bg-white/90 border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-mono font-bold text-slate-900 focus:outline-none focus:border-sky-500 focus:bg-white transition shadow-2xs"
              />
              <span className="absolute right-3.5 top-2.5 text-xs text-slate-400 font-mono font-medium">bp</span>
            </div>
          </div>

          {/* Presets */}
          <div className="space-y-1.5">
            <span className="text-xs font-bold text-slate-700 block">Quick Presets</span>
            <div className="flex flex-wrap gap-1.5">
              {[100, 250, 500, 1000, 2000, 5000].map((p) => (
                <button
                  key={p}
                  onClick={() => handlePreset(p)}
                  className={`text-xs px-3.5 py-1.5 rounded-xl border transition font-mono cursor-pointer ${
                    bpInput === p.toString()
                      ? 'bg-sky-600 text-white border-sky-600 font-bold shadow-xs'
                      : 'bg-white/80 text-slate-600 border-slate-200 hover:bg-white hover:text-slate-900'
                  }`}
                >
                  {p} bp
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 2x2 Glassmorphic Metric KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <MetricCard
          title="Physical Linear Length (B-DNA)"
          value={`${metrics.linear_nm.toFixed(2)} nm`}
          subtext={`${metrics.linear_um.toFixed(4)} µm  •  0.34 nm/base rise`}
          accent="sky"
          icon={Ruler}
        />
        <MetricCard
          title="B-DNA Helical Pitch Turns"
          value={`${metrics.helical_turns} Turns`}
          subtext="Based on canonical 10.5 base pairs per helical turn (3.4 nm pitch)"
          accent="emerald"
          icon={Layers}
        />
        <MetricCard
          title="Estimated Molecular Weight (dsDNA)"
          value={`${metrics.mw_kda.toFixed(2)} kDa`}
          subtext={`${metrics.mw_da.toLocaleString()} Daltons (g/mol)`}
          accent="violet"
          icon={Zap}
        />
        <MetricCard
          title="Average Mass Factor"
          value="660.00 Da / bp"
          subtext="Standard average mass per basepair for double-stranded DNA"
          accent="amber"
          icon={Info}
        />
      </div>

      {/* Bottom Actions */}
      <div className="flex items-center justify-between glass-panel p-4">
        <button
          onClick={handleCopy}
          className="flex items-center space-x-1.5 text-xs font-semibold px-3.5 py-2 rounded-xl bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition cursor-pointer shadow-2xs"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-slate-500" />}
          <span>{copied ? 'Copied Calculation' : 'Copy Metrics Summary'}</span>
        </button>

        <button
          onClick={handleUseInGen}
          className="gradient-btn flex items-center space-x-2 px-5 py-2.5 rounded-xl text-white text-xs font-bold transition shadow-xs cursor-pointer"
        >
          <span>Next: DNA Generator</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
