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
    description="Self-Learning Chess AI Engine - Depth-Limited Minimax and Alpha-Beta Pruning",
    version="1.0.0"
)

# Enable CORS securely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Inject standard security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

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
    # Validate or generate session ID
    if session_id:
        clean_id = session_id.strip()
        if not clean_id.replace("-", "").replace("_", "").isalnum() or len(clean_id) > 64:
            await websocket.close(code=1008, reason="Invalid session ID format")
            return
        if clean_id in session_manager.active_sessions:
            await websocket.close(code=1008, reason="Session ID already in use")
            return
        session_id = clean_id
    else:
        session_id = str(uuid.uuid4())

    registered = await session_manager.register(session_id, websocket)
    if not registered:
        return

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

            # Prevent oversized memory allocation DoS
            if len(raw_text) > 32768:
                await session_manager.send_json(session_id, {
                    "type": "error",
                    "message": "Payload exceeds maximum allowed size"
                })
                continue

            try:
                msg = json.loads(raw_text)
            except json.JSONDecodeError:
                await session_manager.send_json(session_id, {
                    "type": "error",
                    "message": "Malformed JSON payload"
                })
                continue

            # Ensure payload is a dictionary
            if not isinstance(msg, dict):
                await session_manager.send_json(session_id, {
                    "type": "error",
                    "message": "Message payload must be a JSON object"
                })
                continue

            msg_type = str(msg.get("type", "")).lower()

            if msg_type == "start_game":
                human_color = msg.get("human_color", "white")
                algorithm = msg.get("algorithm", "alpha_beta_ordered")
                depth = int(msg.get("depth", 3))
                await session_manager.handle_start_game(
                    session_id, human_color=human_color, algorithm=algorithm, depth=depth
                )

            elif msg_type == "update_settings" or msg_type == "update_config":
                algo = msg.get("algorithm")
                depth_val = msg.get("depth")
                depth_int = int(depth_val) if depth_val is not None else None
                await session_manager.handle_update_settings(
                    session_id, algorithm=algo, depth=depth_int
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

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=False)
