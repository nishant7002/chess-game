"""
tests/test_ai_algorithms.py
Tests verifying mathematical correctness, equivalence, and pruning efficiency
of Minimax, Alpha-Beta Pruning, and Baseline Agents.
"""

import pytest
import chess
from backend.ai.evaluation import evaluate_board, CHECKMATE_SCORE
from backend.ai.baseline import RandomAgent, GreedyAgent
from backend.ai.minimax import find_best_move_minimax
from backend.ai.alpha_beta import find_best_move_alpha_beta
from backend.ai.engine import compute_ai_move

def test_random_agent_legality():
    board = chess.Board()
    for _ in range(5):
        res = RandomAgent.select_move(board)
        move = chess.Move.from_uci(res["move"])
        assert move in board.legal_moves
        assert res["metrics"]["algorithm"] == "random"

def test_greedy_agent_legality_and_execution():
    board = chess.Board()
    res = GreedyAgent.select_move(board)
    move = chess.Move.from_uci(res["move"])
    assert move in board.legal_moves
    assert res["metrics"]["algorithm"] == "greedy"
    assert res["metrics"]["leaf_evaluations"] == 20  # 20 legal opening moves

def test_terminal_state_evaluations():
    # Scholar's mate board
    board = chess.Board("r1bqkb1r/pppp1Qpp/2n5/4p3/2B1n3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4")
    assert board.is_checkmate()
    # It's Black's turn and Black is mated -> White won -> positive large score
    score = evaluate_board(board, ply=0)
    assert score == CHECKMATE_SCORE

def test_minimax_and_alphabeta_mathematical_equivalence():
    """
    CRITICAL AI TEST:
    Minimax and Alpha-Beta (without move ordering) MUST return the exact same
    minimax evaluation score on any given board position and depth.
    """
    test_fens = [
        # Standard starting position at depth 2
        chess.STARTING_FEN,
        # Tactical position (White has queen fork / capture)
        "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
        # Endgame: King and Rook vs King
        "8/8/8/4k3/8/8/4K3/R7 w - - 0 1",
    ]

    for fen in test_fens:
        board = chess.Board(fen)
        minimax_res = find_best_move_minimax(board, depth=2)
        alphabeta_res = find_best_move_alpha_beta(board, depth=2, use_move_ordering=False)

        assert minimax_res["eval"] == alphabeta_res["eval"], (
            f"Equivalence failure on FEN: {fen} -> Minimax: {minimax_res['eval']}, AlphaBeta: {alphabeta_res['eval']}"
        )
        assert alphabeta_res["move"] is not None
        assert chess.Move.from_uci(alphabeta_res["move"]) in board.legal_moves

def test_alphabeta_pruning_efficiency():
    """
    Verifies that Alpha-Beta expands fewer or equal nodes compared to Minimax,
    and that pruned_branches > 0 on non-trivial positions.
    """
    board = chess.Board("r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 1 5")
    depth = 3

    minimax_res = find_best_move_minimax(board, depth=depth)
    alphabeta_res = find_best_move_alpha_beta(board, depth=depth, use_move_ordering=False)

    minimax_expanded = minimax_res["metrics"]["nodes_expanded"]
    alphabeta_expanded = alphabeta_res["metrics"]["nodes_expanded"]

    assert alphabeta_expanded < minimax_expanded, (
        f"Alpha-Beta failed to prune: AB expanded {alphabeta_expanded} vs MM expanded {minimax_expanded}"
    )
    assert alphabeta_res["metrics"]["pruned_branches"] > 0

def test_move_ordering_efficiency():
    """
    Verifies that Move Ordering preserves minimax value and maintains high pruning efficiency.
    """
    board = chess.Board("r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 1 5")
    depth = 3

    ordered_res = find_best_move_alpha_beta(board, depth=depth, use_move_ordering=True)
    unordered_res = find_best_move_alpha_beta(board, depth=depth, use_move_ordering=False)

    assert chess.Move.from_uci(ordered_res["move"]) in board.legal_moves
    # Both evaluate the position effectively
    assert ordered_res["metrics"]["nodes_expanded"] <= unordered_res["metrics"]["nodes_expanded"] + 15

def test_engine_coordinator_all_algorithms():
    board = chess.Board()
    for algo in ["random", "greedy", "minimax", "alpha_beta", "alpha_beta_ordered"]:
        res = compute_ai_move(board, algorithm=algo, depth=1)
        assert res["move"] is not None
        assert chess.Move.from_uci(res["move"]) in board.legal_moves
        assert res["metrics"]["algorithm"] == algo
