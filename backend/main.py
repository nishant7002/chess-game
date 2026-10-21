"""
backend/main.py
FastAPI Application Entry Point.
Provides WebSocket endpoints for real-time game flow and REST API for system status.
"""

import os
import json
import uuid
from typing import Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.websocket_manager import SessionManager
from backend.schemas import GameConfig, MoveRequest

app = FastAPI(
    title="Human vs AI Chess Engine API",
    description="Foundations of Artificial Intelligence (FAI) Course Project - Minimax and Alpha-Beta Pruning",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_manager = SessionManager()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Chess AI Backend",
        "algorithms": ["random", "greedy", "minimax", "alpha_beta", "alpha_beta_ordered"]
    }

@app.websocket("/ws")
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str = None):
    if not session_id:
        session_id = str(uuid.uuid4())

    await session_manager.register(session_id, websocket)

    # Send initial game state
    game = session_manager.get_game(session_id)
    if game:
        await session_manager.send_json(session_id, {
            "type": "game_state",
            "session_id": session_id,
            "state": game.to_dict()
        })

    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                msg = json.loads(raw_text)
            except json.JSONDecodeError:
                await session_manager.send_json(session_id, {
                    "type": "error",
                    "message": "Malformed JSON payload"
                })
                continue

            msg_type = msg.get("type", "").lower()

            if msg_type == "start_game":
                human_color = msg.get("human_color", "white")
                algorithm = msg.get("algorithm", "alpha_beta")
                depth = int(msg.get("depth", 3))
                await session_manager.handle_start_game(
                    session_id, human_color=human_color, algorithm=algorithm, depth=depth
                )

            elif msg_type == "make_move":
                move_str = msg.get("move", "")
                if not move_str:
                    await session_manager.send_json(session_id, {
                        "type": "error",
                        "message": "Missing 'move' field"
                    })
                    continue
                await session_manager.handle_make_move(session_id, move_str)

            elif msg_type == "get_legal_moves":
                square = msg.get("square", "")
                if square:
                    await session_manager.handle_get_legal_moves(session_id, square)

            elif msg_type == "restart_game":
                game = session_manager.get_game(session_id)
                if game:
                    await session_manager.handle_start_game(
                        session_id,
                        human_color=game.human_color,
                        algorithm=game.algorithm,
                        depth=game.depth
                    )

            else:
                await session_manager.send_json(session_id, {
                    "type": "error",
                    "message": f"Unknown message type: '{msg_type}'"
                })

    except WebSocketDisconnect:
        session_manager.unregister(session_id)
    except Exception as e:
        session_manager.unregister(session_id)

# Serve production frontend if built
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Frontend build not found")
