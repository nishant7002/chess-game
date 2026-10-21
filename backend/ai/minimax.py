"""
backend/ai/minimax.py
Pure Depth-Limited Minimax Search without Pruning.
Implements the canonical alternating two-player zero-sum adversarial search.
White maximizes score; Black minimizes score.
"""

import time
from typing import Tuple, Optional, Dict, Any, List
import chess
from backend.ai.evaluation import evaluate_board, CHECKMATE_SCORE

class MinimaxMetrics:
    def __init__(self):
        self.nodes_generated = 0
        self.nodes_expanded = 0
        self.leaf_evaluations = 0
        self.pruned_branches = 0
        self.start_time = 0.0
        self.end_time = 0.0

    @property
    def runtime_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000.0

    def to_dict(self, depth: int) -> Dict[str, Any]:
        return {
            "algorithm": "minimax",
            "depth": depth,
            "runtime_ms": round(self.runtime_ms, 2),
            "nodes_generated": self.nodes_generated,
            "nodes_expanded": self.nodes_expanded,
            "leaf_evaluations": self.leaf_evaluations,
            "pruned_branches": 0
        }

def minimax_search(
    board: chess.Board,
    depth: int,
    ply: int,
    is_maximizing: bool,
    metrics: MinimaxMetrics
) -> Tuple[Optional[chess.Move], int]:
    """
    Recursive depth-limited Minimax search.
    Returns (best_move, best_evaluation_score).
    """
    # Terminal state check
    if board.is_game_over():
        metrics.leaf_evaluations += 1
        return None, evaluate_board(board, ply)

    # Depth limit reached
    if depth == 0:
        metrics.leaf_evaluations += 1
        return None, evaluate_board(board, ply)

    legal_moves = list(board.legal_moves)
    if not legal_moves:
        metrics.leaf_evaluations += 1
        return None, evaluate_board(board, ply)

    metrics.nodes_expanded += 1
    metrics.nodes_generated += len(legal_moves)

    best_move: Optional[chess.Move] = None

    if is_maximizing:
        # White turn: maximize evaluation
        max_eval = -float('inf')
        for move in legal_moves:
            board.push(move)
            _, score = minimax_search(board, depth - 1, ply + 1, False, metrics)
            board.pop()

            if score > max_eval:
                max_eval = score
                best_move = move

        return best_move, int(max_eval)
    else:
        # Black turn: minimize evaluation
        min_eval = float('inf')
        for move in legal_moves:
            board.push(move)
            _, score = minimax_search(board, depth - 1, ply + 1, True, metrics)
            board.pop()

            if score < min_eval:
                min_eval = score
                best_move = move

        return best_move, int(min_eval)

def find_best_move_minimax(board: chess.Board, depth: int) -> Dict[str, Any]:
    """Top-level entry point for Minimax move selection."""
    metrics = MinimaxMetrics()
    metrics.start_time = time.perf_counter()

    is_maximizing = (board.turn == chess.WHITE)
    best_move, best_eval = minimax_search(board, depth, 0, is_maximizing, metrics)

    metrics.end_time = time.perf_counter()

    # Fallback to first legal move if none selected (e.g. at depth 0)
    if best_move is None:
        legal_moves = list(board.legal_moves)
        if legal_moves:
            best_move = legal_moves[0]

    san_str = board.san(best_move) if best_move else None
    uci_str = best_move.uci() if best_move else None

    return {
        "move": uci_str,
        "san": san_str,
        "eval": best_eval,
        "metrics": metrics.to_dict(depth)
    }
