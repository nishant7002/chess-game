import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ChessBoard } from './components/ChessBoard';
import { PromotionModal } from './components/PromotionModal';
import { MoveHistory } from './components/MoveHistory';
import { CapturedPieces } from './components/CapturedPieces';
import { AcademicPanel } from './components/AcademicPanel';
import { GameControls } from './components/GameControls';
import {
  Trophy,
  AlertTriangle,
  RefreshCw,
  User,
  Bot,
  Wifi,
  WifiOff
} from 'lucide-react';

const WS_URL = window.location.protocol === 'https:'
  ? `wss://${window.location.host}/ws`
  : `ws://${window.location.hostname}:8000/ws`;

export default function App() {
  // Game Configuration
  const [humanColor, setHumanColor] = useState('white');
  const [algorithm, setAlgorithm] = useState('alpha_beta_ordered');
  const [depth, setDepth] = useState(3);

  // Authoritative State from Server
  const [gameState, setGameState] = useState({
    fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
    turn: 'white',
    human_color: 'white',
    ai_color: 'black',
    is_human_turn: true,
    is_game_over: false,
    in_check: false,
    result: 'Game in progress',
    winner: null,
    last_move: null,
    move_history: [],
    captured_pieces: { white: [], black: [] },
    material: { white: 39, black: 39, diff: 0 }
  });

  // UI & Interaction States
  const [selectedSquare, setSelectedSquare] = useState(null);
  const [legalDestinations, setLegalDestinations] = useState([]);
  const [pendingPromotion, setPendingPromotion] = useState(null); // { from, to }
  const [isThinking, setIsThinking] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  // AI Telemetry
  const [lastAIMetrics, setLastAIMetrics] = useState(null);
  const [lastEval, setLastEval] = useState(0);

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const connectRef = useRef(null);

  // Connect to WebSocket
  const connectWebSocket = useCallback(() => {
    try {
      const socket = new WebSocket(WS_URL);
      wsRef.current = socket;

      socket.onopen = () => {
        setIsConnected(true);
        setErrorMessage(null);
        console.log('Connected to Chess AI server at', WS_URL);
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'game_state') {
            setGameState(data.state);
            if (data.state.human_color) setHumanColor(data.state.human_color);
            if (data.state.algorithm) setAlgorithm(data.state.algorithm);
            if (data.state.depth) setDepth(data.state.depth);
          } else if (data.type === 'ai_thinking') {
            setIsThinking(data.thinking);
          } else if (data.type === 'ai_move') {
            if (data.metrics) setLastAIMetrics(data.metrics);
            if (data.eval !== undefined) setLastEval(data.eval);
          } else if (data.type === 'legal_moves') {
            setLegalDestinations(data.destinations || []);
          } else if (data.type === 'error') {
            setErrorMessage(data.message);
            setTimeout(() => setErrorMessage(null), 4000);
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message', err);
        }
      };

      socket.onclose = () => {
        setIsConnected(false);
        // Attempt reconnection after 2 seconds
        if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = setTimeout(() => {
          connectRef.current?.();
        }, 2000);
      };

      socket.onerror = (err) => {
        console.error('WebSocket encountered error:', err);
        socket.close();
      };
    } catch (e) {
      console.error('Connection error:', e);
    }
  }, []);

  useEffect(() => {
    connectRef.current = connectWebSocket;
    connectWebSocket();
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    };
  }, [connectWebSocket]);

  const sendWsMessage = (msg) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    } else {
      setErrorMessage('Server connection not active. Reconnecting...');
    }
  };

  // Handle Starting a New Game
  const handleStartGame = () => {
    setSelectedSquare(null);
    setLegalDestinations([]);
    setErrorMessage(null);
    sendWsMessage({
      type: 'start_game',
      human_color: humanColor,
      algorithm: algorithm,
      depth: depth
    });
  };

  // Handle Restarting Game
  const handleRestartGame = () => {
    setSelectedSquare(null);
    setLegalDestinations([]);
    setErrorMessage(null);
    sendWsMessage({
      type: 'restart_game'
    });
  };

  // Handle Square Selection and Moves
  const handleSquareClick = (square, piece) => {
    if (gameState.is_game_over || isThinking || !gameState.is_human_turn) {
      return;
    }

    // 1. If clicking a legal destination for an already selected piece
    if (selectedSquare && legalDestinations.includes(square)) {
      // Check for pawn promotion: Pawn moving to rank 8 (for White) or rank 1 (for Black)
      const isWhitePawn = gameState.human_color === 'white' && selectedSquare[1] === '7' && square[1] === '8';
      const isBlackPawn = gameState.human_color === 'black' && selectedSquare[1] === '2' && square[1] === '1';

      if (isWhitePawn || isBlackPawn) {
        setPendingPromotion({ from: selectedSquare, to: square });
        return;
      }

      // Normal legal move
      const moveUci = `${selectedSquare}${square}`;
      sendWsMessage({
        type: 'make_move',
        move: moveUci
      });

      setSelectedSquare(null);
      setLegalDestinations([]);
      return;
    }

    // 2. If clicking on one of the player's own pieces
    if (piece) {
      const isPieceHuman =
        (gameState.human_color === 'white' && piece === piece.toUpperCase()) ||
        (gameState.human_color === 'black' && piece === piece.toLowerCase());

      if (isPieceHuman) {
        setSelectedSquare(square);
        sendWsMessage({
          type: 'get_legal_moves',
          square: square
        });
        return;
      }
    }

    // 3. Otherwise deselect
    setSelectedSquare(null);
    setLegalDestinations([]);
  };

  // Handle Pawn Promotion Selection
  const handlePromotionSelect = (promoType) => {
    if (!pendingPromotion) return;
    const moveUci = `${pendingPromotion.from}${pendingPromotion.to}${promoType}`;
    sendWsMessage({
      type: 'make_move',
      move: moveUci
    });
    setPendingPromotion(null);
    setSelectedSquare(null);
    setLegalDestinations([]);
  };

  const isHumanTurn = gameState.is_human_turn;
  const isGameOver = gameState.is_game_over;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navigation Bar */}
      <header className="bg-slate-900 border-b border-slate-800 px-4 py-3 sticky top-0 z-30 shadow-md">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center font-bold text-white shadow-md shadow-emerald-900/40">
              ♟
            </div>
            <div>
              <h1 className="text-base sm:text-lg font-bold tracking-tight text-white flex items-center gap-2">
                Real-Time Human vs AI Chess
                <span className="hidden sm:inline-block text-[11px] px-2 py-0.5 rounded-full bg-emerald-950/80 text-emerald-400 border border-emerald-800/80 font-mono">
                  Minimax & Alpha-Beta
                </span>
              </h1>
              <p className="text-xs text-slate-400 hidden sm:block">
                Foundations of Artificial Intelligence (FAI) Course Project
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Server Connection Status */}
            <div className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700">
              {isConnected ? (
                <>
                  <Wifi className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-slate-300 hidden sm:inline">Engine Online</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
                  <span className="text-amber-400 font-medium">Reconnecting...</span>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Error / Alert Banner */}
      {errorMessage && (
        <div className="bg-red-950/90 border-b border-red-800 text-red-200 text-xs px-4 py-2.5 flex items-center justify-center gap-2 animate-shake">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Container */}
      <main className="max-w-7xl mx-auto p-4 sm:p-6 w-full flex-1">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Chess Board & In-game HUD */}
          <div className="lg:col-span-7 flex flex-col items-center space-y-4">
            {/* Top Player Status: AI */}
            <div className="w-full max-w-[560px] flex items-center justify-between px-3 py-2 bg-slate-900/70 border border-slate-800/80 rounded-xl shadow-sm">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-cyan-400 border border-slate-700">
                  <Bot className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm font-semibold text-white">Custom AI Agent</span>
                    <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {gameState.ai_color}
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-400">
                    Strategy: {algorithm.replace(/_/g, ' ')} (Depth {depth})
                  </span>
                </div>
              </div>

              {isThinking && (
                <div className="flex items-center gap-2 text-xs text-amber-400 bg-amber-950/40 border border-amber-800/50 px-2.5 py-1 rounded-full animate-pulse">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Calculating move...</span>
                </div>
              )}
            </div>

            {/* Interactive Chess Board */}
            <ChessBoard
              fen={gameState.fen}
              humanColor={gameState.human_color}
              selectedSquare={selectedSquare}
              legalDestinations={legalDestinations}
              lastMove={gameState.last_move}
              inCheck={gameState.in_check}
              turn={gameState.turn}
              onSquareClick={handleSquareClick}
              disabled={isGameOver || isThinking || !isHumanTurn}
            />

            {/* Bottom Player Status: Human */}
            <div className="w-full max-w-[560px] flex items-center justify-between px-3 py-2 bg-slate-900/70 border border-slate-800/80 rounded-xl shadow-sm">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-emerald-400 border border-slate-700">
                  <User className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm font-semibold text-white">Human Player</span>
                    <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {gameState.human_color}
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-400">
                    {isHumanTurn && !isGameOver ? (
                      <span className="text-emerald-400 font-medium">Your turn to move</span>
                    ) : isGameOver ? (
                      <span className="text-slate-400">Game Over</span>
                    ) : (
                      <span className="text-slate-500">Waiting for AI move</span>
                    )}
                  </span>
                </div>
              </div>

              {/* Status Indicator */}
              {gameState.in_check && !isGameOver && (
                <div className="flex items-center gap-1.5 text-xs text-red-400 bg-red-950/60 border border-red-800/60 px-2.5 py-1 rounded-full font-bold animate-pulse">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>CHECK</span>
                </div>
              )}
            </div>

            {/* Captured Pieces & Material Advantage */}
            <div className="w-full max-w-[560px]">
              <CapturedPieces
                captured={gameState.captured_pieces}
                material={gameState.material}
              />
            </div>
          </div>

          {/* Right Column: Controls, Move History, Academic Telemetry */}
          <div className="lg:col-span-5 space-y-4">
            {/* Game Controls */}
            <GameControls
              humanColor={humanColor}
              setHumanColor={setHumanColor}
              algorithm={algorithm}
              setAlgorithm={setAlgorithm}
              depth={depth}
              setDepth={setDepth}
              onStartGame={handleStartGame}
              onRestartGame={handleRestartGame}
              isGameInProgress={gameState.move_history.length > 0 && !isGameOver}
              isThinking={isThinking}
              gameStatus={gameState.result}
            />

            {/* Move History */}
            <MoveHistory moves={gameState.move_history} />

            {/* Academic Search Telemetry Panel */}
            <AcademicPanel
              metrics={lastAIMetrics}
              lastEval={lastEval}
              isThinking={isThinking}
            />
          </div>
        </div>
      </main>

      {/* Pawn Promotion Modal */}
      <PromotionModal
        isOpen={Boolean(pendingPromotion)}
        color={gameState.human_color}
        onSelect={handlePromotionSelect}
      />

      {/* Game Over Banner / Dialog */}
      {isGameOver && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-fade-in">
          <div className="bg-slate-800 border-2 border-emerald-500/50 p-6 rounded-2xl shadow-2xl max-w-md w-full text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-emerald-950 border border-emerald-700/60 text-emerald-400 flex items-center justify-center mx-auto shadow-lg shadow-emerald-950">
              <Trophy className="w-8 h-8" />
            </div>

            <h2 className="text-2xl font-bold text-white tracking-tight">Game Over</h2>
            <p className="text-base font-semibold text-emerald-400">{gameState.result}</p>

            <div className="py-2 text-xs text-slate-400 bg-slate-900/60 rounded-lg border border-slate-700">
              Total Moves Played: {gameState.move_history.length}
            </div>

            <div className="flex gap-3 justify-center pt-2">
              <button
                type="button"
                onClick={handleStartGame}
                className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-bold rounded-xl shadow-md transition-all"
              >
                Play Again
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 py-3 px-4 text-center text-xs text-slate-500 mt-auto">
        Foundations of Artificial Intelligence (FAI) Course Project • Custom Minimax & Alpha-Beta Engine in Python
      </footer>
    </div>
  );
}
