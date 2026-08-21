import React from 'react';
import { FileText, FlaskConical, Thermometer, Clock, ShieldCheck } from 'lucide-react';

export default function ProtocolPage() {
  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6 animate-fadeIn">
      {/* Header */}
      <div>
        <div className="flex items-center space-x-2 text-xs font-mono text-emerald-600 font-bold uppercase tracking-wider">
          <span>STANDARD OPERATING PROCEDURES (SOP)</span>
        </div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight mt-1">Laboratory Assay Protocols</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Validated thermocycling protocols, master mix stoichiometry, and qPCR detection parameters for DNAx Track & Trace taggants.
        </p>
      </div>

      {/* Protocol 1: PCR Amplification */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm space-y-4">
        <div className="flex items-center space-x-3 pb-3 border-b border-slate-100">
          <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600">
            <FlaskConical className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900">1. Endpoint PCR Master Mix (25 µL Reaction)</h2>
            <p className="text-xs text-slate-500">Standard amplification setup for synthetic DNA barcode retrieval.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="text-slate-700 font-bold font-sans">REACTION COMPONENTS</div>
            <div className="flex justify-between text-slate-800"><span>2X Taq Master Mix</span><span className="font-bold">12.5 µL</span></div>
            <div className="flex justify-between text-slate-800"><span>Forward Primer (10 µM)</span><span className="font-bold">1.0 µL (0.4 µM)</span></div>
            <div className="flex justify-between text-slate-800"><span>Reverse Primer (10 µM)</span><span className="font-bold">1.0 µL (0.4 µM)</span></div>
            <div className="flex justify-between text-slate-800"><span>DNA Template / Extract</span><span className="font-bold">2.0 µL</span></div>
            <div className="flex justify-between text-slate-800"><span>Nuclease-free Water</span><span className="font-bold">8.5 µL</span></div>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="text-slate-700 font-bold font-sans">THERMOCYCLING PROFILE</div>
            <div className="flex justify-between text-slate-800"><span>Initial Denaturation</span><span className="font-bold">95°C • 3 min</span></div>
            <div className="flex justify-between text-emerald-700 font-bold"><span>35 Cycles:</span><span></span></div>
            <div className="flex justify-between text-slate-700 pl-3"><span>- Denaturation</span><span>95°C • 30 s</span></div>
            <div className="flex justify-between text-slate-700 pl-3"><span>- Annealing</span><span>58°C • 30 s</span></div>
            <div className="flex justify-between text-slate-700 pl-3"><span>- Extension</span><span>72°C • 45 s</span></div>
            <div className="flex justify-between text-slate-800"><span>Final Extension</span><span className="font-bold">72°C • 5 min</span></div>
          </div>
        </div>
      </div>

      {/* Protocol 2: Multiplex qPCR */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm space-y-4">
        <div className="flex items-center space-x-3 pb-3 border-b border-slate-100">
          <div className="p-2 rounded-xl bg-violet-50 text-violet-600">
            <Thermometer className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900">2. 4-Channel Multiplex qPCR TaqMan Assay (20 µL)</h2>
            <p className="text-xs text-slate-500">Quantitative detection with FAM, HEX, ROX, Cy5 dual-labeled probes.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="text-slate-700 font-bold font-sans">REACTION COMPONENTS</div>
            <div className="flex justify-between text-slate-800"><span>2X Probe qPCR Master Mix</span><span className="font-bold">10.0 µL</span></div>
            <div className="flex justify-between text-slate-800"><span>Primer Mix (F+R 10 µM)</span><span className="font-bold">0.8 µL each</span></div>
            <div className="flex justify-between text-slate-800"><span>TaqMan Probes (10 µM each)</span><span className="font-bold">0.4 µL each</span></div>
            <div className="flex justify-between text-slate-800"><span>Sample DNA Template</span><span className="font-bold">2.0 µL</span></div>
            <div className="flex justify-between text-slate-800"><span>Nuclease-free Water</span><span className="font-bold">to 20.0 µL</span></div>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="text-slate-700 font-bold font-sans">QPCR CYCLING PROGRAM</div>
            <div className="flex justify-between text-slate-800"><span>Polymerase Activation</span><span className="font-bold">95°C • 2 min</span></div>
            <div className="flex justify-between text-violet-700 font-bold"><span>40 Cycles:</span><span></span></div>
            <div className="flex justify-between text-slate-700 pl-3"><span>- Denaturation</span><span>95°C • 10 s</span></div>
            <div className="flex justify-between text-slate-900 pl-3 font-bold"><span>- Anneal/Extend (Read)</span><span>60°C • 30 s</span></div>
            <div className="flex justify-between text-slate-500 text-[11px] pt-1 font-sans"><span>Acquire channels: FAM, HEX, ROX, Cy5</span><span></span></div>
          </div>
        </div>
      </div>
    </div>
  );
}
