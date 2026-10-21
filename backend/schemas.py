"""
backend/schemas.py
Pydantic schemas and message structures for WebSocket and REST communication.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class GameConfig(BaseModel):
    human_color: str = Field(default="white", description="'white' or 'black'")
    algorithm: str = Field(default="alpha_beta", description="random, greedy, minimax, alpha_beta, alpha_beta_ordered")
    depth: int = Field(default=3, ge=1, le=5, description="Search depth limit")

class MoveRequest(BaseModel):
    move: str = Field(..., description="UCI (e.g. 'e2e4', 'e7e8q') or SAN (e.g. 'Nf3')")

class SquareQuery(BaseModel):
    square: str = Field(..., description="Square notation, e.g. 'e2'")

class WebSocketMessage(BaseModel):
    type: str
    data: Optional[Dict[str, Any]] = None
    move: Optional[str] = None
    square: Optional[str] = None
    human_color: Optional[str] = "white"
    algorithm: Optional[str] = "alpha_beta"
    depth: Optional[int] = 3
