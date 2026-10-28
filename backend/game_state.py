"""
backend/game_state.py
Authoritative Chess Game State Manager using python-chess.
Ensures 100% server-side validation and consistent rule enforcement.
"""

from typing import Dict, Any, List, Optional
import chess

PIECE_SYMBOLS = {
    chess.PAWN: "p",
    chess.KNIGHT: "n",
    chess.BISHOP: "b",
    chess.ROOK: "r",
    chess.QUEEN: "q",
    chess.KING: "k"
}

PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0
}

class GameState:
    def __init__(self, human_color: str = "white", algorithm: str = "alpha_beta_ordered", depth: int = 3):
        self.board = chess.Board()
        self.human_color = human_color.lower()
        self.ai_color = "black" if self.human_color == "white" else "white"
        self.algorithm = algorithm
        self.depth = depth
        self.move_history: List[Dict[str, Any]] = []
        self.captured_pieces: Dict[str, List[str]] = {"white": [], "black": []}
        self.last_move: Optional[Dict[str, str]] = None
        self.game_version: int = 1

    def reset(self, human_color: Optional[str] = None, algorithm: Optional[str] = None, depth: Optional[int] = None):
        """Resets the board for a new game session."""
        self.game_version += 1
        self.board.reset()
        if human_color:
            self.human_color = human_color.lower()
            self.ai_color = "black" if self.human_color == "white" else "white"
        if algorithm:
            self.algorithm = algorithm
        if depth is not None:
            self.depth = max(1, min(depth, 5))
        self.move_history = []
        self.captured_pieces = {"white": [], "black": []}
        self.last_move = None

    @property
    def current_turn(self) -> str:
        return "white" if self.board.turn == chess.WHITE else "black"

    @property
    def is_human_turn(self) -> bool:
        return self.current_turn == self.human_color

    def get_legal_moves_for_square(self, square_name: str) -> List[str]:
        """Returns target squares (e.g. ['e3', 'e4']) for legal moves from a given square."""
        try:
            from_sq = chess.parse_square(square_name)
        except ValueError:
            return []
        
        destinations = []
        for move in self.board.legal_moves:
            if move.from_square == from_sq:
                destinations.append(chess.square_name(move.to_square))
        return destinations

    def make_move(self, move_str: str) -> Dict[str, Any]:
        """
        Validates and executes a move on the authoritative server board.
        Accepts UCI (e.g. 'e2e4', 'e7e8q') or SAN (e.g. 'Nf3', 'O-O').
        Raises ValueError if move is illegal or malformed.
        """
        move_str = move_str.strip()
        parsed_move: Optional[chess.Move] = None

        # Try parsing as UCI first
        try:
            candidate = chess.Move.from_uci(move_str)
            if candidate in self.board.legal_moves:
                parsed_move = candidate
            elif len(move_str) == 4:
                # Check if it was an unpromoted pawn promotion (default to queen)
                promo_candidate = chess.Move.from_uci(move_str + "q")
                if promo_candidate in self.board.legal_moves:
                    parsed_move = promo_candidate
        except ValueError:
            pass

        # If not UCI, try parsing as SAN
        if not parsed_move:
            try:
                candidate = self.board.parse_san(move_str)
                if candidate in self.board.legal_moves:
                    parsed_move = candidate
            except ValueError:
                pass

        if not parsed_move:
            raise ValueError(f"Illegal or unrecognized move: {move_str}")

        # Track captured piece before pushing
        captured_piece = self.board.piece_at(parsed_move.to_square)
        if self.board.is_en_passant(parsed_move):
            # En passant captures pawn on destination file, origin rank
            captured_piece_sym = "P" if self.board.turn == chess.BLACK else "p"
        elif captured_piece:
            captured_piece_sym = captured_piece.symbol()
        else:
            captured_piece_sym = None

        san_str = self.board.san(parsed_move)
        uci_str = parsed_move.uci()
        from_sq = chess.square_name(parsed_move.from_square)
        to_sq = chess.square_name(parsed_move.to_square)
        moving_color = "white" if self.board.turn == chess.WHITE else "black"

        # Push move to python-chess board
        self.board.push(parsed_move)

        # Update captured pieces lists
        # If moving_color was white, white captured black's piece
        if captured_piece_sym:
            if moving_color == "white":
                self.captured_pieces["white"].append(captured_piece_sym.lower())
            else:
                self.captured_pieces["black"].append(captured_piece_sym.upper())

        move_record = {
            "move_number": (len(self.move_history) // 2) + 1,
            "turn": moving_color,
            "san": san_str,
            "uci": uci_str,
            "from": from_sq,
            "to": to_sq,
            "captured": captured_piece_sym
        }
        self.move_history.append(move_record)
        self.last_move = {"from": from_sq, "to": to_sq, "san": san_str, "uci": uci_str}

        return move_record

    def get_game_status(self) -> Dict[str, Any]:
        """Calculates game terminal state and textual explanations."""
        is_over = self.board.is_game_over()
        in_check = self.board.is_check()
        result_desc = "Game in progress"
        winner: Optional[str] = None

        if self.board.is_checkmate():
            winner = "black" if self.board.turn == chess.WHITE else "white"
            result_desc = f"Checkmate! {winner.capitalize()} wins."
        elif self.board.is_stalemate():
            winner = "draw"
            result_desc = "Draw by Stalemate."
        elif self.board.is_insufficient_material():
            winner = "draw"
            result_desc = "Draw by Insufficient Material."
        elif self.board.is_fifty_moves():
            winner = "draw"
            result_desc = "Draw by 50-Move Rule."
        elif self.board.is_repetition(3):
            winner = "draw"
            result_desc = "Draw by Threefold Repetition."
        elif in_check:
            result_desc = f"Check! {self.current_turn.capitalize()} is in check."

        return {
            "is_game_over": is_over,
            "in_check": in_check,
            "result": result_desc,
            "winner": winner
        }

    def get_material_balance(self) -> Dict[str, Any]:
        """Calculates material counts and differential for White and Black."""
        white_val = 0
        black_val = 0
        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if piece:
                val = PIECE_VALUES.get(piece.piece_type, 0)
                if piece.color == chess.WHITE:
                    white_val += val
                else:
                    black_val += val
        diff = white_val - black_val
        return {
            "white": white_val,
            "black": black_val,
            "diff": diff  # positive favors White, negative favors Black
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serializes complete authoritative game state for client transmission."""
        status = self.get_game_status()
        material = self.get_material_balance()

        return {
            "fen": self.board.fen(),
            "turn": self.current_turn,
            "human_color": self.human_color,
            "ai_color": self.ai_color,
            "is_human_turn": self.is_human_turn,
            "algorithm": self.algorithm,
            "depth": self.depth,
            "is_game_over": status["is_game_over"],
            "in_check": status["in_check"],
            "result": status["result"],
            "winner": status["winner"],
            "last_move": self.last_move,
            "move_history": self.move_history,
            "captured_pieces": self.captured_pieces,
            "material": material,
            "fullmove_number": self.board.fullmove_number,
            "halfmove_clock": self.board.halfmove_clock
        }
