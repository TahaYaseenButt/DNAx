import React, { useState } from 'react';
import { Database, ChevronRight, Globe, Sparkles, Download, CheckCircle, RefreshCw, X, ArrowUpRight } from 'lucide-react';
import { api } from '../api';

export default function TopNavBar({
  currentPage,
  setCurrentPage,
  dbCount = 0
}) {
  const [showOtaModal, setShowOtaModal] = useState(false);
  const [otaStatus, setOtaStatus] = useState(null);
  const [checkingOta, setCheckingOta] = useState(false);
  const [installingOta, setInstallingOta] = useState(false);

  const pageTitles = {
    home: 'Command Dashboard',
    size: '1. Physical Sizing',
    dna: '2. DNA Synthesis',
    comparator: '3. BLAST Homology',
    primer: '4. PCR Primers',
    qpcr: '5. qPCR Probes',
    export: '6. Review & Save',
    matrix_db: 'Sequence Library',
    protocol: 'Standard SOPs',
  };

  const handleCheckUpdate = async () => {
    setCheckingOta(true);
    try {
      const res = await api.checkForUpdates();
      setOtaStatus(res);
    } catch (e) {
      console.error(e);
    } finally {
      setCheckingOta(false);
    }
  };

  const handleOpenOtaModal = () => {
    setShowOtaModal(true);
    handleCheckUpdate();
  };

  const handleApplyUpdate = async () => {
    if (!otaStatus?.download_url) return;
    setInstallingOta(true);
    try {
      await api.installUpdate(otaStatus.download_url, otaStatus.sha256);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <>
      <header className="h-16 backdrop-blur-2xl bg-white/70 border-b border-white/80 px-8 flex items-center justify-between select-none z-20 sticky top-0 shadow-2xs">
        {/* 1. Clean Breadcrumb with Gradient Highlight */}
        <div className="flex items-center space-x-2 text-xs">
          <span className="font-semibold text-slate-400">DNAx Workspace</span>
          <ChevronRight className="w-3.5 h-3.5 text-slate-300" />
          <span className="font-extrabold text-slate-900 text-sm tracking-tight">
            {pageTitles[currentPage] || 'Dashboard'}
          </span>
        </div>

        {/* 2. Right: OTA Update Badge + NCBI Status + Sequence Vault */}
        <div className="flex items-center space-x-3">
          {/* OTA Version Status Badge */}
          <button
            onClick={handleOpenOtaModal}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-white/80 hover:bg-white text-slate-700 text-xs font-bold border border-slate-200 shadow-2xs transition cursor-pointer"
            title="Click to check for OTA desktop updates"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>v2.0.0</span>
            <span className="text-[10px] text-slate-400 font-mono">(OTA Ready)</span>
          </button>

          {/* Live NCBI Online Status */}
          <div className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-xl gradient-badge-emerald text-xs font-bold shadow-2xs backdrop-blur-md">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>NCBI BLAST Online</span>
          </div>

          {/* Database Vault CTA */}
          <button
            onClick={() => setCurrentPage('matrix_db')}
            className="gradient-btn flex items-center space-x-2 text-xs font-bold px-4 py-2 rounded-xl transition cursor-pointer shadow-md active:scale-95"
          >
            <Database className="w-3.5 h-3.5 text-sky-200" />
            <span>Library</span>
            <span className="font-mono text-[11px] font-bold px-1.5 py-0.2 rounded-full bg-white/20 text-white border border-white/30">
              {dbCount}
            </span>
          </button>
        </div>
      </header>

      {/* OTA UPDATE MODAL */}
      {showOtaModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-md animate-fadeIn">
          <div className="glass-panel w-full max-w-md p-6 bg-white/95 border-white shadow-2xl space-y-5">
            {/* Header */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-sky-500 to-indigo-600 text-white flex items-center justify-center shadow-xs">
                  <Download className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-extrabold text-slate-900">DNAx Over-The-Air (OTA) Updates</h3>
                  <span className="text-[11px] text-slate-400 font-mono">Current Build: v2.0.0</span>
                </div>
              </div>

              <button
                onClick={() => setShowOtaModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-800 hover:bg-slate-100 transition cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Status Body */}
            <div className="space-y-3 text-xs">
              {checkingOta ? (
                <div className="py-6 text-center text-slate-500 space-y-2">
                  <RefreshCw className="w-6 h-6 mx-auto animate-spin text-sky-600" />
                  <p className="font-medium">Connecting to release manifest...</p>
                </div>
              ) : otaStatus?.update_available ? (
                <div className="p-4 rounded-xl bg-sky-50 border border-sky-200 space-y-2">
                  <div className="flex items-center justify-between text-sky-950 font-bold">
                    <span>🚀 New Version Available: {otaStatus.latest_version}</span>
                    <span className="text-[10px] font-mono text-sky-700">{otaStatus.release_date}</span>
                  </div>
                  <p className="text-[11px] text-slate-600">{otaStatus.release_notes}</p>
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-emerald-50/80 border border-emerald-200 flex items-center space-x-3 text-emerald-950">
                  <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
                  <div>
                    <span className="font-bold block">DNAx is Up to Date (v2.0.0)</span>
                    <span className="text-[11px] text-emerald-800 font-medium block">
                      Standalone desktop executable is operating on the latest verified release.
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between pt-2 border-t border-slate-100">
              <button
                onClick={handleCheckUpdate}
                disabled={checkingOta}
                className="flex items-center space-x-1.5 text-xs font-bold px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 transition cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${checkingOta ? 'animate-spin' : ''}`} />
                <span>Check Again</span>
              </button>

              {otaStatus?.update_available ? (
                <button
                  onClick={handleApplyUpdate}
                  disabled={installingOta}
                  className="gradient-btn flex items-center space-x-1.5 px-4 py-2 rounded-xl text-white text-xs font-bold transition shadow-xs cursor-pointer"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>{installingOta ? 'Updating...' : 'Update & Restart'}</span>
                </button>
              ) : (
                <button
                  onClick={() => setShowOtaModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition cursor-pointer"
                >
                  Close
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
