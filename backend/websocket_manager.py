"""
backend/websocket_manager.py
Manages real-time WebSocket sessions, game state updates, and asynchronous AI moves.
Ensures server-authoritative validation and non-blocking search execution.
"""

import json
import asyncio
from typing import Dict, Any, Optional
from fastapi import WebSocket
import chess
from backend.game_state import GameState
from backend.ai.engine import compute_ai_move

class SessionManager:
    def __init__(self):
        # Maps connection_id to (WebSocket, GameState)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    async def register(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_sessions[session_id] = {
            "ws": websocket,
            "game": GameState(),
            "ai_task": None
        }

    def unregister(self, session_id: str):
        if session_id in self.active_sessions:
            task = self.active_sessions[session_id].get("ai_task")
            if task and not task.done():
                task.cancel()
            del self.active_sessions[session_id]

    def get_game(self, session_id: str) -> Optional[GameState]:
        session = self.active_sessions.get(session_id)
        return session["game"] if session else None

    async def send_json(self, session_id: str, message: Dict[str, Any]):
        session = self.active_sessions.get(session_id)
        if session:
            try:
                await session["ws"].send_text(json.dumps(message))
            except Exception:
                pass

    async def handle_start_game(
        self, session_id: str, human_color: str = "white", algorithm: str = "alpha_beta", depth: int = 3
    ):
        session = self.active_sessions.get(session_id)
        if not session:
            return

        game: GameState = session["game"]
        game.reset(human_color=human_color, algorithm=algorithm, depth=depth)

        # Notify client of game reset
        await self.send_json(session_id, {
            "type": "game_state",
            "state": game.to_dict()
        })

        # If human chose Black, AI (White) makes the opening move!
        if game.human_color == "black" and not game.board.is_game_over():
            await self.trigger_ai_move(session_id)

    async def handle_make_move(self, session_id: str, move_str: str):
        session = self.active_sessions.get(session_id)
        if not session:
            return

        game: GameState = session["game"]

        # Validate turn
        if not game.is_human_turn:
            await self.send_json(session_id, {
                "type": "error",
                "message": "It is not your turn. Please wait for the AI to move."
            })
            return

        # Attempt to execute the human move
        try:
            move_record = game.make_move(move_str)
        except ValueError as e:
            await self.send_json(session_id, {
                "type": "error",
                "message": str(e)
            })
            return

        # Broadcast state after human move
        status = game.get_game_status()
        await self.send_json(session_id, {
            "type": "game_state",
            "state": game.to_dict()
        })

        if status["is_game_over"]:
            await self.send_json(session_id, {
                "type": "game_over",
                "winner": status["winner"],
                "result": status["result"]
            })
            return

        # Trigger AI move
        await self.trigger_ai_move(session_id)

    async def trigger_ai_move(self, session_id: str):
        session = self.active_sessions.get(session_id)
        if not session:
            return

        game: GameState = session["game"]
        if game.board.is_game_over():
            return

        # Send AI thinking indicator
        await self.send_json(session_id, {
            "type": "ai_thinking",
            "thinking": True
        })

        # Execute AI search in background worker thread to prevent blocking event loop
        # Pass a copy of the board to prevent race conditions
        board_copy = game.board.copy()
        algo = game.algorithm
        depth = game.depth

        try:
            ai_result = await asyncio.to_thread(compute_ai_move, board_copy, algo, depth)
        except Exception as e:
            await self.send_json(session_id, {
                "type": "error",
                "message": f"AI search error: {str(e)}"
            })
            await self.send_json(session_id, {"type": "ai_thinking", "thinking": False})
            return

        await self.send_json(session_id, {
            "type": "ai_thinking",
            "thinking": False
        })

        ai_move = ai_result.get("move")
        if ai_move:
            try:
                game.make_move(ai_move)
            except ValueError as e:
                await self.send_json(session_id, {
                    "type": "error",
                    "message": f"Internal AI move execution error: {str(e)}"
                })
                return

        # Send AI move details & search metrics
        await self.send_json(session_id, {
            "type": "ai_move",
            "move": ai_result.get("move"),
            "san": ai_result.get("san"),
            "eval": ai_result.get("eval"),
            "metrics": ai_result.get("metrics")
        })

        # Send updated game state
        status = game.get_game_status()
        await self.send_json(session_id, {
            "type": "game_state",
            "state": game.to_dict()
        })

        if status["is_game_over"]:
            await self.send_json(session_id, {
                "type": "game_over",
                "winner": status["winner"],
                "result": status["result"]
            })

    async def handle_get_legal_moves(self, session_id: str, square_name: str):
        game = self.get_game(session_id)
        if not game:
            return

        destinations = game.get_legal_moves_for_square(square_name)
        await self.send_json(session_id, {
            "type": "legal_moves",
            "square": square_name,
            "destinations": destinations
        })
