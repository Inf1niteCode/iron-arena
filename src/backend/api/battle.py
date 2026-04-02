# Iron Arena — Battle REST API
# Created by: engineering-backend-architect
# Purpose: POST /battle/find (matchmaking), POST /battle/challenge (duel), GET /battle/{id}

import json
import os

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.models.database import get_session
from src.backend.models.player import Player
from src.backend.models.battle import Battle
from src.backend.api.deps import get_current_player

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
HOST = os.getenv("HOST", "localhost")
WS_SCHEME = os.getenv("WS_SCHEME", "ws")  # "wss" in production


def get_redis():
    return aioredis.from_url(REDIS_URL, decode_responses=True)


@router.post("/find")
async def find_battle(
    player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session),
):
    """
    Join random matchmaking queue.
    If another player is waiting, create battle immediately (matched).
    Otherwise, player waits in queue (waiting).
    """
    redis = get_redis()

    # Remove player from queue if already there (prevent duplicates)
    await redis.lrem("matchmaking:queue", 0, str(player.id))

    # Check if anyone is waiting
    opponent_id_str = await redis.lpop("matchmaking:queue")

    if opponent_id_str:
        opponent_id = int(opponent_id_str)
        if opponent_id == player.id:
            # Edge case: player was matched against themselves
            await redis.rpush("matchmaking:queue", str(player.id))
            await redis.aclose()
            return {
                "battle_id": None,
                "status": "waiting",
                "ws_url": f"{WS_SCHEME}://{HOST}/ws/battle/pending",
            }

        # Create battle record
        battle = Battle(
            player1_id=opponent_id,
            player2_id=player.id,
            mode="random",
        )
        session.add(battle)
        await session.flush()

        # Initialize battle state in Redis
        battle_state = {
            "player1_id": opponent_id,
            "player2_id": player.id,
            "status": "matched",
            "round": 0,
            "player1_move": "",
            "player2_move": "",
        }

        # Load player HP/stamina for battle
        opponent_result = await session.execute(
            select(Player).where(Player.id == opponent_id)
        )
        opponent = opponent_result.scalar_one_or_none()
        if opponent:
            battle_state["player1_hp"] = str(opponent.current_hp)
            battle_state["player1_stamina"] = str(opponent.current_stamina)
        battle_state["player2_hp"] = str(player.current_hp)
        battle_state["player2_stamina"] = str(player.current_stamina)

        await redis.hset(f"battle:{battle.id}:state", mapping=battle_state)
        await redis.expire(f"battle:{battle.id}:state", 3600)
        await redis.aclose()

        return {
            "battle_id": battle.id,
            "status": "matched",
            "ws_url": f"{WS_SCHEME}://{HOST}/ws/battle/{battle.id}",
        }
    else:
        # No opponent found — add to queue, player waits via WebSocket
        # We create a pending battle record with only player1 set
        # The opponent will be filled when matched
        battle = Battle(
            player1_id=player.id,
            player2_id=player.id,  # Temporary self-reference, updated when matched
            mode="random",
        )
        session.add(battle)
        await session.flush()

        await redis.rpush("matchmaking:queue", str(player.id))
        # Store pending battle_id for this player
        await redis.set(f"matchmaking:player:{player.id}:battle_id", battle.id, ex=120)
        await redis.aclose()

        return {
            "battle_id": battle.id,
            "status": "waiting",
            "ws_url": f"{WS_SCHEME}://{HOST}/ws/battle/{battle.id}",
        }


class ChallengeRequest(BaseModel):
    target_player_id: int


@router.post("/challenge")
async def challenge_player(
    body: ChallengeRequest,
    player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session),
):
    """Send a direct duel challenge to another player."""
    if body.target_player_id == player.id:
        raise HTTPException(status_code=400, detail={"error": "cannot_challenge_self"})

    target_result = await session.execute(
        select(Player).where(Player.id == body.target_player_id)
    )
    target = target_result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail={"error": "player_not_found"})

    battle = Battle(
        player1_id=player.id,
        player2_id=target.id,
        mode="duel",
    )
    session.add(battle)
    await session.flush()

    redis = get_redis()
    invite = json.dumps({
        "battle_id": battle.id,
        "challenger_id": player.id,
        "challenger_name": player.name,
    })
    await redis.set(f"duel:invite:{target.id}", invite, ex=60)
    await redis.aclose()

    return {
        "battle_id": battle.id,
        "status": "pending",
        "ws_url": f"{WS_SCHEME}://{HOST}/ws/battle/{battle.id}",
    }


@router.get("/{battle_id}")
async def get_battle(
    battle_id: int,
    player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session),
):
    """Get result of a completed battle."""
    result = await session.execute(
        select(Battle).where(Battle.id == battle_id)
    )
    battle = result.scalar_one_or_none()

    if battle is None:
        raise HTTPException(status_code=404, detail={"error": "battle_not_found"})

    p1_result = await session.execute(select(Player).where(Player.id == battle.player1_id))
    p1 = p1_result.scalar_one_or_none()
    p2_result = await session.execute(select(Player).where(Player.id == battle.player2_id))
    p2 = p2_result.scalar_one_or_none()

    return {
        "id": battle.id,
        "player1_id": battle.player1_id,
        "player1_name": p1.name if p1 else "Unknown",
        "player2_id": battle.player2_id,
        "player2_name": p2.name if p2 else "Unknown",
        "winner_id": battle.winner_id,
        "mode": battle.mode,
        "xp_gained": battle.xp_gained,
        "gold_gained": battle.gold_gained,
        "rounds": battle.rounds,
        "created_at": battle.created_at.isoformat(),
    }
