"""
backend/ai/alpha_beta.py
Alpha-Beta Pruning Search Algorithm for Adversarial Chess AI.
Guarantees mathematically identical minimax evaluation to unpruned search
while aggressively pruning branches that cannot alter the minimax decision.
"""

import time
from typing import Tuple, Optional, Dict, Any, List
import chess
from backend.ai.evaluation import evaluate_board
from backend.ai.move_ordering import order_moves

class AlphaBetaMetrics:
    def __init__(self, algorithm_name: str = "alpha_beta"):
        self.algorithm_name = algorithm_name
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
            "algorithm": self.algorithm_name,
            "depth": depth,
            "runtime_ms": round(self.runtime_ms, 2),
            "nodes_generated": self.nodes_generated,
            "nodes_expanded": self.nodes_expanded,
            "leaf_evaluations": self.leaf_evaluations,
            "pruned_branches": self.pruned_branches
        }

def alpha_beta_search(
    board: chess.Board,
    depth: int,
    ply: int,
    alpha: float,
    beta: float,
    is_maximizing: bool,
    metrics: AlphaBetaMetrics,
    use_move_ordering: bool = False
) -> Tuple[Optional[chess.Move], int]:
    """
    Alpha-Beta search recursive routine.
    Returns (best_move, best_evaluation_score).
    """
    # Terminal check
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

    # Optional Move Ordering
    if use_move_ordering:
        moves_to_search = order_moves(board, legal_moves)
    else:
        moves_to_search = legal_moves

    best_move: Optional[chess.Move] = None

    if is_maximizing:
        # White turn: seeking to maximize evaluation score
        max_eval = -float('inf')
        for move in moves_to_search:
            board.push(move)
            _, score = alpha_beta_search(
                board, depth - 1, ply + 1, alpha, beta, False, metrics, use_move_ordering
            )
            board.pop()

            if score > max_eval:
                max_eval = score
                best_move = move

            alpha = max(alpha, max_eval)
            if beta <= alpha:
                metrics.pruned_branches += 1
                break  # Beta cutoff (prune remaining sibling branches)

        return best_move, int(max_eval)
    else:
        # Black turn: seeking to minimize evaluation score
        min_eval = float('inf')
        for move in moves_to_search:
            board.push(move)
            _, score = alpha_beta_search(
                board, depth - 1, ply + 1, alpha, beta, True, metrics, use_move_ordering
            )
            board.pop()

            if score < min_eval:
                min_eval = score
                best_move = move

            beta = min(beta, min_eval)
            if beta <= alpha:
                metrics.pruned_branches += 1
                break  # Alpha cutoff (prune remaining sibling branches)

        return best_move, int(min_eval)

def find_best_move_alpha_beta(
    board: chess.Board,
    depth: int,
    use_move_ordering: bool = False
) -> Dict[str, Any]:
    """Top-level entry point for Alpha-Beta search."""
    algo_name = "alpha_beta_ordered" if use_move_ordering else "alpha_beta"
    metrics = AlphaBetaMetrics(algorithm_name=algo_name)
    metrics.start_time = time.perf_counter()

    is_maximizing = (board.turn == chess.WHITE)
    alpha = -float('inf')
    beta = float('inf')

    best_move, best_eval = alpha_beta_search(
        board, depth, 0, alpha, beta, is_maximizing, metrics, use_move_ordering
    )

    metrics.end_time = time.perf_counter()

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
