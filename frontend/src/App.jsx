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
  WifiOff,
  Eye,
  RotateCcw,
  Play
} from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_WS_BACKEND_URL;

const WS_URL = BACKEND_URL
  ? BACKEND_URL
  : (window.location.protocol === 'https:'
      ? `wss://${window.location.host}/ws`
      : (window.location.port === '5173'
          ? `ws://${window.location.hostname}:8000/ws`
          : `ws://${window.location.host}/ws`));

// Helper to determine the piece character occupying a square from the FEN string
const getPieceAtSquare = (fen, square) => {
  if (!fen || !square || square.length !== 2) return null;
  const file = square.charCodeAt(0) - 'a'.charCodeAt(0);
  const rank = parseInt(square[1], 10);
  const r = 8 - rank;
  const f = file;
  if (r < 0 || r > 7 || f < 0 || f > 7) return null;

  const boardPart = fen.split(' ')[0];
  const rows = boardPart.split('/');
  if (!rows[r]) return null;

  let col = 0;
  for (const ch of rows[r]) {
    if (ch >= '1' && ch <= '8') {
      col += parseInt(ch, 10);
    } else {
      if (col === f) return ch;
      col++;
    }
  }
  return null;
};

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
  const [isGameStarted, setIsGameStarted] = useState(false);
  const [selectedSquare, setSelectedSquare] = useState(null);
  const [selectedPiece, setSelectedPiece] = useState(null);
  const [legalDestinations, setLegalDestinations] = useState([]);
  const [pendingPromotion, setPendingPromotion] = useState(null); // { from, to }
  const [isThinking, setIsThinking] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  // AI Telemetry
  const [lastAIMetrics, setLastAIMetrics] = useState(null);
  const [lastEval, setLastEval] = useState(0);

  // Game Over Modal visibility & delay timer
  const [showGameOverModal, setShowGameOverModal] = useState(false);
  const gameOverTimeoutRef = useRef(null);

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
            if (data.state.move_history && data.state.move_history.length === 0) {
              setLastAIMetrics(null);
              setLastEval(0);
            }
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

  // Monitor Game Over: allow user to inspect the decisive move on the board for 1.8s
  useEffect(() => {
    if (gameState.is_game_over) {
      if (gameOverTimeoutRef.current) clearTimeout(gameOverTimeoutRef.current);
      gameOverTimeoutRef.current = setTimeout(() => {
        setShowGameOverModal(true);
      }, 1800);
    } else {
      setShowGameOverModal(false);
      if (gameOverTimeoutRef.current) clearTimeout(gameOverTimeoutRef.current);
    }
    return () => {
      if (gameOverTimeoutRef.current) clearTimeout(gameOverTimeoutRef.current);
    };
  }, [gameState.is_game_over]);

  const sendWsMessage = (msg) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    } else {
      setErrorMessage('Server connection not active. Reconnecting...');
    }
  };

  // Handle Color Selection (configures player color before starting)
  const handleColorChange = (newColor) => {
    setHumanColor(newColor);
    setSelectedSquare(null);
    setSelectedPiece(null);
    setLegalDestinations([]);
    // Immediately orient the board for the chosen color
    setGameState(prev => ({
      ...prev,
      human_color: newColor,
      ai_color: newColor === 'white' ? 'black' : 'white',
      is_human_turn: newColor === 'white'
    }));
  };

  // Handle Algorithm Strategy Selection
  const handleAlgorithmChange = (newAlgo) => {
    setAlgorithm(newAlgo);
    sendWsMessage({
      type: 'update_settings',
      algorithm: newAlgo,
      depth: depth
    });
  };

  // Handle Search Depth Change
  const handleDepthChange = (newDepth) => {
    setDepth(newDepth);
    sendWsMessage({
      type: 'update_settings',
      algorithm: algorithm,
      depth: newDepth
    });
  };

  // Seamless state reset helper for both optimistic UI and server sync
  const resetToFreshGameState = (isStarted = true) => {
    const isHumanWhite = humanColor === 'white';
    setIsGameStarted(isStarted);
    setShowGameOverModal(false);
    if (gameOverTimeoutRef.current) clearTimeout(gameOverTimeoutRef.current);
    setSelectedSquare(null);
    setSelectedPiece(null);
    setLegalDestinations([]);
    setPendingPromotion(null);
    setErrorMessage(null);
    setLastAIMetrics(null);
    setLastEval(0);
    // If game is started and human is Black, AI (White) begins calculating immediately
    setIsThinking(isStarted && !isHumanWhite);

    setGameState({
      fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
      turn: 'white',
      human_color: humanColor,
      ai_color: isHumanWhite ? 'black' : 'white',
      is_human_turn: isStarted ? isHumanWhite : isHumanWhite,
      is_game_over: false,
      in_check: false,
      result: isStarted ? 'Game in progress' : 'Choose options and click Start Game',
      winner: null,
      last_move: null,
      move_history: [],
      captured_pieces: { white: [], black: [] },
      material: { white: 39, black: 39, diff: 0 }
    });
  };

  // Handle Starting the Game after options have been chosen
  const handleStartGame = () => {
    resetToFreshGameState(true);
    sendWsMessage({
      type: 'start_game',
      human_color: humanColor,
      algorithm: algorithm,
      depth: depth
    });
  };

  // Handle Restarting Game with current options
  const handleRestartGame = () => {
    resetToFreshGameState(true);
    sendWsMessage({
      type: 'start_game',
      human_color: humanColor,
      algorithm: algorithm,
      depth: depth
    });
  };

  // Handle New Game (returns to setup mode so user can re-choose options)
  const handleNewGame = () => {
    resetToFreshGameState(false);
  };

  // Handle Square Selection and Moves
  const handleSquareClick = (square, piece) => {
    if (!isGameStarted) {
      setErrorMessage("Please click 'Start Game' to begin playing!");
      setTimeout(() => setErrorMessage(null), 3000);
      return;
    }

    if (gameState.is_game_over || isThinking || !gameState.is_human_turn) {
      return;
    }

    // 1. If clicking a legal destination for an already selected piece
    if (selectedSquare && legalDestinations.includes(square)) {
      // Check for pawn promotion: ONLY if the selected piece is actually a Pawn ('P' or 'p')
      const movingPiece = selectedPiece || getPieceAtSquare(gameState.fen, selectedSquare);
      const isPawn = movingPiece && movingPiece.toUpperCase() === 'P';

      const isWhitePawnPromo = isPawn && gameState.human_color === 'white' && selectedSquare[1] === '7' && square[1] === '8';
      const isBlackPawnPromo = isPawn && gameState.human_color === 'black' && selectedSquare[1] === '2' && square[1] === '1';

      if (isWhitePawnPromo || isBlackPawnPromo) {
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
      setSelectedPiece(null);
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
        setSelectedPiece(piece);
        sendWsMessage({
          type: 'get_legal_moves',
          square: square
        });
        return;
      }
    }

    // 3. Otherwise deselect
    setSelectedSquare(null);
    setSelectedPiece(null);
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
    setSelectedPiece(null);
    setLegalDestinations([]);
  };

  const isHumanTurn = gameState.is_human_turn;
  const isGameOver = gameState.is_game_over;

  const lastMoveRecord =
    gameState.move_history && gameState.move_history.length > 0
      ? gameState.move_history[gameState.move_history.length - 1]
      : (gameState.last_move
          ? {
              san: gameState.last_move.san || gameState.last_move.uci,
              uci: gameState.last_move.uci,
              from: gameState.last_move.from,
              to: gameState.last_move.to,
              turn: gameState.turn === 'white' ? 'black' : 'white',
              captured: null
            }
          : null);

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
                Self-Learning Chess AI Engine Project
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
          {/* 1. Pre-Game Settings (Top on Mobile, Left on Desktop) */}
          <div className="order-1 lg:col-span-5 lg:col-start-1 lg:row-start-1 w-full">
            <GameControls
              humanColor={humanColor}
              onColorChange={handleColorChange}
              algorithm={algorithm}
              onAlgorithmChange={handleAlgorithmChange}
              depth={depth}
              onDepthChange={handleDepthChange}
              isGameStarted={isGameStarted}
              onStartGame={handleStartGame}
              onNewGame={handleNewGame}
              onRestartGame={handleRestartGame}
              isThinking={isThinking}
              _gameStatus={gameState.result}
            />
          </div>

          {/* 2. Chess Board & In-game HUD (After Settings on Mobile, Right side on Desktop) */}
          <div className="order-2 lg:col-span-7 lg:col-start-6 lg:row-start-1 lg:row-span-2 flex flex-col items-center space-y-4 w-full">
            {/* Decisive End-Game Floating Review Banner (Visible when reviewing board after game over) */}
            {isGameOver && !showGameOverModal && (
              <div className="w-full max-w-[560px] bg-slate-900/95 border-2 border-emerald-500/60 rounded-xl p-3 shadow-xl flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 animate-fade-in">
                <div className="flex items-center gap-2.5 min-w-0 flex-1">
                  <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/40 flex items-center justify-center shrink-0">
                    <Trophy className="w-4 h-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs sm:text-sm font-bold text-white truncate">{gameState.result}</p>
                    {lastMoveRecord && (
                      <p className="text-[11px] text-slate-300 font-mono truncate">
                        Final Move:{' '}
                        <span className="text-emerald-400 font-bold">{lastMoveRecord.san || lastMoveRecord.uci}</span>
                        {' '}({lastMoveRecord.from} → {lastMoveRecord.to})
                        {' '}• <span className="text-slate-400">{lastMoveRecord.turn === gameState.human_color ? 'You' : 'AI'}</span>
                      </p>
                    )}
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-1.5 w-full sm:w-auto sm:flex sm:items-center sm:gap-2 shrink-0 pt-1.5 sm:pt-0 border-t border-slate-800/80 sm:border-0">
                  <button
                    type="button"
                    onClick={() => setShowGameOverModal(true)}
                    className="w-full sm:w-auto justify-center px-2 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-lg border border-slate-600 shadow-sm transition-all flex items-center gap-1.5 whitespace-nowrap"
                  >
                    <Trophy className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                    <span>Summary</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleRestartGame}
                    className="w-full sm:w-auto justify-center px-2 py-1.5 text-xs bg-slate-700 hover:bg-slate-600 text-slate-200 font-semibold rounded-lg border border-slate-600 shadow-sm transition-all flex items-center gap-1.5 whitespace-nowrap"
                  >
                    <RotateCcw className="w-3.5 h-3.5 text-slate-300 shrink-0" />
                    <span>Restart</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleNewGame}
                    className="w-full sm:w-auto justify-center px-2.5 py-1.5 text-xs bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg shadow-sm transition-all flex items-center gap-1 whitespace-nowrap"
                  >
                    <Play className="w-3.5 h-3.5 shrink-0" />
                    <span>New Game</span>
                  </button>
                </div>
              </div>
            )}

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
              disabled={!isGameStarted || isGameOver || isThinking || !isHumanTurn}
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
                    {!isGameStarted ? (
                      <span className="text-amber-400 font-medium">Ready — Choose options & click Start Game</span>
                    ) : isHumanTurn && !isGameOver ? (
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

          {/* 3. Move History & Academic Search Telemetry (Below Board on Mobile, Left Column on Desktop) */}
          <div className="order-3 lg:col-span-5 lg:col-start-1 lg:row-start-2 space-y-4 w-full">
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

      {/* Game Over Banner / Dialog with Review Board option and Decisive Move */}
      {showGameOverModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-fade-in"
          onClick={() => setShowGameOverModal(false)}
        >
          <div
            className="bg-slate-800 border-2 border-emerald-500/50 p-6 rounded-2xl shadow-2xl max-w-md w-full text-center space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="w-16 h-16 rounded-full bg-emerald-950 border border-emerald-700/60 text-emerald-400 flex items-center justify-center mx-auto shadow-lg shadow-emerald-950">
              <Trophy className="w-8 h-8" />
            </div>

            <h2 className="text-2xl font-bold text-white tracking-tight">Game Over</h2>
            <p className="text-base font-semibold text-emerald-400">{gameState.result}</p>

            {/* Decisive Last Move Card */}
            {lastMoveRecord && (
              <div className="bg-slate-900/90 border border-slate-700/90 rounded-xl p-3 text-left space-y-1.5">
                <div className="text-[11px] text-slate-400 uppercase font-mono tracking-wider flex items-center justify-between">
                  <span>Decisive Final Move</span>
                  <span className={`font-semibold px-2 py-0.5 rounded text-[10px] ${
                    lastMoveRecord.turn === gameState.human_color
                      ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                      : 'bg-cyan-950 text-cyan-400 border border-cyan-800'
                  }`}>
                    {lastMoveRecord.turn === gameState.human_color ? 'You (Human)' : 'AI Engine'}
                  </span>
                </div>
                <div className="flex items-center justify-between pt-1">
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-mono font-bold text-white bg-slate-800 px-3 py-1 rounded-lg border border-slate-700 shadow-inner">
                      {lastMoveRecord.san || lastMoveRecord.uci}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">
                      ({lastMoveRecord.from} → {lastMoveRecord.to})
                    </span>
                  </div>
                  {lastMoveRecord.captured && (
                    <span className="text-xs text-red-300 bg-red-950/80 border border-red-800/80 px-2.5 py-1 rounded font-medium">
                      Captured {lastMoveRecord.captured.toUpperCase()}
                    </span>
                  )}
                </div>
              </div>
            )}

            <div className="py-2 text-xs text-slate-400 bg-slate-900/60 rounded-lg border border-slate-700 flex justify-around">
              <span>Total Moves: <strong className="text-white font-mono">{gameState.move_history.length}</strong></span>
              <span>Final Turn: <strong className="text-white font-mono capitalize">{gameState.turn}</strong></span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowGameOverModal(false)}
                className="w-full justify-center px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-semibold rounded-xl border border-slate-600 shadow-sm transition-all flex items-center gap-1.5"
              >
                <Eye className="w-3.5 h-3.5" />
                <span>Review Board</span>
              </button>
              <button
                type="button"
                onClick={handleRestartGame}
                className="w-full justify-center px-3.5 py-2 bg-slate-600 hover:bg-slate-500 text-white text-xs font-semibold rounded-xl shadow-md transition-all flex items-center gap-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Restart Game</span>
              </button>
              <button
                type="button"
                onClick={handleNewGame}
                className="w-full justify-center px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl shadow-md transition-all flex items-center gap-1.5"
              >
                <Play className="w-3.5 h-3.5" />
                <span>New Game</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 py-3 px-4 text-center text-xs text-slate-500 mt-auto">
        Self-Learning Chess AI Project • Custom Minimax & Alpha-Beta Engine in Python
      </footer>
    </div>
  );
}
