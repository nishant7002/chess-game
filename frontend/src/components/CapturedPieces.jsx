import React from 'react';
import { PieceIcon } from './ChessPieces';

export const CapturedPieces = ({ captured = { white: [], black: [] }, material = { diff: 0 } }) => {
  // Sort pieces by standard value for neat presentation: Q, R, B, N, P
  const sortPieces = (pieces) => {
    const order = { q: 1, r: 2, b: 3, n: 4, p: 5 };
    return [...pieces].sort((a, b) => (order[a.toLowerCase()] || 99) - (order[b.toLowerCase()] || 99));
  };

  const whiteCaptured = sortPieces(captured.white || []); // pieces captured by White (black pieces)
  const blackCaptured = sortPieces(captured.black || []); // pieces captured by Black (white pieces)

  const diff = material.diff || 0; // positive = White advantage, negative = Black advantage

  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-3 shadow-lg space-y-2">
      {/* Captured by Black (White pieces taken) */}
      <div className="flex items-center justify-between min-h-[30px] border-b border-slate-700/40 pb-1.5">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs text-slate-400 font-medium mr-1">Captured White:</span>
          {blackCaptured.length === 0 ? (
            <span className="text-[11px] text-slate-500 italic">None</span>
          ) : (
            blackCaptured.map((p, idx) => (
              <div key={idx} className="w-5 h-5 opacity-90 hover:opacity-100 transition-opacity">
                <PieceIcon piece={p.toUpperCase()} />
              </div>
            ))
          )}
        </div>
        {diff < 0 && (
          <span className="text-xs font-bold text-red-400 bg-red-950/60 px-1.5 py-0.5 rounded border border-red-800/50">
            +{Math.abs(diff)}
          </span>
        )}
      </div>

      {/* Captured by White (Black pieces taken) */}
      <div className="flex items-center justify-between min-h-[30px] pt-0.5">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs text-slate-400 font-medium mr-1">Captured Black:</span>
          {whiteCaptured.length === 0 ? (
            <span className="text-[11px] text-slate-500 italic">None</span>
          ) : (
            whiteCaptured.map((p, idx) => (
              <div key={idx} className="w-5 h-5 opacity-90 hover:opacity-100 transition-opacity">
                <PieceIcon piece={p.toLowerCase()} />
              </div>
            ))
          )}
        </div>
        {diff > 0 && (
          <span className="text-xs font-bold text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800/50">
            +{diff}
          </span>
        )}
      </div>
    </div>
  );
};
