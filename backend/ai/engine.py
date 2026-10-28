"""
backend/ai/engine.py
Central AI Engine Coordinator for Chess Agent Move Selection.
Provides a unified interface across all algorithmic strategies.
"""

from typing import Dict, Any
import chess
from backend.ai.baseline import RandomAgent, GreedyAgent
from backend.ai.minimax import find_best_move_minimax
from backend.ai.alpha_beta import find_best_move_alpha_beta

VALID_ALGORITHMS = ["random", "greedy", "minimax", "alpha_beta", "alpha_beta_ordered"]

def compute_ai_move(board: chess.Board, algorithm: str = "alpha_beta", depth: int = 3) -> Dict[str, Any]:
    """
    Computes best legal move according to chosen AI algorithm and search depth.
    Safely handles edge cases and returns standard response dictionary.
    """
    if board.is_game_over() or not list(board.legal_moves):
        return {
            "move": None,
            "san": None,
            "eval": 0,
            "metrics": {
                "algorithm": algorithm,
                "depth": depth,
                "runtime_ms": 0.0,
                "nodes_generated": 0,
                "nodes_expanded": 0,
                "leaf_evaluations": 0,
                "pruned_branches": 0
            }
        }

    algo_key = algorithm.lower().strip()

    # Algorithm-specific safe depth clamping to prevent CPU exhaustion DoS
    if algo_key == "minimax":
        safe_depth = max(1, min(depth, 3))
        return find_best_move_minimax(board, safe_depth)
    elif algo_key == "random":
        return RandomAgent.select_move(board)
    elif algo_key == "greedy":
        return GreedyAgent.select_move(board)
    elif algo_key == "alpha_beta_ordered":
        safe_depth = max(1, min(depth, 4))
        return find_best_move_alpha_beta(board, safe_depth, use_move_ordering=True)
    elif algo_key == "alpha_beta":
        safe_depth = max(1, min(depth, 4))
        return find_best_move_alpha_beta(board, safe_depth, use_move_ordering=False)
    else:
        # Default fallback
        safe_depth = max(1, min(depth, 4))
        return find_best_move_alpha_beta(board, safe_depth, use_move_ordering=True)
