import React, { useState } from 'react';
import { Copy, Check, Eye, Layers, Sparkles } from 'lucide-react';

export default function SequenceViewer({
  title = "DNA Sequence (5' → 3')",
  sequence = "",
  badge = "",
  primers = null,
  probes = [],
  highlightSpan = null // { start, end, label, colorHex, bgClass }
}) {
  const [copied, setCopied] = useState(false);
  const [activeHighlight, setActiveHighlight] = useState(highlightSpan);

  const handleCopy = () => {
    if (!sequence) return;
    navigator.clipboard.writeText(sequence);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const fwdLen = primers?.fwd?.len || primers?.fwd?.seq?.length || 20;
  const revLen = primers?.rev?.len || primers?.rev?.seq?.length || 20;
  const seqLen = sequence.length || 300;

  const defaultFeatures = [
    { label: "5' Fwd Primer", start: 0, end: fwdLen, color: '#10b981', bg: 'bg-emerald-100 text-emerald-900 border-emerald-300' },
    { label: 'FAM Probe', start: 30, end: 54, color: '#22c55e', bg: 'bg-green-100 text-green-900 border-green-300' },
    { label: 'HEX Probe', start: 80, end: 104, color: '#eab308', bg: 'bg-amber-100 text-amber-900 border-amber-300' },
    { label: 'ROX Probe', start: 140, end: 164, color: '#f97316', bg: 'bg-orange-100 text-orange-900 border-orange-300' },
    { label: 'Cy5 Probe', start: 200, end: 224, color: '#ec4899', bg: 'bg-pink-100 text-pink-900 border-pink-300' },
    { label: "3' Rev Primer", start: Math.max(0, seqLen - revLen), end: seqLen, color: '#0ea5e9', bg: 'bg-sky-100 text-sky-900 border-sky-300' },
  ];

  const features = highlightSpan ? [highlightSpan] : defaultFeatures;

  // Format sequence into 50-bp rows with 10-bp blocks (Benchling/SnapGene standard)
  const renderNumberedSequence = () => {
    if (!sequence) return <span className="text-slate-400 italic">No sequence data</span>;

    const rowSize = 50;
    const rows = [];
    for (let i = 0; i < sequence.length; i += rowSize) {
      const rowSeq = sequence.slice(i, i + rowSize);
      const startCoord = i + 1;
      const endCoord = Math.min(sequence.length, i + rowSize);

      // Split row into 10-bp blocks
      const blocks = [];
      for (let j = 0; j < rowSeq.length; j += 10) {
        const blockSeq = rowSeq.slice(j, j + 10);
        const blockStartIdx = i + j;

        const renderedBases = blockSeq.split('').map((base, bIdx) => {
          const globalIdx = blockStartIdx + bIdx;

          // Check highlights
          let isHighlighted = false;
          let highlightStyle = '';

          if (activeHighlight && globalIdx >= activeHighlight.start && globalIdx < activeHighlight.end) {
            isHighlighted = true;
            highlightStyle = 'bg-sky-200 text-sky-950 font-black ring-1 ring-sky-500 rounded-2xs';
          } else {
            for (const f of defaultFeatures) {
              if (globalIdx >= f.start && globalIdx < f.end) {
                if (f.label.includes('Fwd')) highlightStyle = 'bg-emerald-100/90 text-emerald-950 font-bold';
                else if (f.label.includes('Rev')) highlightStyle = 'bg-sky-100/90 text-sky-950 font-bold';
                else if (f.label.includes('FAM')) highlightStyle = 'bg-green-100/90 text-green-950 font-bold';
                else if (f.label.includes('HEX')) highlightStyle = 'bg-amber-100/90 text-amber-950 font-bold';
                else if (f.label.includes('ROX')) highlightStyle = 'bg-orange-100/90 text-orange-950 font-bold';
                else if (f.label.includes('Cy5')) highlightStyle = 'bg-pink-100/90 text-pink-950 font-bold';
                break;
              }
            }
          }

          let baseColor = 'text-slate-700';
          if (!highlightStyle) {
            if (base === 'A') baseColor = 'text-rose-600 font-bold';
            else if (base === 'T') baseColor = 'text-sky-600 font-bold';
            else if (base === 'C') baseColor = 'text-emerald-600 font-bold';
            else if (base === 'G') baseColor = 'text-amber-600 font-bold';
          }

          return (
            <span key={bIdx} className={`${baseColor} ${highlightStyle} px-[1px]`}>
              {base}
            </span>
          );
        });

        blocks.push(
          <span key={j} className="inline-block mr-2.5">
            {renderedBases}
          </span>
        );
      }

      rows.push(
        <div key={i} className="flex items-center space-x-3 py-0.5 hover:bg-slate-100/80 rounded px-1.5 transition">
          <span className="text-[11px] font-mono text-slate-400 select-none w-10 text-right shrink-0">
            {startCoord}
          </span>
          <div className="font-mono text-xs tracking-wider flex-1">
            {blocks}
          </div>
          <span className="text-[11px] font-mono text-slate-400 select-none w-10 text-left shrink-0">
            {endCoord}
          </span>
        </div>
      );
    }

    return <div className="space-y-0.5 select-text">{rows}</div>;
  };

  return (
    <div className="lab-card p-5 space-y-4">
      {/* Header Toolbar */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-100 flex-wrap gap-2">
        <div className="flex items-center space-x-2">
          <Eye className="w-4 h-4 text-sky-600" />
          <span className="text-sm font-bold text-slate-900">{title}</span>
          {badge && (
            <span className="text-[10px] uppercase font-mono font-bold tracking-wider px-2 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200">
              {badge}
            </span>
          )}
        </div>

        <div className="flex items-center space-x-3">
          <span className="text-xs text-slate-500 font-mono font-bold">{sequence ? `${sequence.length} bp` : '0 bp'}</span>
          <button
            onClick={handleCopy}
            disabled={!sequence}
            className="flex items-center space-x-1.5 text-xs font-semibold px-3 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition cursor-pointer"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span className="text-emerald-700 font-bold">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-slate-500" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Feature Annotation Map Strip */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-[11px] font-bold text-slate-400 uppercase tracking-wider">
          <span className="flex items-center space-x-1">
            <Layers className="w-3.5 h-3.5 text-sky-600" />
            <span>Annotated Feature Binding Map</span>
          </span>
          {activeHighlight && (
            <button
              onClick={() => setActiveHighlight(null)}
              className="text-xs text-sky-600 hover:underline font-bold capitalize cursor-pointer"
            >
              Clear selection
            </button>
          )}
        </div>

        <div className="flex flex-wrap gap-1.5">
          {features.map((feat, idx) => {
            const isSelected = activeHighlight?.label === feat.label;
            return (
              <button
                key={idx}
                onClick={() => setActiveHighlight(isSelected ? null : feat)}
                className={`flex items-center space-x-1.5 text-[10px] font-mono font-bold px-2.5 py-1 rounded-lg border transition cursor-pointer ${
                  feat.bg || 'bg-slate-100 text-slate-800 border-slate-200'
                } ${isSelected ? 'ring-2 ring-sky-500 shadow-xs scale-105' : 'hover:opacity-85'}`}
              >
                <span>{feat.label}</span>
                <span className="opacity-60 text-[9px]">[{feat.start}..{feat.end}]</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Numbered Grouped Nucleotide Viewport */}
      <div className="bg-slate-50/80 rounded-xl p-4 max-h-64 overflow-y-auto border border-slate-200 shadow-inner">
        {renderNumberedSequence()}
      </div>
    </div>
  );
}
