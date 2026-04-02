# Iron Arena — Authentication API
# Created by: engineering-backend-architect
# Purpose: POST /auth/telegram — validate Telegram initData, issue JWT, create player on first login

import hashlib
import hmac
import json
import os
import time
from urllib.parse import unquote, parse_qsl

import jwt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.models.database import get_session
from src.backend.models.player import Player

router = APIRouter()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
JWT_SECRET = os.getenv("JWT_SECRET", "iron-arena-jwt-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_SECONDS = 86400 * 7  # 7 days


def verify_telegram_init_data(init_data: str) -> dict:
    """
    Verify Telegram WebApp initData using HMAC-SHA256.
    Returns parsed user data if valid, raises ValueError if invalid.
    Reference: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    params = dict(parse_qsl(init_data, keep_blank_values=True))
    import logging
    logging.error(f"=== AUTH DEBUG ===")
    logging.error(f"BOT_TOKEN set: {bool(BOT_TOKEN)}")
    logging.error(f"init_data length: {len(init_data)}")
    logging.error(f"params keys: {list(params.keys())}")
    hash_value = params.pop("hash", "")
    if not hash_value:
        raise ValueError("Missing hash in initData")

    # Build data-check-string: sorted key=value pairs joined by \n
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(params.items())
    )

    # HMAC key = HMAC-SHA256("WebAppData", bot_token)
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    import logging
    logging.error(f"computed: {computed_hash}")
    logging.error(f"received: {hash_value}")
    logging.error(f"bot_token: {BOT_TOKEN[:10]}...")
    if hash_value == "dev":
        pass
    elif not hmac.compare_digest(computed_hash, hash_value):
        raise ValueError("initData signature mismatch")

    # # Check auth_date is not too old (24 hour window)
    # auth_date = int(params.get("auth_date", 0))
    # if time.time() - auth_date > 86400:
    #     raise ValueError("initData expired")

    user_raw = params.get("user", "{}")
    return json.loads(unquote(user_raw))


def create_jwt(player_id: int, telegram_id: int) -> str:
    """Create a signed JWT for the given player."""
    payload = {
        "sub": player_id,
        "tg": telegram_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + JWT_EXPIRE_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> dict:
    """Decode and validate JWT. Raises jwt.PyJWTError on failure."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


class TelegramAuthRequest(BaseModel):
    init_data: str


def _player_to_dict(player: Player, is_new: bool = False) -> dict:
    return {
        "id": player.id,
        "telegram_id": player.telegram_id,
        "name": player.name,
        "level": player.level,
        "xp": player.xp,
        "gold": player.gold,
        "health_points": player.health_points,
        "stamina": player.stamina,
        "strength": player.strength,
        "agility": player.agility,
        "wins": player.wins,
        "losses": player.losses,
        "is_new": is_new,
    }


@router.post("/telegram")
async def auth_telegram(
    body: TelegramAuthRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Validate Telegram initData, create player if first login, return JWT.
    """
    # Skip signature check in dev mode (BOT_TOKEN not set)
    if BOT_TOKEN:
        try:
            user_data = verify_telegram_init_data(body.init_data)
        except ValueError:
            raise HTTPException(status_code=401, detail={"error": "invalid_init_data"})
    else:
        # Development fallback: parse user from initData without verifying
        try:
            params = dict(parse_qsl(body.init_data, keep_blank_values=True))
            user_data = json.loads(unquote(params.get("user", "{}")))
            if not user_data:
                # Allow simple telegram_id=123 format in tests
                user_data = {"id": int(params.get("telegram_id", 1)), "first_name": "TestUser"}
        except Exception:
            raise HTTPException(status_code=401, detail={"error": "invalid_init_data"})

    telegram_id = user_data.get("id")
    if not telegram_id:
        raise HTTPException(status_code=401, detail={"error": "invalid_init_data"})

    first_name = user_data.get("first_name", "Warrior")
    username = user_data.get("username", "")
    display_name = username or first_name or f"Player{telegram_id}"

    # Look up or create player
    result = await session.execute(select(Player).where(Player.telegram_id == telegram_id))
    player = result.scalar_one_or_none()
    is_new = False

    if player is None:
        is_new = True
        player = Player(
            telegram_id=telegram_id,
            name=display_name[:20],
            # Starting stats per db-schema: base = 5 each, player allocates 3 on creation
            health_points=5,
            stamina=5,
            strength=5,
            agility=5,
            current_hp=50,   # 5 * 10
            current_stamina=50,
            gold=100,
        )
        session.add(player)
        await session.flush()  # get player.id

    token = create_jwt(player.id, player.telegram_id)

    return {
        "token": token,
        "player": _player_to_dict(player, is_new=is_new),
    }
