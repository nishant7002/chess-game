"""
backend/ai/move_ordering.py
Move Ordering heuristics to optimize Alpha-Beta pruning cutoffs.
Explores high-potential moves (captures via MVV-LVA, promotions, checks) first.
"""

from typing import List, Optional
import chess
from backend.ai.evaluation import MATERIAL_VALUES, get_pst_value, is_endgame

def get_move_priority(board: chess.Board, move: chess.Move, endgame: bool) -> int:
    """
    Assigns an integer priority score to a move.
    Higher score indicates higher search priority.
    """
    score = 0
    piece = board.piece_at(move.from_square)
    if not piece:
        return 0

    # 1. Captures: MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
    if board.is_capture(move):
        victim_type = chess.PAWN
        if board.is_en_passant(move):
            victim_type = chess.PAWN
        else:
            victim_piece = board.piece_at(move.to_square)
            if victim_piece:
                victim_type = victim_piece.piece_type

        victim_val = MATERIAL_VALUES.get(victim_type, 100)
        attacker_val = MATERIAL_VALUES.get(piece.piece_type, 100)
        score += 10000 + (victim_val * 10) - attacker_val

    # 2. Pawn Promotion
    if move.promotion:
        score += 8000 + MATERIAL_VALUES.get(move.promotion, 900)

    # 3. Direct Checks
    if board.gives_check(move):
        score += 5000

    # 4. Castling
    if board.is_castling(move):
        score += 3000

    # 5. Positional piece-square improvement
    from_pst = get_pst_value(piece.piece_type, piece.color, move.from_square, endgame)
    to_pst = get_pst_value(piece.piece_type, piece.color, move.to_square, endgame)
    score += (to_pst - from_pst)

    return score

def order_moves(board: chess.Board, moves: List[chess.Move], pv_move: Optional[chess.Move] = None) -> List[chess.Move]:
    """Sorts legal moves descending by priority score, prioritizing pv_move if provided."""
    endgame = is_endgame(board)
    sorted_moves = sorted(moves, key=lambda m: get_move_priority(board, m, endgame), reverse=True)
    if pv_move and pv_move in sorted_moves:
        sorted_moves.remove(pv_move)
        sorted_moves.insert(0, pv_move)
    return sorted_moves
