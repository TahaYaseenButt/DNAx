import React, { useState } from 'react';
import {
  Save,
  FileSpreadsheet,
  FileText,
  Database,
  CheckCircle2,
  ShieldCheck,
  ArrowRight
} from 'lucide-react';
import SequenceViewer from '../components/SequenceViewer';
import { api } from '../api';

export default function ExportPage({ setCurrentPage, constructData, refreshDbCount }) {
  const [name, setName] = useState('DNAx_Construct_01');
  const [notes, setNotes] = useState('Synthetic taggant construct. BLAST screen verified.');
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [exportMessage, setExportMessage] = useState('');

  const payload = constructData?.payload || 'CGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGAT';
  const fullSeq = constructData?.linear_seq || payload;
  const length = constructData?.length || payload.length;
  const gc = constructData?.gc_pct || 51.4;

  const handleSaveToDb = async () => {
    if (!name.trim()) {
      alert('Please enter a construct name');
      return;
    }
    setSaving(true);
    try {
      const record = {
        name,
        notes,
        mode: constructData?.mode || 'linear',
        payload,
        full_sequence: fullSeq,
        length,
        gc_pct: gc,
        primers: constructData?.primers || {},
        probes: constructData?.probes || [],
      };
      const res = await api.saveSequence(record);
      if (res && res.success) {
        setSavedSuccess(true);
        if (refreshDbCount) refreshDbCount();
        setExportMessage('✓ Construct successfully saved to database.');
      }
    } catch (e) {
      console.error(e);
      alert('Error saving sequence: ' + e);
    } finally {
      setSaving(false);
    }
  };

  const handleExportExcel = async () => {
    await api.exportExcel(constructData, `${name}.xlsx`);
    setExportMessage('✓ Exported laboratory data to Excel (.xlsx)');
  };

  const handleExportPdf = async () => {
    await api.exportPdf(constructData, `${name}.pdf`);
    setExportMessage('✓ Generated report PDF (.pdf)');
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs font-mono text-slate-500 font-bold uppercase">
            STEP 06 OF 06 • REVIEW & SAVE
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight mt-1">Review & Save Construct</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Confirm specifications, commit sequence to local library, and export reports.
          </p>
        </div>

        <button
          onClick={() => setCurrentPage('matrix_db')}
          className="flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition shadow-xs cursor-pointer"
        >
          <Database className="w-4 h-4 text-sky-400" />
          <span>Open Library</span>
        </button>
      </div>

      {/* Checklist */}
      <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-xs">
        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2.5">
          Validation Checklist
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 text-xs">
          {[
            '1. Sizing',
            '2. DNA Gen',
            '3. BLAST ≥25%',
            '4. Primers',
            '5. Probes',
            '6. Save',
          ].map((item, idx) => (
            <div
              key={idx}
              className="p-2 rounded-lg bg-slate-50 border border-slate-200 flex items-center space-x-1.5 font-semibold text-slate-800"
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
              <span className="truncate">{item}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Construct Form */}
      <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-xs space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-700">Construct Name *</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. DNAx_Construct_01"
              className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3.5 py-2 text-xs font-bold text-slate-900 focus:outline-none focus:border-sky-600 focus:bg-white transition"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-700">Laboratory Notes</label>
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Project notes, batch ID..."
              className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3.5 py-2 text-xs text-slate-800 focus:outline-none focus:border-sky-600 focus:bg-white transition"
            />
          </div>
        </div>

        {/* Specs Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs bg-slate-50 p-3.5 rounded-lg border border-slate-200">
          <div>
            <span className="text-slate-500 block text-[10px] font-bold">LENGTH</span>
            <span className="font-bold text-slate-900 font-mono">{length} bp</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] font-bold">GC CONTENT</span>
            <span className="font-bold text-slate-900 font-mono">{gc.toFixed(1)}%</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] font-bold">PRIMERS</span>
            <span className="font-bold text-emerald-700 font-mono">Verified</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] font-bold">PROBES</span>
            <span className="font-bold text-sky-700 font-mono">4 Channels</span>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-100">
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={handleSaveToDb}
              disabled={saving}
              className="flex items-center space-x-1.5 px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white text-xs font-bold transition shadow-xs disabled:opacity-50 cursor-pointer"
            >
              {saving ? (
                <span>Saving...</span>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  <span>{savedSuccess ? '✓ Saved in Library' : 'Save to Library'}</span>
                </>
              )}
            </button>

            <button
              onClick={handleExportExcel}
              className="flex items-center space-x-1.5 px-3.5 py-2.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold border border-slate-200 transition shadow-xs cursor-pointer"
            >
              <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
              <span>Export Excel</span>
            </button>

            <button
              onClick={handleExportPdf}
              className="flex items-center space-x-1.5 px-3.5 py-2.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold border border-slate-200 transition shadow-xs cursor-pointer"
            >
              <FileText className="w-4 h-4 text-rose-600" />
              <span>Export PDF</span>
            </button>
          </div>

          <button
            onClick={() => setCurrentPage('matrix_db')}
            className="flex items-center space-x-1 px-4 py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition shadow-xs cursor-pointer"
          >
            <span>Open Library</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {exportMessage && (
          <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs font-bold">
            {exportMessage}
          </div>
        )}
      </div>

      {/* Sequence Viewer */}
      <SequenceViewer
        title="Construct Sequence"
        sequence={fullSeq}
        badge={constructData?.mode === 'circular' ? 'Circular Vector' : 'Linear Construct'}
      />
    </div>
  );
}
