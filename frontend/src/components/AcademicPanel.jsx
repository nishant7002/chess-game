import React, { useState } from 'react';
import { Cpu, ChevronDown, ChevronUp, Activity, Zap, Layers, Scissors, Target } from 'lucide-react';

export const AcademicPanel = ({ metrics, lastEval, isThinking }) => {
  const [isOpen, setIsOpen] = useState(true);

  if (!metrics) {
    return (
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-4 shadow-lg text-slate-400 text-xs text-center">
        <Cpu className="w-5 h-5 mx-auto mb-1 text-slate-500" />
        AI search telemetry will appear after the AI agent computes its move.
      </div>
    );
  }

  // Format evaluation in pawns (centipawns / 100)
  const evalPawns = lastEval !== undefined && lastEval !== null ? (lastEval / 100).toFixed(2) : '0.00';
  const evalSign = lastEval > 0 ? `+${evalPawns}` : evalPawns;

  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-4 shadow-lg">
      <div
        className="flex items-center justify-between cursor-pointer select-none pb-2 border-b border-slate-700/60"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-semibold text-slate-200">AI Search Telemetry & Metrics</h3>
        </div>
        <button className="text-slate-400 hover:text-white transition-colors">
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {isOpen && (
        <div className="mt-3 space-y-3">
          {isThinking && (
            <div className="flex items-center gap-2 px-3 py-2 bg-cyan-950/40 border border-cyan-800/60 rounded-lg text-xs text-cyan-300 animate-pulse">
              <Activity className="w-4 h-4 animate-spin text-cyan-400" />
              <span>AI search in progress: evaluating minimax game tree...</span>
            </div>
          )}

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
            {/* Algorithm */}
            <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-700/50">
              <span className="text-[10px] text-slate-400 block uppercase font-medium">Algorithm</span>
              <span className="text-xs font-bold text-white capitalize">
                {metrics.algorithm?.replace(/_/g, ' ') || 'Alpha-Beta'}
              </span>
            </div>

            {/* Depth */}
            <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-700/50">
              <span className="text-[10px] text-slate-400 block uppercase font-medium">Search Depth</span>
              <span className="text-xs font-bold text-amber-400">{metrics.depth ?? '-'} ply</span>
            </div>

            {/* Runtime */}
            <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-700/50">
              <span className="text-[10px] text-slate-400 block uppercase font-medium flex items-center gap-1">
                <Zap className="w-3 h-3 text-amber-400" /> Runtime
              </span>
              <span className="text-xs font-bold text-emerald-400">{metrics.runtime_ms ?? 0} ms</span>
            </div>

            {/* Nodes Expanded */}
            <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-700/50">
              <span className="text-[10px] text-slate-400 block uppercase font-medium flex items-center gap-1">
                <Layers className="w-3 h-3 text-blue-400" /> Nodes Expanded
              </span>
              <span className="text-xs font-bold text-blue-300">
                {metrics.nodes_expanded?.toLocaleString() ?? 0}
              </span>
            </div>

            {/* Leaf Evaluations */}
            <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-700/50">
              <span className="text-[10px] text-slate-400 block uppercase font-medium flex items-center gap-1">
                <Target className="w-3 h-3 text-purple-400" /> Leaf Evaluations
              </span>
              <span className="text-xs font-bold text-purple-300">
                {metrics.leaf_evaluations?.toLocaleString() ?? 0}
              </span>
            </div>

            {/* Branches Pruned */}
            <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-700/50">
              <span className="text-[10px] text-slate-400 block uppercase font-medium flex items-center gap-1">
                <Scissors className="w-3 h-3 text-emerald-400" /> Pruned Branches
              </span>
              <span className="text-xs font-bold text-emerald-300">
                {metrics.pruned_branches?.toLocaleString() ?? 0}
              </span>
            </div>
          </div>

          {/* Position Evaluation Score */}
          <div className="bg-slate-900/70 p-2.5 rounded-lg border border-slate-700/50 flex items-center justify-between">
            <span className="text-xs text-slate-300 font-medium">Position Evaluation (White Perspective):</span>
            <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${
              lastEval > 50
                ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                : lastEval < -50
                ? 'bg-red-950 text-red-300 border border-red-800'
                : 'bg-slate-800 text-slate-200'
            }`}>
              {evalSign} cp
            </span>
          </div>

          <p className="text-[11px] text-slate-400 leading-relaxed bg-slate-900/30 p-2 rounded border border-slate-800">
            <strong>Theory Note:</strong> Alpha-Beta pruning guarantees identical Minimax decisions while avoiding branches outside the $[\alpha, \beta]$ search window. Move ordering improves cutoffs by evaluating captures (MVV-LVA) and checks first.
          </p>
        </div>
      )}
    </div>
  );
};
