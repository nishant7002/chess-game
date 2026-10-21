import React from 'react';
import { RotateCcw, Play, Settings2 } from 'lucide-react';

export const GameControls = ({
  humanColor,
  setHumanColor,
  algorithm,
  setAlgorithm,
  depth,
  setDepth,
  onStartGame,
  onRestartGame,
  isGameInProgress,
  isThinking,
  _gameStatus
}) => {
  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-4 shadow-lg space-y-4">
      <div className="flex items-center gap-2 pb-2 border-b border-slate-700/60">
        <Settings2 className="w-4 h-4 text-emerald-400" />
        <h3 className="text-sm font-semibold text-slate-200">Game & AI Settings</h3>
      </div>

      {/* Human Color Selection */}
      <div>
        <label className="text-xs text-slate-400 block mb-1.5 font-medium">Player Color</label>
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            disabled={isGameInProgress || isThinking}
            onClick={() => setHumanColor('white')}
            className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold border transition-all ${
              humanColor === 'white'
                ? 'bg-slate-100 text-slate-900 border-white shadow-md'
                : 'bg-slate-700/50 text-slate-300 border-slate-600 hover:bg-slate-700'
            } disabled:opacity-50`}
          >
            <div className="w-3.5 h-3.5 rounded-full bg-white border border-slate-400 shadow-sm" />
            Play White (First)
          </button>

          <button
            type="button"
            disabled={isGameInProgress || isThinking}
            onClick={() => setHumanColor('black')}
            className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold border transition-all ${
              humanColor === 'black'
                ? 'bg-slate-900 text-white border-slate-400 shadow-md ring-1 ring-white/20'
                : 'bg-slate-700/50 text-slate-300 border-slate-600 hover:bg-slate-700'
            } disabled:opacity-50`}
          >
            <div className="w-3.5 h-3.5 rounded-full bg-black border border-slate-500 shadow-sm" />
            Play Black (AI Starts)
          </button>
        </div>
      </div>

      {/* Algorithm Selection */}
      <div>
        <label className="text-xs text-slate-400 block mb-1.5 font-medium">AI Algorithm Strategy</label>
        <select
          value={algorithm}
          disabled={isThinking}
          onChange={(e) => setAlgorithm(e.target.value)}
          className="w-full bg-slate-900/90 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 font-medium"
        >
          <option value="alpha_beta_ordered">Alpha-Beta Pruning + Move Ordering (Recommended)</option>
          <option value="alpha_beta">Alpha-Beta Pruning (Canonical)</option>
          <option value="minimax">Pure Minimax (Depth-Limited, No Pruning)</option>
          <option value="greedy">Greedy Agent (1-ply Heuristic Baseline)</option>
          <option value="random">Random Legal Move (Stochastic Baseline)</option>
        </select>
      </div>

      {/* Depth Slider */}
      <div>
        <div className="flex justify-between items-center mb-1.5">
          <label className="text-xs text-slate-400 font-medium">Search Depth Limit</label>
          <span className="text-xs font-mono font-bold text-amber-400">
            {depth} {depth === 1 ? 'ply' : 'plies'}
          </span>
        </div>
        <input
          type="range"
          min="1"
          max="4"
          step="1"
          value={depth}
          disabled={isThinking || algorithm === 'random' || algorithm === 'greedy'}
          onChange={(e) => setDepth(parseInt(e.target.value, 10))}
          className="w-full accent-emerald-500 cursor-pointer disabled:opacity-40"
        />
        <div className="flex justify-between text-[10px] text-slate-500 mt-1">
          <span>1 (Fast)</span>
          <span>2 (Casual)</span>
          <span>3 (Tactical)</span>
          <span>4 (Deep Search)</span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-2 pt-2">
        <button
          type="button"
          onClick={onStartGame}
          disabled={isThinking}
          className="flex items-center justify-center gap-1.5 py-2.5 px-3 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg shadow-md transition-all disabled:opacity-50"
        >
          <Play className="w-3.5 h-3.5" />
          New Game
        </button>

        <button
          type="button"
          onClick={onRestartGame}
          disabled={isThinking}
          className="flex items-center justify-center gap-1.5 py-2.5 px-3 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-semibold rounded-lg border border-slate-600 transition-all disabled:opacity-50"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Restart Game
        </button>
      </div>
    </div>
  );
};
