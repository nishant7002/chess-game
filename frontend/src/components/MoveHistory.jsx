import React, { useEffect, useRef } from 'react';
import { ScrollText } from 'lucide-react';

export const MoveHistory = ({ moves = [] }) => {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [moves]);

  // Group moves into turns: [{ moveNum: 1, white: 'e4', black: 'e5' }, ...]
  const turns = [];
  for (let i = 0; i < moves.length; i += 2) {
    const moveNum = Math.floor(i / 2) + 1;
    const whiteMove = moves[i] ? moves[i].san : '';
    const blackMove = moves[i + 1] ? moves[i + 1].san : '';
    turns.push({ moveNum, white: whiteMove, black: blackMove });
  }

  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-4 flex flex-col h-[280px] shadow-lg">
      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-slate-700/60">
        <ScrollText className="w-4 h-4 text-emerald-400" />
        <h3 className="text-sm font-semibold text-slate-200">Move History (Algebraic Notation)</h3>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-1 pr-1 font-mono text-sm scrollbar-thin">
        {turns.length === 0 ? (
          <p className="text-xs text-slate-500 italic text-center py-8">No moves played yet.</p>
        ) : (
          turns.map((turn) => (
            <div
              key={turn.moveNum}
              className="grid grid-cols-12 py-1 px-2 rounded hover:bg-slate-700/40 text-xs transition-colors"
            >
              <span className="col-span-2 text-slate-500">{turn.moveNum}.</span>
              <span className="col-span-5 text-slate-200 font-medium">{turn.white}</span>
              <span className="col-span-5 text-slate-300 font-medium">{turn.black}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
