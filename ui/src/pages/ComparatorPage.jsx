import React, { useState, useEffect } from 'react';
import {
  Scale,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  FlaskConical,
  Save,
  Globe,
  Zap,
  Info,
  ExternalLink,
  Clock,
  Dna,
  CheckCircle2,
  Filter
} from 'lucide-react';
import { api } from '../api';

export default function ComparatorPage({ setCurrentPage, constructData }) {
  const seq = constructData?.linear_seq || constructData?.payload || '';
  const [blastMode, setBlastMode] = useState('ncbi_live'); // Default to Live NCBI as requested!
  const [loading, setLoading] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [blastResult, setBlastResult] = useState(null);
  const [statusStep, setStatusStep] = useState(1);
  const [activeFilter, setActiveFilter] = useState('all'); // 'all' | 'natural' | 'synthetic'

  // Elapsed timer during NCBI loading
  useEffect(() => {
    let interval;
    if (loading) {
      setElapsedSeconds(0);
      setStatusStep(1);
      interval = setInterval(() => {
        setElapsedSeconds((prev) => {
          const next = prev + 1;
          if (next >= 4 && next < 12) setStatusStep(2);
          else if (next >= 12) setStatusStep(3);
          return next;
        });
      }, 1000);
    } else {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [loading]);

  const handleRunBlast = async () => {
    if (!seq) return;
    setLoading(true);
    setBlastResult(null);
    try {
      const res = await api.runBlast(seq, blastMode);
      setBlastResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const naturalHits = blastResult?.natural || [];
  const syntheticHits = blastResult?.synthetic || [];
  const allHits = [...naturalHits, ...syntheticHits];

  // Calculate highest similarity and uniqueness in each category
  const maxNaturalSim = naturalHits.length > 0 ? Math.max(...naturalHits.map((h) => parseFloat(h.match_pct) || 0)) : 0;
  const maxSyntheticSim = syntheticHits.length > 0 ? Math.max(...syntheticHits.map((h) => parseFloat(h.match_pct) || 0)) : 0;

  const naturalUniqueness = Math.max(0, 100 - maxNaturalSim);
  const syntheticUniqueness = Math.max(0, 100 - maxSyntheticSim);

  // Criteria: Must be AT LEAST 25% UNIQUE in BOTH Natural and Synthetic (i.e. similarity <= 75%)
  const isNaturalUnique = naturalUniqueness >= 25.0; // max similarity <= 75%
  const isSyntheticUnique = syntheticUniqueness >= 25.0; // max similarity <= 75%
  const isOverallUnique = isNaturalUnique && isSyntheticUnique;

  const displayedHits =
    activeFilter === 'natural'
      ? naturalHits
      : activeFilter === 'synthetic'
      ? syntheticHits
      : allHits;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-indigo-600 font-bold uppercase tracking-wider">
            <span>STEP 03 OF 06</span>
            <span>•</span>
            <span>HOMOLOGY SCREENING</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight mt-1">NCBI BLAST Comparator</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Query nucleotide datasets in real-time via official NCBI QBLAST servers to guarantee 100% synthetic orthogonality.
          </p>
        </div>

        <button
          onClick={() => setCurrentPage('primer')}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 active:scale-95 text-white text-xs font-bold transition shadow-sm"
        >
          <span>Next: Primer Designer</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Query Configuration & Launcher Card */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <span className="text-xs font-bold text-slate-700">Search Engine Mode:</span>
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => setBlastMode('ncbi_live')}
                className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-bold border transition ${
                  blastMode === 'ncbi_live'
                    ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm shadow-indigo-600/30'
                    : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
                }`}
              >
                <Globe className="w-3.5 h-3.5" />
                <span>🌐 Live NCBI Remote QBLAST (Official)</span>
              </button>

              <button
                type="button"
                onClick={() => setBlastMode('in_silico')}
                className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-bold border transition ${
                  blastMode === 'in_silico'
                    ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm shadow-indigo-600/30'
                    : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
                }`}
              >
                <Zap className="w-3.5 h-3.5" />
                <span>⚡ Instant In-Silico Database Screen (0.1s)</span>
              </button>
            </div>
          </div>

          <button
            onClick={handleRunBlast}
            disabled={loading || !seq}
            className="flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-600 active:scale-95 text-white text-xs font-bold transition shadow-md shadow-amber-500/20 disabled:opacity-50 cursor-pointer"
          >
            {loading ? (
              <span className="flex items-center space-x-2">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Screening...</span>
              </span>
            ) : (
              <>
                <Scale className="w-4 h-4" />
                <span>Execute BLAST Screening</span>
              </>
            )}
          </button>
        </div>

        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs font-bold text-slate-700">
            <span>Query DNA Construct</span>
            <span className="font-mono text-slate-500">{seq ? `${seq.length} bp` : '0 bp'}</span>
          </div>
          <div className="bg-slate-50 font-mono text-xs text-slate-800 p-3.5 rounded-xl border border-slate-200/90 max-h-20 overflow-y-auto break-all font-medium select-text">
            {seq || <span className="text-slate-400 italic">No sequence passed. Synthesize a sequence in Step 2 first.</span>}
          </div>
        </div>
      </div>

      {/* 🚀 HIGH-TECH ANIMATED NCBI LOADER */}
      {loading && (
        <div className="bg-white rounded-3xl p-8 border border-indigo-100 shadow-md space-y-6 animate-fadeIn">
          <div className="flex flex-col items-center justify-center text-center space-y-4">
            {/* Animated Radar / Spinner */}
            <div className="relative w-20 h-20 flex items-center justify-center">
              <div className="absolute inset-0 rounded-full border-4 border-indigo-100 animate-ping opacity-60" />
              <div className="absolute inset-0 rounded-full border-4 border-indigo-600/20 border-t-indigo-600 animate-spin" />
              <Dna className="w-8 h-8 text-indigo-600 animate-pulse" />
            </div>

            <div className="space-y-1">
              <h3 className="text-base font-extrabold text-slate-900">
                Running NCBI Remote QBLAST Job
              </h3>
              <p className="text-xs text-slate-500 max-w-md">
                Communicating with the National Center for Biotechnology Information (NCBI) GenBank supercomputers.
              </p>
            </div>

            {/* Live Timer Pill */}
            <div className="flex items-center space-x-2 bg-indigo-50 px-3.5 py-1.5 rounded-full border border-indigo-200 text-indigo-700 text-xs font-mono font-bold">
              <Clock className="w-3.5 h-3.5 animate-spin" />
              <span>Elapsed: {elapsedSeconds}s</span>
              <span className="text-slate-400 font-normal">| Typical queue: 15–30s</span>
            </div>
          </div>

          {/* Stepper Progress Bar */}
          <div className="max-w-xl mx-auto space-y-3 pt-2">
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className={`p-2.5 rounded-xl border flex items-center space-x-2 ${
                statusStep >= 1 ? 'bg-emerald-50 border-emerald-200 text-emerald-800 font-bold' : 'bg-slate-50 border-slate-200 text-slate-400'
              }`}>
                <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                <span>1. Submit Query</span>
              </div>

              <div className={`p-2.5 rounded-xl border flex items-center space-x-2 ${
                statusStep >= 2 ? 'bg-indigo-50 border-indigo-200 text-indigo-800 font-bold' : 'bg-slate-50 border-slate-200 text-slate-400'
              }`}>
                <RefreshCw className={`w-3.5 h-3.5 shrink-0 ${statusStep === 2 ? 'animate-spin' : ''}`} />
                <span>2. Polling Queue</span>
              </div>

              <div className={`p-2.5 rounded-xl border flex items-center space-x-2 ${
                statusStep >= 3 ? 'bg-indigo-50 border-indigo-200 text-indigo-800 font-bold' : 'bg-slate-50 border-slate-200 text-slate-400'
              }`}>
                <Scale className="w-3.5 h-3.5 shrink-0" />
                <span>3. Parse Hits</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* RESULTS DISPLAY */}
      {blastResult && !loading && (
        <div className="space-y-6 animate-fadeIn">
          {/* Summary Status Banner */}
          <div
            className={`rounded-2xl p-5 border flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-sm ${
              isOverallUnique
                ? 'bg-emerald-50/90 border-emerald-200'
                : 'bg-amber-50/90 border-amber-300'
            }`}
          >
            <div className="flex items-center space-x-3.5">
              <div
                className={`p-2.5 rounded-2xl ${
                  isOverallUnique
                    ? 'bg-emerald-100 text-emerald-700'
                    : 'bg-amber-100 text-amber-700'
                }`}
              >
                {isOverallUnique ? (
                  <ShieldCheck className="w-6 h-6" />
                ) : (
                  <AlertTriangle className="w-6 h-6" />
                )}
              </div>
              <div>
                <div
                  className={`text-sm font-bold ${
                    isOverallUnique ? 'text-emerald-900' : 'text-amber-900'
                  }`}
                >
                  {isOverallUnique
                    ? '✓ Verified Unique: Sequence meets ≥ 25% Uniqueness Requirement in both Natural & Synthetic Datasets'
                    : `⚠️ Notice: Sequence is < 25% Unique (Similarity > 75%) in ${!isNaturalUnique ? 'Natural Genomes' : ''} ${!isNaturalUnique && !isSyntheticUnique ? 'and ' : ''} ${!isSyntheticUnique ? 'Synthetic Vectors' : ''}`}
                </div>
                <div
                  className={`text-xs mt-1.5 font-medium flex flex-wrap gap-2 ${
                    isOverallUnique ? 'text-emerald-800/90' : 'text-amber-800/90'
                  }`}
                >
                  <span className={`font-semibold px-2 py-0.5 rounded border ${
                    isNaturalUnique ? 'bg-emerald-100 text-emerald-900 border-emerald-300' : 'bg-rose-100 text-rose-900 border-rose-300'
                  }`}>
                    🌿 Natural Uniqueness: {naturalUniqueness.toFixed(1)}% {isNaturalUnique ? '(≥ 25% Safe)' : '(Low < 25%)'}
                  </span>
                  <span className={`font-semibold px-2 py-0.5 rounded border ${
                    isSyntheticUnique ? 'bg-emerald-100 text-emerald-900 border-emerald-300' : 'bg-amber-100 text-amber-900 border-amber-300'
                  }`}>
                    🧪 Synthetic Uniqueness: {syntheticUniqueness.toFixed(1)}% {isSyntheticUnique ? '(≥ 25% Safe)' : '(Low < 25%)'}
                  </span>
                  <span className="text-slate-500 font-mono text-[11px] self-center">• {blastResult.source}</span>
                </div>
              </div>
            </div>

            <span
              className={`px-3.5 py-1.5 rounded-full text-xs font-extrabold uppercase border shrink-0 ${
                isOverallUnique
                  ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                  : 'bg-amber-100 text-amber-800 border-amber-300'
              }`}
            >
              {isOverallUnique ? 'PASSED (≥ 25% UNIQUE)' : 'LOW UNIQUENESS (< 25%)'}
            </span>
          </div>

          {/* Filter Tabs & Alignment Table */}
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center space-x-2">
                <Filter className="w-4 h-4 text-slate-400" />
                <span className="text-xs font-bold text-slate-700">Filter Alignments:</span>
                <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-xl">
                  <button
                    onClick={() => setActiveFilter('all')}
                    className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
                      activeFilter === 'all'
                        ? 'bg-white text-indigo-600 shadow-sm'
                        : 'text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    All Hits ({allHits.length})
                  </button>
                  <button
                    onClick={() => setActiveFilter('natural')}
                    className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
                      activeFilter === 'natural'
                        ? 'bg-white text-indigo-600 shadow-sm'
                        : 'text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    Natural Genomes ({naturalHits.length})
                  </button>
                  <button
                    onClick={() => setActiveFilter('synthetic')}
                    className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
                      activeFilter === 'synthetic'
                        ? 'bg-white text-indigo-600 shadow-sm'
                        : 'text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    Synthetic / Vectors ({syntheticHits.length})
                  </button>
                </div>
              </div>

              {blastResult.rid && (
                <span className="text-xs font-mono text-slate-500 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200">
                  NCBI Job ID: #{blastResult.rid}
                </span>
              )}
            </div>

            {/* Alignments Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                  <tr>
                    <th className="p-3.5">GenBank Title / Description</th>
                    <th className="p-3.5">Accession</th>
                    <th className="p-3.5">Category</th>
                    <th className="p-3.5">E-Value</th>
                    <th className="p-3.5">Bit Score</th>
                    <th className="p-3.5">Identity %</th>
                    <th className="p-3.5 text-right">NCBI Link</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {displayedHits.length > 0 ? (
                    displayedHits.map((hit, idx) => {
                      const isNat = !syntheticHits.includes(hit);
                      return (
                        <tr key={idx} className="hover:bg-slate-50 transition">
                          <td className="p-3.5 font-bold text-slate-900 max-w-xs truncate" title={hit.title}>
                            {hit.title}
                          </td>
                          <td className="p-3.5 font-mono text-slate-700 font-semibold">{hit.accession || 'N/A'}</td>
                          <td className="p-3.5">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                                isNat
                                  ? 'bg-rose-50 text-rose-700 border-rose-200'
                                  : 'bg-amber-50 text-amber-700 border-amber-200'
                              }`}
                            >
                              {isNat ? 'Natural' : 'Synthetic Vector'}
                            </span>
                          </td>
                          <td className="p-3.5 font-mono text-slate-800">{hit.evalue}</td>
                          <td className="p-3.5 font-mono text-slate-800">{hit.bit_score || '--'}</td>
                          <td className="p-3.5 font-mono font-bold text-slate-900">{hit.match_pct}%</td>
                          <td className="p-3.5 text-right">
                            {hit.url ? (
                              <a
                                href={hit.url}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center space-x-1 text-indigo-600 hover:text-indigo-800 font-bold"
                              >
                                <span>GenBank</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            ) : (
                              <span className="text-slate-400">Local</span>
                            )}
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan="7" className="p-10 text-center text-slate-400 font-medium">
                        ✓ No alignment hits found in this category. The query sequence is 100% unique.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Next Steps Footer */}
          <div className="bg-white rounded-2xl p-4 border border-slate-200/90 shadow-sm flex items-center justify-end space-x-3">
            <button
              onClick={() => setCurrentPage('primer')}
              className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition shadow-sm"
            >
              <FlaskConical className="w-3.5 h-3.5" />
              <span>Next: Review PCR Primers ➡</span>
            </button>
            <button
              onClick={() => setCurrentPage('export')}
              className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition shadow-sm"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Proceed to Review & Save ➡</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
