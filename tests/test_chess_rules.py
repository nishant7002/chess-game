"""
tests/test_chess_rules.py
Unit tests for server-authoritative chess rules, move validation, and game state management.
"""

import pytest
import chess
from backend.game_state import GameState

def test_initial_board_setup():
    gs = GameState(human_color="white", algorithm="alpha_beta", depth=3)
    state = gs.to_dict()
    assert state["fen"] == chess.STARTING_FEN
    assert state["turn"] == "white"
    assert state["human_color"] == "white"
    assert state["ai_color"] == "black"
    assert state["is_human_turn"] is True
    assert state["is_game_over"] is False
    assert state["in_check"] is False
    assert len(state["move_history"]) == 0
    assert state["material"]["white"] == 39
    assert state["material"]["black"] == 39
    assert state["material"]["diff"] == 0

def test_legal_moves_and_turn_alternation():
    gs = GameState(human_color="white")
    # 1. e4
    rec1 = gs.make_move("e2e4")
    assert rec1["san"] == "e4"
    assert rec1["from"] == "e2"
    assert rec1["to"] == "e4"
    assert gs.current_turn == "black"
    assert gs.is_human_turn is False

    # 1... e5 (SAN test)
    rec2 = gs.make_move("e5")
    assert rec2["san"] == "e5"
    assert gs.current_turn == "white"
    assert gs.is_human_turn is True
    assert len(gs.move_history) == 2

def test_illegal_move_rejection():
    gs = GameState(human_color="white")
    with pytest.raises(ValueError):
        gs.make_move("e2e5")  # Pawn can't jump 3 squares
    # Verify board state remained unchanged
    assert gs.board.fen() == chess.STARTING_FEN
    assert gs.current_turn == "white"

def test_castling_kingside_and_queenside():
    # Setup position where White can castle kingside and Black can castle queenside
    fen = "r3k2r/pppq1ppp/2np1n2/2b1p1B1/2B1P1b1/2NP1N2/PPPQ1PPP/R3K2R w KQkq - 6 8"
    gs = GameState()
    gs.board.set_fen(fen)

    # White castles kingside (O-O)
    rec_w = gs.make_move("e1g1")
    assert rec_w["san"] == "O-O"
    assert gs.board.piece_at(chess.G1).symbol() == "K"
    assert gs.board.piece_at(chess.F1).symbol() == "R"

    # Black castles queenside (O-O-O)
    rec_b = gs.make_move("e8c8")
    assert rec_b["san"] == "O-O-O"
    assert gs.board.piece_at(chess.C8).symbol() == "k"
    assert gs.board.piece_at(chess.D8).symbol() == "r"

def test_en_passant():
    # Setup standard en passant position
    # White pawn on e5, Black plays d7-d5
    fen = "rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3"
    gs = GameState()
    gs.board.set_fen(fen)

    # White captures en passant exd6
    rec = gs.make_move("e5d6")
    assert "d6" in rec["san"]
    assert gs.board.piece_at(chess.D5) is None  # Black pawn removed
    assert gs.board.piece_at(chess.D6).symbol() == "P"  # White pawn on d6
    assert "p" in gs.captured_pieces["white"]

def test_pawn_promotion():
    # White pawn on e7, can promote on e8
    fen = "8/4P3/8/8/8/8/k7/4K3 w - - 0 1"
    gs = GameState()
    gs.board.set_fen(fen)

    # Promote to Queen
    rec_q = gs.make_move("e7e8q")
    assert rec_q["san"] == "e8=Q"
    assert gs.board.piece_at(chess.E8).symbol() == "Q"

    # Reset with promotion to Knight
    gs.board.set_fen(fen)
    rec_n = gs.make_move("e7e8n")
    assert rec_n["san"] == "e8=N"
    assert gs.board.piece_at(chess.E8).symbol() == "N"

def test_checkmate_scholars_mate():
    gs = GameState()
    moves = ["e4", "e5", "Bc4", "Nc6", "Qh5", "Nf6", "Qxf7#"]
    for m in moves:
        gs.make_move(m)
    status = gs.get_game_status()
    assert status["is_game_over"] is True
    assert status["winner"] == "white"
    assert "Checkmate" in status["result"]

def test_stalemate():
    # Classic stalemate: Black King on a8, White King on c7, White Queen on b6
    # Wait, with White queen on b6 and King on c7, Black king on a8 has no moves
    fen = "k7/2K5/1Q6/8/8/8/8/8 b - - 0 1"
    gs = GameState()
    gs.board.set_fen(fen)
    status = gs.get_game_status()
    assert status["is_game_over"] is True
    assert status["winner"] == "draw"
    assert "Stalemate" in status["result"]

def test_insufficient_material():
    # King vs King
    fen = "8/8/4k3/8/8/4K3/8/8 w - - 0 1"
    gs = GameState()
    gs.board.set_fen(fen)
    status = gs.get_game_status()
    assert status["is_game_over"] is True
    assert status["winner"] == "draw"
    assert "Insufficient Material" in status["result"]
