"""
backend/ai/evaluation.py
Heuristic Chess Position Evaluation Function.
Calculates position evaluation from White's perspective (+ for White, - for Black).
Centipawn scale (100 cp = 1 pawn).
"""

from typing import Dict
import chess

# Material Values in centipawns
MATERIAL_VALUES: Dict[chess.PieceType, int] = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}

CHECKMATE_SCORE = 100000
DRAW_SCORE = 0

# Piece-Square Tables (oriented for White, mirrored for Black rank by rank)
# Higher values reward placing pieces on squares that maximize control and safety.

PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_TABLE = [
   -50,-40,-30,-30,-30,-30,-40,-50,
   -40,-20,  0,  0,  0,  0,-20,-40,
   -30,  0, 10, 15, 15, 10,  0,-30,
   -30,  5, 15, 20, 20, 15,  5,-30,
   -30,  0, 15, 20, 20, 15,  0,-30,
   -30,  5, 10, 15, 15, 10,  5,-30,
   -40,-20,  0,  5,  5,  0,-20,-40,
   -50,-40,-30,-30,-30,-30,-40,-50
]

BISHOP_TABLE = [
   -20,-10,-10,-10,-10,-10,-10,-20,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -10,  0,  5, 10, 10,  5,  0,-10,
   -10,  5,  5, 10, 10,  5,  5,-10,
   -10,  0, 10, 10, 10, 10,  0,-10,
   -10, 10, 10, 10, 10, 10, 10,-10,
   -10,  5,  0,  0,  0,  0,  5,-10,
   -20,-10,-10,-10,-10,-10,-10,-20
]

ROOK_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0
]

QUEEN_TABLE = [
   -20,-10,-10, -5, -5,-10,-10,-20,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
     0,  0,  5,  5,  5,  5,  0, -5,
   -10,  5,  5,  5,  5,  5,  0,-10,
   -10,  0,  5,  0,  0,  0,  0,-10,
   -20,-10,-10, -5, -5,-10,-10,-20
]

KING_MIDGAME_TABLE = [
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -20,-30,-30,-40,-40,-30,-30,-20,
   -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20
]

KING_ENDGAME_TABLE = [
   -50,-40,-30,-20,-20,-30,-40,-50,
   -30,-20,-10,  0,  0,-10,-20,-30,
   -30,-10, 20, 30, 30, 20,-10,-30,
   -30,-10, 30, 40, 40, 30,-10,-30,
   -30,-10, 30, 40, 40, 30,-10,-30,
   -30,-10, 20, 30, 30, 20,-10,-30,
   -30,-30,  0,  0,  0,  0,-30,-30,
   -50,-30,-30,-30,-30,-30,-30,-50
]

PIECE_TABLES = {
    chess.PAWN: PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK: ROOK_TABLE,
    chess.QUEEN: QUEEN_TABLE
}

def is_endgame(board: chess.Board) -> bool:
    """Determines if the position is an endgame based on minor/major pieces present."""
    major_minor_count = len(board.pieces(chess.QUEEN, chess.WHITE)) + \
                        len(board.pieces(chess.QUEEN, chess.BLACK)) + \
                        len(board.pieces(chess.ROOK, chess.WHITE)) + \
                        len(board.pieces(chess.ROOK, chess.BLACK)) + \
                        len(board.pieces(chess.BISHOP, chess.WHITE)) + \
                        len(board.pieces(chess.BISHOP, chess.BLACK)) + \
                        len(board.pieces(chess.KNIGHT, chess.WHITE)) + \
                        len(board.pieces(chess.KNIGHT, chess.BLACK))
    return major_minor_count <= 6

def get_pst_value(piece_type: chess.PieceType, color: chess.Color, square: chess.Square, in_endgame: bool) -> int:
    """Calculates piece-square table positional bonus for a piece at square."""
    if piece_type == chess.KING:
        table = KING_ENDGAME_TABLE if in_endgame else KING_MIDGAME_TABLE
    else:
        table = PIECE_TABLES.get(piece_type, [0] * 64)

    # For White: rank 1 is index 56-63, rank 8 is index 0-7
    # chess.Square index is 0 (a1) to 63 (h8)
    # The tables are written rank 8 (top) to rank 1 (bottom).
    # To map square (0..63) to table index:
    # rank 0 (rank 1) -> table rows 7 (indices 56..63)
    # rank 7 (rank 8) -> table rows 0 (indices 0..7)
    file_idx = chess.square_file(square)
    rank_idx = chess.square_rank(square)

    if color == chess.WHITE:
        table_idx = (7 - rank_idx) * 8 + file_idx
    else:
        # Mirror rank for Black
        table_idx = rank_idx * 8 + file_idx

    return table[table_idx]

def evaluate_board(board: chess.Board, ply: int = 0) -> int:
    """
    Evaluates the board state from White's perspective (+ = White advantage, - = Black advantage).
    Returns an integer score in centipawns.
    Handles terminal states (checkmate and draws) consistently.
    """
    # 1. Terminal State Checks
    if board.is_checkmate():
        # If it's White's turn and checkmated, Black won -> negative score.
        # Include ply to reward faster wins and slower losses.
        if board.turn == chess.WHITE:
            return -CHECKMATE_SCORE + ply
        else:
            return CHECKMATE_SCORE - ply

    if (
        board.is_stalemate()
        or board.is_insufficient_material()
        or board.is_fifty_moves()
        or board.is_repetition(3)
    ):
        return DRAW_SCORE

    # 2. Material and Piece-Square Table Positional Scoring
    endgame = is_endgame(board)
    material_score = 0
    pst_score = 0

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None:
            continue

        val = MATERIAL_VALUES[piece.piece_type]
        pst = get_pst_value(piece.piece_type, piece.color, square, endgame)

        if piece.color == chess.WHITE:
            material_score += val
            pst_score += pst
        else:
            material_score -= val
            pst_score -= pst

    # 3. Mobility bonus (approximate legal moves differential)
    # Give a small bonus (2 centipawns per legal move) for activity
    mobility_score = 0
    current_legal_moves = board.legal_moves.count()
    if board.turn == chess.WHITE:
        mobility_score += current_legal_moves * 2
    else:
        mobility_score -= current_legal_moves * 2

    # 4. Total heuristic score
    total_score = material_score + pst_score + mobility_score
    return total_score
