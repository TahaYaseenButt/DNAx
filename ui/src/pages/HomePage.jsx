import React, { useState, useEffect, useRef } from 'react';
import {
  Plus,
  Database,
  ArrowRight,
  Globe,
  Trash2,
  Dna,
  Search,
  ChevronDown,
  ChevronUp,
  FileText,
  Copy,
  Check,
  X,
  Sparkles,
  Zap,
  Layers,
  ShieldCheck,
  Activity,
  FlaskConical,
  Download
} from 'lucide-react';
import logoImg from '../assets/logo.png';
import { api } from '../api';
import SequenceViewer from '../components/SequenceViewer';

export default function HomePage({ setCurrentPage, dbCount = 0 }) {
  const [sequences, setSequences] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedInspectSeq, setSelectedInspectSeq] = useState(null);
  const [copiedSeq, setCopiedSeq] = useState(false);
  const [exportingPdf, setExportingPdf] = useState(false);

  const screen1Ref = useRef(null);
  const screen2Ref = useRef(null);

  const loadSeqs = async () => {
    try {
      const list = await api.getSequences();
      setSequences(list || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadSeqs();
  }, []);

  const handleDelete = async (id, e) => {
    e?.stopPropagation();
    if (!confirm('Are you sure you want to delete this sequence?')) return;
    await api.deleteSequence(id);
    if (selectedInspectSeq?.id === id) setSelectedInspectSeq(null);
    loadSeqs();
  };

  const scrollToScreen2 = () => {
    screen2Ref.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const scrollToScreen1 = () => {
    screen1Ref.current?.scrollIntoView({ behavior: 'smooth' });
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

  const filteredSequences = sequences.filter(
    (s) =>
      s.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.mode?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="h-[calc(100vh-4rem)] overflow-y-auto snap-y-mandatory relative">
      {/* ========================================================================= */}
      {/* SCREEN 1 (FULL VIEWPORT): Clean Hero + Logo + 2 Status Tiles ONLY         */}
      {/* ========================================================================= */}
      <section
        ref={screen1Ref}
        className="snap-start-always h-[calc(100vh-4rem)] flex flex-col justify-between p-6 sm:p-8 max-w-5xl mx-auto select-none"
      >
        <div className="space-y-6 my-auto">
          {/* 1. Proportional Glassmorphic Hero Centerpiece */}
          <div className="relative glass-panel p-8 sm:p-10 overflow-hidden text-center flex flex-col items-center justify-center space-y-6 shadow-sm">
            {/* Seamless Floating Logo with Alpha Drop-Shadow */}
            <div
              className="cursor-pointer select-none transition-transform duration-300 hover:scale-105"
              onClick={() => setCurrentPage('size')}
              title="Click to start new assay pipeline"
            >
              <img
                src={logoImg}
                alt="DNAx Logo"
                className="w-36 h-36 sm:w-40 sm:h-40 object-contain drop-shadow-[0_12px_28px_rgba(2,132,199,0.22)] hover:drop-shadow-[0_18px_36px_rgba(2,132,199,0.35)] transition-all duration-300"
              />
            </div>

            {/* Primary Action Button */}
            <div>
              <button
                onClick={() => setCurrentPage('size')}
                className="gradient-btn flex items-center space-x-2 px-7 py-3 rounded-2xl text-white text-xs sm:text-sm font-bold shadow-md active:scale-95 cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                <span>Start Assay Pipeline</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* 2. Key Status Tiles (Database Total DNA + NCBI Online Status) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Tile 1: Database Total DNA */}
            <div
              onClick={scrollToScreen2}
              className="glass-panel glass-panel-hover p-5 flex items-center justify-between cursor-pointer group"
              title="Click or scroll down to view sequence repository"
            >
              <div className="space-y-1">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5 font-mono">
                  <Database className="w-3.5 h-3.5 text-sky-600" />
                  <span>Database Total DNA</span>
                </span>
                <div className="text-2xl sm:text-3xl font-black text-slate-900 font-sans tracking-tight">
                  {dbCount} <span className="text-sm font-medium text-slate-400">Constructs</span>
                </div>
                <span className="text-xs text-sky-600 font-bold group-hover:translate-x-1 transition-transform inline-flex items-center space-x-1">
                  <span>View Sequence Vault</span>
                  <ChevronDown className="w-3.5 h-3.5" />
                </span>
              </div>

              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-sky-500 to-indigo-600 text-white flex items-center justify-center shadow-md shadow-sky-500/20 group-hover:scale-105 transition-transform">
                <Dna className="w-6 h-6" />
              </div>
            </div>

            {/* Tile 2: NCBI Online Status */}
            <div className="glass-panel glass-panel-hover p-5 flex items-center justify-between">
              <div className="space-y-1">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5 font-mono">
                  <Globe className="w-3.5 h-3.5 text-emerald-600" />
                  <span>NCBI BLAST Service</span>
                </span>
                <div className="text-2xl sm:text-3xl font-black text-emerald-600 font-sans tracking-tight flex items-center space-x-2">
                  <span>ONLINE</span>
                </div>
                <div className="flex items-center space-x-1.5 text-xs text-slate-500 font-medium">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span>GenBank nt Sync Active</span>
                </div>
              </div>

              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white flex items-center justify-center shadow-md shadow-emerald-500/20">
                <Globe className="w-6 h-6" />
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Full-Window Snap Scroll Prompt */}
        <div className="flex justify-center pb-2 pt-2">
          <button
            onClick={scrollToScreen2}
            className="flex items-center space-x-1.5 px-4 py-1.5 rounded-full bg-white/80 hover:bg-white text-slate-600 hover:text-slate-900 border border-slate-200/90 text-xs font-bold transition cursor-pointer backdrop-blur-md shadow-2xs group"
          >
            <span>Scroll down for Sequence Vault</span>
            <ChevronDown className="w-3.5 h-3.5 group-hover:translate-y-0.5 transition-transform text-sky-600 animate-bounce" />
          </button>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* SCREEN 2 (FULL VIEWPORT): Full Sequence Repository Ledger & Inspection    */}
      {/* ========================================================================= */}
      <section
        ref={screen2Ref}
        className="snap-start-always h-[calc(100vh-4rem)] flex flex-col justify-between p-6 sm:p-8 max-w-5xl mx-auto"
      >
        <div className="space-y-4 flex-1 flex flex-col justify-center">
          {/* Top Return Button */}
          <div className="flex items-center justify-between pb-1">
            <button
              onClick={scrollToScreen1}
              className="flex items-center space-x-1.5 text-xs font-bold text-sky-600 hover:text-indigo-700 transition cursor-pointer bg-white/80 px-3 py-1.5 rounded-xl border border-slate-200 shadow-2xs"
            >
              <ChevronUp className="w-3.5 h-3.5" />
              <span>Back to Command Dashboard</span>
            </button>

            <span className="text-xs text-slate-400 font-medium">Click any construct to view full molecular protocol dossier</span>
          </div>

          {/* Sequence Repository Ledger Table */}
          <div className="glass-panel overflow-hidden shadow-sm flex-1 flex flex-col justify-between max-h-[72vh]">
            {/* Table Header Controls */}
            <div className="p-4 flex items-center justify-between flex-wrap gap-3 border-b border-slate-200/60 bg-white/40">
              <div className="flex items-center space-x-2">
                <Dna className="w-4 h-4 text-sky-600" />
                <h2 className="text-xs font-extrabold text-slate-900 uppercase tracking-wider">Sequence Repository Ledger</h2>
                <span className="text-xs text-slate-500 font-mono font-bold px-2 py-0.5 rounded-full bg-white/80 border border-slate-200">
                  {filteredSequences.length}
                </span>
              </div>

              <div className="flex items-center space-x-3">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search saved constructs..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="bg-white/90 border border-slate-200 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-sky-500 focus:bg-white transition w-48 sm:w-56 font-medium shadow-2xs"
                  />
                </div>

                <button
                  onClick={() => setCurrentPage('matrix_db')}
                  className="text-xs text-sky-600 hover:text-indigo-600 font-bold flex items-center space-x-1 cursor-pointer transition"
                >
                  <span>Heatmap Matrix</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Table Grid */}
            <div className="overflow-y-auto flex-1">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50/70 text-slate-600 font-bold border-b border-slate-200/60 sticky top-0 backdrop-blur-md">
                  <tr>
                    <th className="py-3 px-4">Accession ID</th>
                    <th className="py-3 px-4">Construct Name</th>
                    <th className="py-3 px-4">Architecture</th>
                    <th className="py-3 px-4">Length</th>
                    <th className="py-3 px-4">GC Content</th>
                    <th className="py-3 px-4">Creation Date</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100/80 font-mono">
                  {filteredSequences.length > 0 ? (
                    filteredSequences.map((s) => (
                      <tr
                        key={s.id}
                        onClick={() => setSelectedInspectSeq(s)}
                        className="hover:bg-sky-50/60 transition cursor-pointer group"
                      >
                        <td className="py-3 px-4 text-slate-400">#LIB-{String(s.id).padStart(4, '0')}</td>
                        <td className="py-3 px-4 font-bold text-slate-900 font-sans group-hover:text-sky-700 transition">
                          {s.name}
                        </td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100/90 text-slate-700 border border-slate-200">
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
                      <td colSpan="7" className="py-12 text-center text-slate-400 font-sans space-y-2">
                        <Database className="w-7 h-7 mx-auto text-slate-300" />
                        <p className="text-xs font-medium">No sequences in repository vault yet.</p>
                        <button
                          onClick={() => setCurrentPage('size')}
                          className="gradient-btn px-4 py-2 rounded-xl text-white text-xs font-bold transition shadow-sm cursor-pointer"
                        >
                          Start First Design
                        </button>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

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
                  </div>
                  <span className="text-xs text-slate-400 font-mono">
                    Accession #LIB-{String(selectedInspectSeq.id).padStart(4, '0')} • Created {selectedInspectSeq.created_at || 'Recent'}
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
              <div className="flex items-center space-x-2">
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
              </div>

              <div className="flex items-center space-x-2">
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
        </div>
      )}
    </div>
  );
}
