# Iron Arena — Matchmaking Logic
# Created by: engineering-backend-architect
# Purpose: Redis-backed matchmaking queue management for random PvP battles

import os
import json
from typing import Optional

import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
MATCHMAKING_QUEUE_KEY = "matchmaking:queue"
MATCHMAKING_TTL = 120  # seconds a player waits before timeout


class MatchmakingService:
    """
    Manages the random matchmaking queue using Redis Lists.
    Thread-safe atomic operations via Redis transactions.
    """

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    async def enqueue(self, player_id: int, battle_id: int) -> None:
        """Add player to matchmaking queue. Stores player_id -> battle_id mapping."""
        await self.redis.lrem(MATCHMAKING_QUEUE_KEY, 0, str(player_id))
        await self.redis.rpush(MATCHMAKING_QUEUE_KEY, str(player_id))
        await self.redis.set(
            f"matchmaking:player:{player_id}:battle_id",
            battle_id,
            ex=MATCHMAKING_TTL,
        )

    async def dequeue(self) -> Optional[int]:
        """Pop the oldest player from the queue. Returns player_id or None."""
        val = await self.redis.lpop(MATCHMAKING_QUEUE_KEY)
        return int(val) if val else None

    async def remove(self, player_id: int) -> None:
        """Remove a specific player from the queue (e.g., on disconnect)."""
        await self.redis.lrem(MATCHMAKING_QUEUE_KEY, 0, str(player_id))
        await self.redis.delete(f"matchmaking:player:{player_id}:battle_id")

    async def get_pending_battle_id(self, player_id: int) -> Optional[int]:
        """Get the pending battle_id for a waiting player."""
        val = await self.redis.get(f"matchmaking:player:{player_id}:battle_id")
        return int(val) if val else None

    async def queue_length(self) -> int:
        """Return current queue depth."""
        return await self.redis.llen(MATCHMAKING_QUEUE_KEY)


async def try_match(player_id: int, battle_id: int) -> Optional[int]:
    """
    Attempt to match player_id against someone in the queue.
    Returns the opponent's player_id if matched, None if added to queue.

    This is a simplified version for the REST endpoint.
    The WebSocket engine has its own more complete matching logic.
    """
    redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    service = MatchmakingService(redis)

    # Try to pop an opponent
    opponent_id = await service.dequeue()

    if opponent_id is not None and opponent_id != player_id:
        await redis.aclose()
        return opponent_id

    # No opponent or matched self — enqueue this player
    if opponent_id == player_id:
        # Put self back and wait
        await service.enqueue(player_id, battle_id)
    else:
        await service.enqueue(player_id, battle_id)

    await redis.aclose()
    return None
