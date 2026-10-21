"""
tests/test_api_websocket.py
Integration tests for FastAPI endpoints and WebSocket real-time communication.
"""

import pytest
import json
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "alpha_beta" in data["algorithms"]

def test_websocket_connection_and_initial_state(client):
    with client.websocket_connect("/ws/test-session-1") as ws:
        # First message sent upon connection is initial game state
        msg = json.loads(ws.receive_text())
        assert msg["type"] == "game_state"
        assert msg["state"]["turn"] == "white"
        assert msg["state"]["human_color"] == "white"
        assert msg["state"]["is_human_turn"] is True

def test_websocket_start_game_and_legal_moves(client):
    with client.websocket_connect("/ws/test-session-2") as ws:
        # Receive initial state
        _ = ws.receive_text()

        # Query legal moves for e2
        ws.send_text(json.dumps({
            "type": "get_legal_moves",
            "square": "e2"
        }))
        res = json.loads(ws.receive_text())
        assert res["type"] == "legal_moves"
        assert res["square"] == "e2"
        assert "e3" in res["destinations"]
        assert "e4" in res["destinations"]

def test_websocket_human_move_and_ai_response(client):
    with client.websocket_connect("/ws/test-session-3") as ws:
        _ = ws.receive_text()

        # Configure fast search (depth 1, alpha-beta)
        ws.send_text(json.dumps({
            "type": "start_game",
            "human_color": "white",
            "algorithm": "alpha_beta",
            "depth": 1
        }))
        start_state = json.loads(ws.receive_text())
        assert start_state["type"] == "game_state"

        # Make human move: 1. e4
        ws.send_text(json.dumps({
            "type": "make_move",
            "move": "e2e4"
        }))

        # 1. State after human move
        human_state_msg = json.loads(ws.receive_text())
        assert human_state_msg["type"] == "game_state"
        assert human_state_msg["state"]["turn"] == "black"
        assert human_state_msg["state"]["last_move"]["uci"] == "e2e4"

        # 2. AI thinking True
        ai_think_on = json.loads(ws.receive_text())
        assert ai_think_on["type"] == "ai_thinking"
        assert ai_think_on["thinking"] is True

        # 3. AI thinking False
        ai_think_off = json.loads(ws.receive_text())
        assert ai_think_off["type"] == "ai_thinking"
        assert ai_think_off["thinking"] is False

        # 4. AI move payload with metrics
        ai_move_msg = json.loads(ws.receive_text())
        assert ai_move_msg["type"] == "ai_move"
        assert ai_move_msg["move"] is not None
        assert "metrics" in ai_move_msg

        # 5. State after AI move
        final_state_msg = json.loads(ws.receive_text())
        assert final_state_msg["type"] == "game_state"
        assert final_state_msg["state"]["turn"] == "white"
        assert len(final_state_msg["state"]["move_history"]) == 2

def test_websocket_illegal_move_handling(client):
    with client.websocket_connect("/ws/test-session-4") as ws:
        _ = ws.receive_text()

        # Send illegal move: e2e5 (pawn jump 3 squares)
        ws.send_text(json.dumps({
            "type": "make_move",
            "move": "e2e5"
        }))
        err_msg = json.loads(ws.receive_text())
        assert err_msg["type"] == "error"
        assert "Illegal" in err_msg["message"]

def test_websocket_play_as_black_ai_starts(client):
    with client.websocket_connect("/ws/test-session-5") as ws:
        _ = ws.receive_text()

        # Human plays Black -> AI (White) moves immediately
        ws.send_text(json.dumps({
            "type": "start_game",
            "human_color": "black",
            "algorithm": "greedy",
            "depth": 1
        }))

        # 1. Start game state confirmation
        init_msg = json.loads(ws.receive_text())
        assert init_msg["type"] == "game_state"
        assert init_msg["state"]["human_color"] == "black"

        # 2. AI thinking indicator True
        ai_think_on = json.loads(ws.receive_text())
        assert ai_think_on["type"] == "ai_thinking"
        assert ai_think_on["thinking"] is True

        # 3. AI thinking indicator False
        ai_think_off = json.loads(ws.receive_text())
        assert ai_think_off["type"] == "ai_thinking"
        assert ai_think_off["thinking"] is False

        # 4. AI move payload
        ai_move_msg = json.loads(ws.receive_text())
        assert ai_move_msg["type"] == "ai_move"

        # 5. State after AI's opening move (now it's black/human's turn)
        post_move = json.loads(ws.receive_text())
        assert post_move["type"] == "game_state"
        assert post_move["state"]["turn"] == "black"
        assert post_move["state"]["is_human_turn"] is True
