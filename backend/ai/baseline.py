"""
backend/ai/baseline.py
Baseline AI Agents for Algorithmic Comparison:
1. RandomAgent: Selects uniformly from legal moves.
2. GreedyAgent: 1-ply search selecting the move with the highest immediate static evaluation.
"""

import time
import random
from typing import Dict, Any, Optional
import chess
from backend.ai.evaluation import evaluate_board

class RandomAgent:
    """Baseline Random Legal Move Agent."""
    @staticmethod
    def select_move(board: chess.Board) -> Dict[str, Any]:
        start_time = time.perf_counter()
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return {
                "move": None,
                "san": None,
                "eval": 0,
                "metrics": {
                    "algorithm": "random",
                    "depth": 0,
                    "runtime_ms": 0.0,
                    "nodes_generated": 0,
                    "nodes_expanded": 0,
                    "leaf_evaluations": 0,
                    "pruned_branches": 0
                }
            }

        chosen_move = random.choice(legal_moves)
        san_str = board.san(chosen_move)
        runtime_ms = (time.perf_counter() - start_time) * 1000.0

        # Evaluate the resulting board position for feedback
        board.push(chosen_move)
        eval_score = evaluate_board(board)
        board.pop()

        return {
            "move": chosen_move.uci(),
            "san": san_str,
            "eval": eval_score,
            "metrics": {
                "algorithm": "random",
                "depth": 0,
                "runtime_ms": round(runtime_ms, 2),
                "nodes_generated": len(legal_moves),
                "nodes_expanded": 1,
                "leaf_evaluations": 1,
                "pruned_branches": 0
            }
        }

class GreedyAgent:
    """Baseline 1-ply Greedy Evaluation Agent."""
    @staticmethod
    def select_move(board: chess.Board) -> Dict[str, Any]:
        start_time = time.perf_counter()
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return {
                "move": None,
                "san": None,
                "eval": 0,
                "metrics": {
                    "algorithm": "greedy",
                    "depth": 1,
                    "runtime_ms": 0.0,
                    "nodes_generated": 0,
                    "nodes_expanded": 0,
                    "leaf_evaluations": 0,
                    "pruned_branches": 0
                }
            }

        is_white = board.turn == chess.WHITE
        best_score = float('-inf') if is_white else float('inf')
        best_move = legal_moves[0]
        leaf_evals = 0

        for move in legal_moves:
            board.push(move)
            score = evaluate_board(board, ply=1)
            board.pop()
            leaf_evals += 1

            if is_white:
                if score > best_score:
                    best_score = score
                    best_move = move
            else:
                if score < best_score:
                    best_score = score
                    best_move = move

        san_str = board.san(best_move)
        runtime_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "move": best_move.uci(),
            "san": san_str,
            "eval": int(best_score),
            "metrics": {
                "algorithm": "greedy",
                "depth": 1,
                "runtime_ms": round(runtime_ms, 2),
                "nodes_generated": len(legal_moves),
                "nodes_expanded": 1,
                "leaf_evaluations": leaf_evals,
                "pruned_branches": 0
            }
        }
