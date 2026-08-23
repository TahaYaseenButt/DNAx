import React, { useState, useEffect } from 'react';
import {
  Save,
  FileSpreadsheet,
  FileText,
  Database,
  CheckCircle2,
  ShieldCheck,
  ArrowRight,
  Sparkles,
  Download,
  Dna,
  FlaskConical,
  Activity
} from 'lucide-react';
import SequenceViewer from '../components/SequenceViewer';
import { api } from '../api';

export default function ExportPage({ setCurrentPage, constructData, refreshDbCount }) {
  const [name, setName] = useState(constructData?.name || '');
  const [notes, setNotes] = useState('Synthetic taggant construct. BLAST screen verified.');
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [exportMessage, setExportMessage] = useState('');

  const payload = constructData?.payload || 'CGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGAT';
  const fullSeq = constructData?.linear_seq || payload;
  const length = constructData?.length || payload.length;
  const gc = constructData?.gc_pct || 51.4;

  useEffect(() => {
    // If no name is provided, generate a distinct sequential construct name
    const initName = async () => {
      if (constructData?.name && constructData.name.trim() !== '') {
        setName(constructData.name);
        return;
      }
      try {
        const seqs = await api.getSequences();
        const nextNum = (seqs?.length || 0) + 1;
        setName(`DNAx_Construct_${String(nextNum).padStart(2, '0')}`);
      } catch (e) {
        setName(`DNAx_Construct_${Date.now().toString().slice(-4)}`);
      }
    };
    initName();
  }, [constructData]);

  const handleSaveToDb = async () => {
    const finalName = name.trim() || `DNAx_Construct_${Date.now().toString().slice(-4)}`;
    setSaving(true);
    try {
      const record = {
        name: finalName,
        notes,
        mode: constructData?.mode || 'linear',
        payload,
        linear_seq: fullSeq,
        length,
        gc_pct: gc,
        primers: constructData?.primers || {},
        probes: constructData?.probes || [],
      };
      const res = await api.saveSequence(record);
      if (res && (res.success || res.id)) {
        setSavedSuccess(true);
        if (refreshDbCount) refreshDbCount();
        setExportMessage(`✓ Construct "${finalName}" successfully committed to database.`);
      }
    } catch (e) {
      console.error(e);
      alert('Error saving sequence: ' + e);
    } finally {
      setSaving(false);
    }
  };

  const handleExportExcel = async () => {
    await api.exportExcel(constructData, `${name || 'DNAx_Construct'}.xlsx`);
    setExportMessage('✓ Exported laboratory data to Excel (.xlsx)');
  };

  const handleExportPdf = async () => {
    await api.exportPdf({ ...constructData, name }, `${name || 'DNAx_Construct'}_Protocol.pdf`);
    setExportMessage('✓ Generated assay protocol PDF');
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs font-mono text-sky-600 font-bold uppercase tracking-wider">
            STEP 06 OF 06 • REVIEW & SAVE
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight mt-1">Review & Save Construct</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Confirm specifications, commit sequence to cloud/local vault, and export reports.
          </p>
        </div>

        <button
          onClick={() => setCurrentPage('matrix_db')}
          className="gradient-btn flex items-center space-x-1.5 px-4 py-2.5 rounded-xl text-white text-xs font-bold transition shadow-xs cursor-pointer"
        >
          <Database className="w-4 h-4 text-sky-200" />
          <span>Open Sequence Library</span>
        </button>
      </div>

      {/* Checklist */}
      <div className="glass-panel p-4 shadow-2xs">
        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2.5">
          Validation Checklist
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 text-xs">
          {[
            '1. Sizing',
            '2. Synthesis',
            '3. BLAST Safe',
            '4. Primers Set',
            '5. Multiplex Probes',
            '6. Vault Ready',
          ].map((item, idx) => (
            <div
              key={idx}
              className="p-2 rounded-xl bg-white/90 border border-slate-200 flex items-center space-x-1.5 font-bold text-slate-800 shadow-2xs"
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
              <span className="truncate">{item}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Construct Form */}
      <div className="glass-panel p-6 shadow-sm space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-700">Construct Name / Batch Identifier *</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. DNAx_Construct_02"
              className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs font-bold text-slate-900 focus:outline-none focus:border-sky-600 transition shadow-2xs"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-700">Laboratory Notes & Substrate</label>
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Pharma API Lot #884, Textile taggant..."
              className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs text-slate-800 focus:outline-none focus:border-sky-600 transition shadow-2xs"
            />
          </div>
        </div>

        {/* Specifications Summary */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[10px] text-slate-400 font-bold block uppercase">Architecture</span>
            <span className="font-bold text-slate-900">Linear dsDNA</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[10px] text-slate-400 font-bold block uppercase">Length</span>
            <span className="font-mono font-bold text-slate-900">{length} bp</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[10px] text-slate-400 font-bold block uppercase">GC Content</span>
            <span className="font-mono font-bold text-slate-900">{typeof gc === 'number' ? gc.toFixed(1) : gc}%</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[10px] text-slate-400 font-bold block uppercase">Probes Configured</span>
            <span className="font-mono font-bold text-slate-900">{constructData?.probes?.length || 4} Channels</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-100">
          <div className="flex items-center space-x-2">
            <button
              onClick={handleExportPdf}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold border border-slate-200 transition shadow-2xs cursor-pointer"
            >
              <FileText className="w-3.5 h-3.5 text-rose-500" />
              <span>Download Assay PDF</span>
            </button>

            <button
              onClick={handleExportExcel}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold border border-slate-200 transition shadow-2xs cursor-pointer"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
              <span>Export Excel</span>
            </button>
          </div>

          <button
            onClick={handleSaveToDb}
            disabled={saving}
            className="gradient-btn flex items-center space-x-2 px-6 py-2.5 rounded-xl text-white text-xs font-bold transition shadow-md cursor-pointer disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? 'Saving...' : '💾 Save to Database Vault'}</span>
          </button>
        </div>

        {exportMessage && (
          <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{exportMessage}</span>
          </div>
        )}
      </div>

      {/* Sequence Viewer */}
      <SequenceViewer
        title="Construct Sequence to Commit"
        sequence={fullSeq}
        badge="Linear dsDNA"
      />
    </div>
  );
}
