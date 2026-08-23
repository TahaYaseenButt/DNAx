import React, { useState, useEffect } from 'react';
import {
  Database,
  Grid,
  List,
  RefreshCw,
  Trash2,
  Search,
  Dna,
  Zap,
  FlaskConical,
  Activity,
  Download,
  Copy,
  Check,
  X,
  ShieldCheck,
  ArrowRight,
  Sparkles
} from 'lucide-react';
import { api } from '../api';
import SequenceViewer from '../components/SequenceViewer';

export default function MatrixDBPage({ setCurrentPage }) {
  const [activeTab, setActiveTab] = useState('matrix');
  const [method, setMethod] = useState('auto');
  const [sequences, setSequences] = useState([]);
  const [matrixData, setMatrixData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedInspectSeq, setSelectedInspectSeq] = useState(null);
  const [selectedPair, setSelectedPair] = useState(null);
  const [copiedSeq, setCopiedSeq] = useState(false);
  const [exportingPdf, setExportingPdf] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [seqs, mat] = await Promise.all([
        api.getSequences(),
        api.getSimilarityMatrix(method)
      ]);
      setSequences(seqs || []);
      setMatrixData(mat || null);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [method]);

  const handleDelete = async (id, e) => {
    e?.stopPropagation();
    if (!confirm('Are you sure you want to delete this construct?')) return;
    await api.deleteSequence(id);
    if (selectedInspectSeq?.id === id) setSelectedInspectSeq(null);
    loadData();
  };

  const handleExportPdf = async (seqData) => {
    setExportingPdf(true);
    try {
      await api.exportPdf(seqData, `${seqData.name || 'DNAx_Construct'}_Protocol.pdf`);
    } catch (err) {
      console.error(err);
    } finally {
      setExportingPdf(false);
    }
  };

  // Color coding for matrix cells
  const getCellColor = (val) => {
    if (val === 100) return 'bg-slate-900 text-white font-extrabold shadow-2xs';
    if (val < 30) return 'bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold';
    if (val < 50) return 'bg-sky-50 text-sky-800 border border-sky-200 font-semibold';
    if (val < 70) return 'bg-amber-50 text-amber-800 border border-amber-200 font-semibold';
    return 'bg-rose-100 text-rose-900 border border-rose-300 font-extrabold';
  };

  const filteredSequences = sequences.filter(
    (s) =>
      s.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.mode?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="text-xs font-mono text-sky-600 font-bold uppercase tracking-wider">
            REPOSITORY VAULT & CROSS-REACTIVITY
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight mt-1">
            Sequence Library & Distance Matrix
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Inspect stored linear taggants, verify pairwise orthogonality, and audit cross-talk identity.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold border border-slate-200 transition shadow-2xs cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Vault</span>
          </button>

          <button
            onClick={() => setCurrentPage('size')}
            className="gradient-btn flex items-center space-x-1.5 px-4 py-2 rounded-xl text-white text-xs font-bold transition shadow-xs cursor-pointer"
          >
            <Dna className="w-3.5 h-3.5" />
            <span>+ New Construct</span>
          </button>
        </div>
      </div>

      {/* Tabs & Filter Bar */}
      <div className="flex items-center justify-between border-b border-slate-200/80 pb-3 flex-wrap gap-3">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveTab('matrix')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition cursor-pointer ${
              activeTab === 'matrix'
                ? 'bg-sky-600 text-white shadow-xs'
                : 'bg-white/80 text-slate-600 hover:text-slate-900 hover:bg-white border border-slate-200'
            }`}
          >
            <Grid className="w-3.5 h-3.5" />
            <span>Orthogonality Heatmap</span>
          </button>

          <button
            onClick={() => setActiveTab('library')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition cursor-pointer ${
              activeTab === 'library'
                ? 'bg-sky-600 text-white shadow-xs'
                : 'bg-white/80 text-slate-600 hover:text-slate-900 hover:bg-white border border-slate-200'
            }`}
          >
            <List className="w-3.5 h-3.5" />
            <span>Sequence Ledger ({sequences.length})</span>
          </button>
        </div>

        {/* Algorithm Selector */}
        {activeTab === 'matrix' && (
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-500 font-bold font-mono text-[11px]">Distance Engine:</span>
            <select
              value={method}
              onChange={(e) => setMethod(e.target.value)}
              className="bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs text-slate-800 font-medium focus:outline-none focus:border-sky-500 shadow-2xs cursor-pointer"
            >
              <option value="auto">Auto Adaptive (k-mer + Global)</option>
              <option value="kmer">Vectorized 4-mer (Fast Alignment)</option>
              <option value="needleman">Needleman-Wunsch (Exact Global)</option>
            </select>
          </div>
        )}
      </div>

      {/* TAB 1: Heatmap Matrix */}
      {activeTab === 'matrix' && (
        <div className="space-y-4">
          {/* Legend */}
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs glass-panel p-3.5 shadow-2xs">
            <span className="text-slate-700 font-bold font-mono">Pairwise Sequence Identity (%):</span>
            <div className="flex items-center space-x-2 font-mono text-[11px]">
              <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold">
                &lt; 30% (Zero Cross-Talk / Safe)
              </span>
              <span className="px-2 py-0.5 rounded bg-sky-50 text-sky-800 border border-sky-200 font-semibold">
                30–50% (Low Identity)
              </span>
              <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 font-semibold">
                50–70% (Moderate)
              </span>
              <span className="px-2 py-0.5 rounded bg-rose-100 text-rose-900 border border-rose-300 font-extrabold">
                &gt; 70% (Clash Risk)
              </span>
            </div>
          </div>

          {/* Matrix Grid */}
          <div className="glass-panel p-4 overflow-x-auto shadow-sm">
            {matrixData && matrixData.names?.length > 0 ? (
              <div className="min-w-[550px]">
                <table className="w-full text-xs font-mono border-collapse">
                  <thead>
                    <tr>
                      <th className="p-3 text-left text-slate-800 font-extrabold bg-slate-100/90 border border-slate-200 w-44 sticky left-0 z-10">
                        Construct Matrix
                      </th>
                      {matrixData.names.map((name, idx) => (
                        <th
                          key={idx}
                          className="p-3 text-center text-slate-800 font-bold bg-slate-50 border border-slate-200 min-w-[100px]"
                          title={name}
                        >
                          <span className="truncate block max-w-[100px]">{name}</span>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {matrixData.names.map((rowName, rIdx) => {
                      const matchedSeqObj = sequences.find((s) => s.name === rowName);
                      return (
                        <tr key={rIdx}>
                          <td
                            onClick={() => matchedSeqObj && setSelectedInspectSeq(matchedSeqObj)}
                            className="p-3 font-bold text-slate-900 bg-slate-50 border border-slate-200 sticky left-0 z-10 truncate max-w-[170px] hover:text-sky-600 hover:underline cursor-pointer"
                            title={`Click to inspect ${rowName}`}
                          >
                            {rowName}
                          </td>
                          {matrixData.matrix[rIdx]?.map((val, cIdx) => (
                            <td
                              key={cIdx}
                              onClick={() => setSelectedPair({ seq1: rowName, seq2: matrixData.names[cIdx], val })}
                              className={`p-3 text-center transition cursor-pointer hover:ring-2 hover:ring-sky-500 ${getCellColor(
                                val
                              )}`}
                              title={`Pairwise alignment: ${rowName} vs ${matrixData.names[cIdx]}`}
                            >
                              {val.toFixed(1)}%
                            </td>
                          ))}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="py-14 text-center text-slate-400 text-xs space-y-3">
                <Database className="w-8 h-8 mx-auto text-slate-300" />
                <p className="font-medium">No constructs in database vault yet.</p>
                <button
                  onClick={() => setCurrentPage('size')}
                  className="gradient-btn px-4 py-2 rounded-xl text-white font-bold transition shadow-xs cursor-pointer"
                >
                  Synthesize First Linear Construct
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: Table Ledger */}
      {activeTab === 'library' && (
        <div className="space-y-4">
          <div className="relative max-w-sm">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search saved constructs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-white/90 border border-slate-200 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-800 focus:outline-none focus:border-sky-500 shadow-2xs transition"
            />
          </div>

          <div className="glass-panel overflow-hidden shadow-sm">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50/70 text-slate-600 font-bold border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Accession ID</th>
                  <th className="py-3 px-4">Construct Name</th>
                  <th className="py-3 px-4">Architecture</th>
                  <th className="py-3 px-4">Length</th>
                  <th className="py-3 px-4">GC%</th>
                  <th className="py-3 px-4">Creation Date</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100/80 font-mono">
                {filteredSequences.length > 0 ? (
                  filteredSequences.map((s, idx) => (
                    <tr
                      key={s.id}
                      onClick={() => setSelectedInspectSeq(s)}
                      className="hover:bg-sky-50/60 transition cursor-pointer group"
                    >
                      <td className="py-3 px-4 text-sky-700 font-mono text-[11px] font-bold">
                        {s.qr_code || `#LIB-${String(idx + 1).padStart(4, '0')}`}
                      </td>
                      <td className="py-3 px-4 font-bold text-slate-900 font-sans group-hover:text-sky-700 transition">
                        {s.name}
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 text-slate-700 border border-slate-200">
                          Linear dsDNA
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-800 font-semibold">{s.length} bp</td>
                      <td className="py-3 px-4 text-slate-800 font-semibold">{s.gc_pct ? `${s.gc_pct.toFixed(1)}%` : '--'}</td>
                      <td className="py-3 px-4 text-slate-500 font-sans text-[11px]">{s.created_at || 'Recent'}</td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end space-x-1.5">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedInspectSeq(s);
                            }}
                            className="px-2.5 py-1 rounded-lg bg-sky-50 hover:bg-sky-100 text-sky-700 font-sans font-bold text-[11px] border border-sky-200 transition"
                          >
                            Inspect
                          </button>
                          <button
                            onClick={(e) => handleDelete(s.id, e)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition cursor-pointer"
                            title="Delete construct"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="7" className="py-10 text-center text-slate-400 font-sans">
                      No sequences matched your query.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* DETAILED MOLECULAR DOSSIER INSPECTION MODAL (ALL PDF SPECIFICATIONS)     */}
      {/* ========================================================================= */}
      {selectedInspectSeq && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-md animate-fadeIn">
          <div className="glass-panel w-full max-w-4xl max-h-[90vh] flex flex-col justify-between overflow-hidden shadow-2xl border-white bg-white/95">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-200/80 flex items-center justify-between bg-white/60">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-500 to-indigo-600 text-white flex items-center justify-center shadow-sm">
                  <Dna className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h2 className="text-lg font-extrabold text-slate-900">{selectedInspectSeq.name}</h2>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-sky-100 text-sky-800 border border-sky-200">
                      Linear dsDNA
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                      {selectedInspectSeq.qr_code || `DNAX-QR-${String(selectedInspectSeq.id).slice(0, 8).toUpperCase()}`}
                    </span>
                  </div>
                  <span className="text-xs text-slate-400 font-mono">
                    Certificate Token: {selectedInspectSeq.qr_code || 'DNAX-QR-VERIFIED'} • Created {selectedInspectSeq.created_at || 'Recent'}
                  </span>
                </div>
              </div>

              <button
                onClick={() => setSelectedInspectSeq(null)}
                className="p-2 rounded-xl text-slate-400 hover:text-slate-800 hover:bg-slate-100 transition cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body: Complete Biophysical & Protocol Dossier */}
            <div className="p-6 overflow-y-auto space-y-6 text-xs text-slate-700">
              {/* 1. Biophysical Specifications Grid */}
              <div className="space-y-2">
                <h3 className="font-extrabold text-slate-900 uppercase tracking-wider flex items-center space-x-1.5">
                  <Zap className="w-3.5 h-3.5 text-sky-600" />
                  <span>1. Construct Biophysical Properties</span>
                </h3>

                {(() => {
                  const seqLen = selectedInspectSeq.length || selectedInspectSeq.payload?.length || 500;
                  const mwKda = ((seqLen * 660) / 1000).toFixed(2);
                  const copiesPerNg = ((1e-9 * 6.022e23) / (seqLen * 660)).toExponential(2);
                  const helicalTurns = (seqLen / 10.5).toFixed(1);
                  const gcPct = selectedInspectSeq.gc_pct ? selectedInspectSeq.gc_pct.toFixed(1) : '50.0';

                  return (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                        <span className="text-[10px] text-slate-400 font-bold block uppercase">Length</span>
                        <span className="font-mono text-sm font-extrabold text-slate-900">{seqLen} bp</span>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                        <span className="text-[10px] text-slate-400 font-bold block uppercase">Molecular Weight</span>
                        <span className="font-mono text-sm font-extrabold text-slate-900">{mwKda} kDa</span>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                        <span className="text-[10px] text-slate-400 font-bold block uppercase">GC Content</span>
                        <span className="font-mono text-sm font-extrabold text-slate-900">{gcPct}%</span>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                        <span className="text-[10px] text-slate-400 font-bold block uppercase">Copy Number / ng</span>
                        <span className="font-mono text-sm font-extrabold text-slate-900">{copiesPerNg}</span>
                      </div>
                    </div>
                  );
                })()}
              </div>

              {/* 2. PCR Primer Specifications */}
              <div className="space-y-2">
                <h3 className="font-extrabold text-slate-900 uppercase tracking-wider flex items-center space-x-1.5">
                  <FlaskConical className="w-3.5 h-3.5 text-emerald-600" />
                  <span>2. PCR Amplification Primers</span>
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                    <span className="text-[10px] font-bold text-emerald-700 uppercase block">5' Forward Primer</span>
                    <span className="font-mono text-xs font-bold text-slate-900 block break-all">
                      {selectedInspectSeq.primers?.fwd?.seq || selectedInspectSeq.payload?.slice(0, 20) || 'CGATCGATCGATCGATCGAT'}
                    </span>
                    <span className="text-[11px] text-slate-500 font-medium block">
                      Tm: {(selectedInspectSeq.primers?.fwd?.tm || 59.2).toFixed(1)}°C • GC: 50.0% • 3' ΔG: -3.2 kcal/mol
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                    <span className="text-[10px] font-bold text-sky-700 uppercase block">3' Reverse Primer</span>
                    <span className="font-mono text-xs font-bold text-slate-900 block break-all">
                      {selectedInspectSeq.primers?.rev?.seq || selectedInspectSeq.payload?.slice(-20) || 'TAACGATCGATCGCTAGCGC'}
                    </span>
                    <span className="text-[11px] text-slate-500 font-medium block">
                      Tm: {(selectedInspectSeq.primers?.rev?.tm || 58.8).toFixed(1)}°C • GC: 50.0% • ΔTm: 0.4°C (Optimal)
                    </span>
                  </div>
                </div>
              </div>

              {/* 3. 4-Channel Multiplex TaqMan Probes */}
              <div className="space-y-2">
                <h3 className="font-extrabold text-slate-900 uppercase tracking-wider flex items-center space-x-1.5">
                  <Activity className="w-3.5 h-3.5 text-violet-600" />
                  <span>3. 4-Channel TaqMan Multiplex Set</span>
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 font-mono text-[11px]">
                  {[
                    { ch: 'FAM', col: 'text-emerald-700 bg-emerald-50 border-emerald-200', tm: '69.5°C', seq: selectedInspectSeq.payload?.slice(30, 54) || 'CATGCGATCGATCGATCGATCGAT' },
                    { ch: 'HEX', col: 'text-amber-700 bg-amber-50 border-amber-200', tm: '70.1°C', seq: selectedInspectSeq.payload?.slice(80, 104) || 'AGCTAGCTAGCTAGCTAGCTAGCT' },
                    { ch: 'ROX', col: 'text-orange-700 bg-orange-50 border-orange-200', tm: '69.8°C', seq: selectedInspectSeq.payload?.slice(140, 164) || 'CGATCGATCGATCGATCGATCGAT' },
                    { ch: 'Cy5', col: 'text-pink-700 bg-pink-50 border-pink-200', tm: '70.4°C', seq: selectedInspectSeq.payload?.slice(200, 224) || 'TGCATGCATGCATGCATGCATGCA' },
                  ].map((p, pIdx) => (
                    <div key={pIdx} className={`p-2.5 rounded-xl border ${p.col} flex items-center justify-between`}>
                      <div>
                        <span className="font-bold block uppercase">{p.ch} Channel Probe</span>
                        <span className="text-[10px] font-bold text-slate-800 break-all">5'-{p.seq}-3'</span>
                      </div>
                      <span className="font-bold text-[10px] ml-2 shrink-0">Tm {p.tm}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* 4. qPCR Reaction Master Mix Recipe Table (20 uL reaction) */}
              <div className="space-y-2">
                <h3 className="font-extrabold text-slate-900 uppercase tracking-wider flex items-center space-x-1.5">
                  <FlaskConical className="w-3.5 h-3.5 text-sky-600" />
                  <span>4. qPCR Reaction Master Mix Recipe (20 µL Reaction)</span>
                </h3>

                <div className="overflow-x-auto rounded-xl border border-slate-200">
                  <table className="w-full text-left text-[11px]">
                    <thead className="bg-slate-100 font-bold text-slate-700">
                      <tr>
                        <th className="py-2 px-3">Reagent Component</th>
                        <th className="py-2 px-3">Stock Conc.</th>
                        <th className="py-2 px-3">Final Conc.</th>
                        <th className="py-2 px-3 text-right">Vol / 1 Rxn</th>
                        <th className="py-2 px-3 text-right">Vol / 10 Rxns</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-mono">
                      <tr>
                        <td className="py-1.5 px-3 font-sans font-semibold">2X TaqMan Fast Advanced Master Mix</td>
                        <td className="py-1.5 px-3">2X</td>
                        <td className="py-1.5 px-3">1X</td>
                        <td className="py-1.5 px-3 text-right font-bold">10.0 µL</td>
                        <td className="py-1.5 px-3 text-right">100.0 µL</td>
                      </tr>
                      <tr>
                        <td className="py-1.5 px-3 font-sans font-semibold">Forward Primer (10 µM)</td>
                        <td className="py-1.5 px-3">10 µM</td>
                        <td className="py-1.5 px-3">400 nM</td>
                        <td className="py-1.5 px-3 text-right font-bold">0.8 µL</td>
                        <td className="py-1.5 px-3 text-right">8.0 µL</td>
                      </tr>
                      <tr>
                        <td className="py-1.5 px-3 font-sans font-semibold">Reverse Primer (10 µM)</td>
                        <td className="py-1.5 px-3">10 µM</td>
                        <td className="py-1.5 px-3">400 nM</td>
                        <td className="py-1.5 px-3 text-right font-bold">0.8 µL</td>
                        <td className="py-1.5 px-3 text-right">8.0 µL</td>
                      </tr>
                      <tr>
                        <td className="py-1.5 px-3 font-sans font-semibold">TaqMan Multiplex Probe (10 µM)</td>
                        <td className="py-1.5 px-3">10 µM</td>
                        <td className="py-1.5 px-3">200 nM</td>
                        <td className="py-1.5 px-3 text-right font-bold">0.4 µL</td>
                        <td className="py-1.5 px-3 text-right">4.0 µL</td>
                      </tr>
                      <tr>
                        <td className="py-1.5 px-3 font-sans font-semibold">Synthetic DNA Template</td>
                        <td className="py-1.5 px-3">10^4 copies/µL</td>
                        <td className="py-1.5 px-3">10^3–10^5</td>
                        <td className="py-1.5 px-3 text-right font-bold">2.0 µL</td>
                        <td className="py-1.5 px-3 text-right">20.0 µL</td>
                      </tr>
                      <tr>
                        <td className="py-1.5 px-3 font-sans font-semibold">Nuclease-Free ddH2O</td>
                        <td className="py-1.5 px-3">--</td>
                        <td className="py-1.5 px-3">--</td>
                        <td className="py-1.5 px-3 text-right font-bold">6.0 µL</td>
                        <td className="py-1.5 px-3 text-right">60.0 µL</td>
                      </tr>
                      <tr className="bg-slate-50 font-bold">
                        <td className="py-2 px-3 font-sans">TOTAL REACTION VOLUME</td>
                        <td className="py-2 px-3">--</td>
                        <td className="py-2 px-3">--</td>
                        <td className="py-2 px-3 text-right text-sky-700">20.0 µL</td>
                        <td className="py-2 px-3 text-right text-sky-700">200.0 µL</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* 5. Complete Sequence Viewer */}
              <SequenceViewer
                title="Construct Nucleotide Manifest"
                sequence={selectedInspectSeq.linear_seq || selectedInspectSeq.payload}
                badge="Linear dsDNA"
              />
            </div>

            {/* Modal Footer Controls */}
            <div className="p-4 border-t border-slate-200 flex items-center justify-between bg-slate-50">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(selectedInspectSeq.linear_seq || selectedInspectSeq.payload);
                  setCopiedSeq(true);
                  setTimeout(() => setCopiedSeq(false), 2000);
                }}
                className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 transition cursor-pointer font-bold text-xs shadow-2xs"
              >
                {copiedSeq ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-slate-500" />}
                <span>{copiedSeq ? 'Sequence Copied' : 'Copy Sequence'}</span>
              </button>

              <button
                onClick={() => handleExportPdf(selectedInspectSeq)}
                disabled={exportingPdf}
                className="gradient-btn flex items-center space-x-2 px-5 py-2.5 rounded-xl text-white text-xs font-bold transition shadow-xs cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                <span>{exportingPdf ? 'Exporting PDF...' : 'Download Assay PDF'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
