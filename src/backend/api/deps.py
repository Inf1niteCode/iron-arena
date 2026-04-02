# Iron Arena — Shared API Dependencies
# Created by: engineering-backend-architect
# Purpose: FastAPI dependency for JWT auth — extracts current player from Bearer token

from fastapi import Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from src.backend.models.database import get_session
from src.backend.models.player import Player
from src.backend.api.auth import JWT_SECRET, JWT_ALGORITHM


async def get_current_player(
    authorization: str = Header(...),
    session: AsyncSession = Depends(get_session),
) -> Player:
    """
    FastAPI dependency: validate Bearer token and return the current Player.
    Raises HTTP 401 if token is missing, invalid, or expired.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})

    token = authorization.removeprefix("Bearer ").strip()

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})

    player_id = payload.get("sub")
    if not player_id:
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})

    result = await session.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()

    if player is None:
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})

    return player
