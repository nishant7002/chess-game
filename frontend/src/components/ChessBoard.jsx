import React from 'react';
import { PieceIcon } from './ChessPieces';

// Parses FEN string into an 8x8 board array: board[rankIndex][fileIndex]
// rankIndex 0 is rank 8, rankIndex 7 is rank 1
// fileIndex 0 is file a, fileIndex 7 is file h
export const parseFen = (fen) => {
  if (!fen) return Array(8).fill(null).map(() => Array(8).fill(null));
  const boardPart = fen.split(' ')[0];
  const rows = boardPart.split('/');
  const board = [];

  for (let r = 0; r < 8; r++) {
    const row = [];
    const rowStr = rows[r] || '';
    for (let c = 0; c < rowStr.length; c++) {
      const char = rowStr[c];
      if (char >= '1' && char <= '8') {
        const emptyCount = parseInt(char, 10);
        for (let e = 0; e < emptyCount; e++) row.push(null);
      } else {
        row.push(char);
      }
    }
    board.push(row);
  }
  return board;
};

export const ChessBoard = ({
  fen,
  humanColor = 'white',
  selectedSquare,
  legalDestinations = [],
  lastMove,
  inCheck,
  turn,
  onSquareClick,
  disabled = false
}) => {
  const boardGrid = parseFen(fen);
  const isFlipped = humanColor === 'black';

  // Files: 0 -> 'a', 7 -> 'h'
  // Ranks: 0 -> 8, 7 -> 1
  const ranks = isFlipped ? [0, 1, 2, 3, 4, 5, 6, 7] : [0, 1, 2, 3, 4, 5, 6, 7];
  const files = isFlipped ? [7, 6, 5, 4, 3, 2, 1, 0] : [0, 1, 2, 3, 4, 5, 6, 7];

  // Helper to map (rankIdx, fileIdx) to algebraic name like "e4"
  const getSquareName = (r, f) => {
    const fileChar = String.fromCharCode('a'.charCodeAt(0) + f);
    const rankNum = 8 - r;
    return `${fileChar}${rankNum}`;
  };

  // Find king square if in check
  let checkedKingSquare = null;
  if (inCheck) {
    const kingChar = turn === 'white' ? 'K' : 'k';
    for (let r = 0; r < 8; r++) {
      for (let f = 0; f < 8; f++) {
        if (boardGrid[r][f] === kingChar) {
          checkedKingSquare = getSquareName(r, f);
          break;
        }
      }
      if (checkedKingSquare) break;
    }
  }

  return (
    <div className="relative select-none aspect-square w-full max-w-[560px] mx-auto rounded-xl shadow-2xl p-2.5 bg-gradient-to-br from-amber-950 via-stone-900 to-amber-950 border-4 border-amber-900/60">
      <div className="grid grid-cols-8 grid-rows-8 w-full h-full rounded-lg overflow-hidden border border-black/40">
        {ranks.map((r) => {
          const actualR = isFlipped ? 7 - r : r;
          return files.map((f) => {
            const squareName = getSquareName(actualR, f);
            const piece = boardGrid[actualR][f];
            const isLight = (actualR + f) % 2 === 0;
            const isSelected = selectedSquare === squareName;
            const isLegalDest = legalDestinations.includes(squareName);
            const isLastMoveFrom = lastMove && lastMove.from === squareName;
            const isLastMoveTo = lastMove && lastMove.to === squareName;
            const isChecked = checkedKingSquare === squareName;

            // Base square colors
            let bgClass = isLight ? 'bg-[#f0d9b5]' : 'bg-[#b58863]';

            // Highlighting overlays
            if (isLastMoveFrom || isLastMoveTo) {
              bgClass = isLight ? 'bg-[#cdd26a]' : 'bg-[#aaa23a]';
            }
            if (isSelected) {
              bgClass = 'bg-[#7ca982] ring-4 ring-inset ring-emerald-400';
            }
            if (isChecked) {
              bgClass = 'bg-red-500/80 ring-4 ring-inset ring-red-600 animate-pulse';
            }

            return (
              <div
                key={squareName}
                onClick={() => !disabled && onSquareClick(squareName, piece)}
                className={`relative flex items-center justify-center cursor-pointer transition-colors duration-150 ${bgClass}`}
                data-square={squareName}
              >
                {/* Board Rank & File Labels */}
                {f === (isFlipped ? 7 : 0) && (
                  <span
                    className={`absolute top-0.5 left-1 text-[10px] font-bold pointer-events-none ${
                      isLight ? 'text-[#b58863]' : 'text-[#f0d9b5]'
                    }`}
                  >
                    {8 - actualR}
                  </span>
                )}
                {r === (isFlipped ? 0 : 7) && (
                  <span
                    className={`absolute bottom-0.5 right-1 text-[10px] font-bold pointer-events-none ${
                      isLight ? 'text-[#b58863]' : 'text-[#f0d9b5]'
                    }`}
                  >
                    {String.fromCharCode('a'.charCodeAt(0) + f)}
                  </span>
                )}

                {/* Piece Vector */}
                {piece && (
                  <div className="w-[82%] h-[82%] z-10 transition-transform duration-150 hover:scale-105 pointer-events-none">
                    <PieceIcon piece={piece} />
                  </div>
                )}

                {/* Legal Move Indicators */}
                {isLegalDest && !piece && (
                  <div className="absolute w-3.5 h-3.5 rounded-full bg-slate-900/35 pointer-events-none z-20 shadow-sm" />
                )}
                {isLegalDest && piece && (
                  <div className="absolute inset-0.5 rounded-full ring-4 ring-red-500/50 pointer-events-none z-20" />
                )}
              </div>
            );
          });
        })}
      </div>
    </div>
  );
};
