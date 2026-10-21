import React from 'react';
import { PieceIcon } from './ChessPieces';

export const PromotionModal = ({ isOpen, color = 'white', onSelect }) => {
  if (!isOpen) return null;

  const pieces = ['q', 'r', 'b', 'n'];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-800 border border-slate-700 p-6 rounded-2xl shadow-2xl max-w-sm w-full mx-4 text-center">
        <h3 className="text-xl font-bold text-white mb-2">Pawn Promotion</h3>
        <p className="text-sm text-slate-400 mb-6">Choose a piece to promote your pawn:</p>
        <div className="grid grid-cols-4 gap-3">
          {pieces.map((type) => {
            const pieceChar = color === 'white' ? type.toUpperCase() : type;
            return (
              <button
                key={type}
                onClick={() => onSelect(type)}
                className="flex flex-col items-center justify-center p-3 bg-slate-700/60 hover:bg-emerald-600/30 hover:border-emerald-500 border border-slate-600 rounded-xl transition-all duration-200 group"
              >
                <div className="w-12 h-12 transition-transform group-hover:scale-110">
                  <PieceIcon piece={pieceChar} />
                </div>
                <span className="text-xs uppercase font-semibold text-slate-300 mt-2">
                  {type === 'q' ? 'Queen' : type === 'r' ? 'Rook' : type === 'b' ? 'Bishop' : 'Knight'}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
