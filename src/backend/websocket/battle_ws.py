# Iron Arena — PvP Battle WebSocket Engine
# Created by: engineering-senior-developer
# Purpose: Real-time 1v1 battle engine via WebSocket.
# Architecture: Each battle room is managed in Redis. Two players connect to the same
# battle_id endpoint. Rounds have a 10-second timer. All moves validated server-side.
# Anti-cheat: clients only send attack_zone + defend_zone; all damage calc on server.

import asyncio
import json
import logging
import os
from typing import Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.models.database import async_session_maker
from src.backend.models.player import Player
from src.backend.models.item import Item, ARMOR_ZONE_MAP
from src.backend.models.battle import Battle
from src.backend.api.auth import decode_jwt
from src.backend.game_logic.formulas import (
    process_round,
    calc_battle_rewards,
    check_level_up,
    calc_hp_recovery_per_minute,
    calc_stamina_recovery_per_minute,
)

router = APIRouter()
logger = logging.getLogger("battle_ws")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
ROUND_TIMER_SECONDS = 10
VALID_ZONES = {"head", "chest", "waist", "legs"}

# In-memory connection registry: battle_id -> {player_id -> WebSocket}
# In production this would use a pub/sub layer for multi-server deployments.
_connections: dict[int, dict[int, WebSocket]] = {}


def get_redis() -> aioredis.Redis:
    return aioredis.from_url(REDIS_URL, decode_responses=True)


async def _send(ws: WebSocket, data: dict) -> None:
    """Send JSON message to a WebSocket, ignore if disconnected."""
    try:
        await ws.send_json(data)
    except Exception:
        pass


async def _broadcast(battle_id: int, data: dict) -> None:
    """Broadcast a message to both players in a battle."""
    room = _connections.get(battle_id, {})
    for ws in room.values():
        await _send(ws, data)


async def _get_player_armor_at_zone(session: AsyncSession, player_id: int, zone: str) -> int:
    """
    Get the armor value defending a specific zone for a player.
    Zone-to-item-type: head->helmet, chest->chest, waist->bracers, legs->boots.
    Only equipped, non-broken items count.
    """
    zone_to_type = {v: k for k, v in ARMOR_ZONE_MAP.items()}
    item_type = zone_to_type.get(zone)
    if not item_type:
        return 0

    result = await session.execute(
        select(Item).where(
            Item.player_id == player_id,
            Item.type == item_type,
            Item.is_equipped == True,
            Item.is_broken == False,
        )
    )
    item = result.scalar_one_or_none()
    return item.armor_value if item else 0


async def _load_battle_state(redis: aioredis.Redis, battle_id: int) -> dict:
    """Load battle state hash from Redis."""
    return await redis.hgetall(f"battle:{battle_id}:state")


async def _save_battle_state(redis: aioredis.Redis, battle_id: int, state: dict) -> None:
    """Persist battle state to Redis with 1-hour TTL."""
    await redis.hset(f"battle:{battle_id}:state", mapping=state)
    await redis.expire(f"battle:{battle_id}:state", 3600)


async def _finalize_battle(
    session: AsyncSession,
    redis: aioredis.Redis,
    battle_id: int,
    winner_id: int,
    loser_id: int,
    total_rounds: int,
) -> dict:
    """
    Apply battle rewards and update player records.
    Returns reward data for game_over message.
    Anti-cheat: All reward calculations happen here, server-side only.
    """
    winner_result = await session.execute(select(Player).where(Player.id == winner_id))
    loser_result = await session.execute(select(Player).where(Player.id == loser_id))
    winner = winner_result.scalar_one_or_none()
    loser = loser_result.scalar_one_or_none()

    if not winner or not loser:
        return {"winner_xp": 0, "loser_xp": 0, "winner_gold": 0}

    rewards = calc_battle_rewards(winner.level, loser.level)

    # Apply rewards to winner
    winner.xp += rewards.winner_xp
    winner.gold += rewards.winner_gold
    winner.wins += 1
    new_level, remaining_xp = check_level_up(winner.level, winner.xp)
    winner.level = new_level
    winner.xp = remaining_xp

    # Apply rewards to loser
    loser.xp += rewards.loser_xp
    loser.losses += 1
    new_level, remaining_xp = check_level_up(loser.level, loser.xp)
    loser.level = new_level
    loser.xp = remaining_xp

    # Update battle record
    battle_result = await session.execute(select(Battle).where(Battle.id == battle_id))
    battle = battle_result.scalar_one_or_none()
    if battle:
        battle.winner_id = winner_id
        battle.xp_gained = rewards.winner_xp
        battle.gold_gained = rewards.winner_gold
        battle.rounds = total_rounds

    await session.commit()

    # Cleanup Redis state
    await redis.delete(f"battle:{battle_id}:state")

    return {
        "winner_xp": rewards.winner_xp,
        "loser_xp": rewards.loser_xp,
        "winner_gold": rewards.winner_gold,
    }


async def _run_round_timer(
    battle_id: int,
    round_num: int,
    redis: aioredis.Redis,
    session: AsyncSession,
) -> None:
    """
    Wait ROUND_TIMER_SECONDS for both moves. If a player doesn't move,
    auto-assign a random valid move for them (anti-AFK).
    Then process the round.
    """
    await asyncio.sleep(ROUND_TIMER_SECONDS)

    state = await _load_battle_state(redis, battle_id)
    if not state or state.get("status") == "complete":
        return

    p1_id = int(state["player1_id"])
    p2_id = int(state["player2_id"])

    # Auto-move for missing players (server decides for AFK players)
    import random as _random
    zones = list(VALID_ZONES)

    p1_move_raw = state.get("player1_move", "")
    p2_move_raw = state.get("player2_move", "")

    if not p1_move_raw:
        auto_move = {"attack_zone": _random.choice(zones), "defend_zone": _random.choice(zones)}
        state["player1_move"] = json.dumps(auto_move)
        logger.info(f"Battle {battle_id}: Auto-move for player {p1_id} round {round_num}")

    if not p2_move_raw:
        auto_move = {"attack_zone": _random.choice(zones), "defend_zone": _random.choice(zones)}
        state["player2_move"] = json.dumps(auto_move)
        logger.info(f"Battle {battle_id}: Auto-move for player {p2_id} round {round_num}")

    # Trigger round resolution (both moves now present)
    await _resolve_round(battle_id, state, redis, session)


async def _resolve_round(
    battle_id: int,
    state: dict,
    redis: aioredis.Redis,
    session: AsyncSession,
) -> None:
    """
    Resolve a round once both moves are submitted.
    Calculates damage, checks for battle end, broadcasts results.
    """
    p1_id = int(state["player1_id"])
    p2_id = int(state["player2_id"])
    p1_hp = int(state["player1_hp"])
    p2_hp = int(state["player2_hp"])
    round_num = int(state.get("round", 1))

    p1_move = json.loads(state["player1_move"])
    p2_move = json.loads(state["player2_move"])

    # Server-side validation of move zones (anti-cheat)
    for move, player_id in [(p1_move, p1_id), (p2_move, p2_id)]:
        if move.get("attack_zone") not in VALID_ZONES:
            logger.warning(f"Invalid attack_zone from player {player_id}, using 'chest'")
            move["attack_zone"] = "chest"
        if move.get("defend_zone") not in VALID_ZONES:
            logger.warning(f"Invalid defend_zone from player {player_id}, using 'chest'")
            move["defend_zone"] = "chest"

    # Get armor values from database (server authoritative)
    p1_armor = await _get_player_armor_at_zone(session, p1_id, p1_move["defend_zone"])
    p2_armor = await _get_player_armor_at_zone(session, p2_id, p2_move["defend_zone"])

    # Load player stats (server authoritative — client cannot send stats)
    p1_result = await session.execute(select(Player).where(Player.id == p1_id))
    p2_result = await session.execute(select(Player).where(Player.id == p2_id))
    p1_player = p1_result.scalar_one_or_none()
    p2_player = p2_result.scalar_one_or_none()

    if not p1_player or not p2_player:
        return

    # Process round using canonical formula from game_logic.formulas
    result = process_round(
        p1_strength=p1_player.strength,
        p1_agility=p1_player.agility,
        p1_hp=p1_hp,
        p1_attack_zone=p1_move["attack_zone"],
        p1_defend_zone=p1_move["defend_zone"],
        p1_armor_at_zone=p1_armor,
        p2_strength=p2_player.strength,
        p2_agility=p2_player.agility,
        p2_hp=p2_hp,
        p2_attack_zone=p2_move["attack_zone"],
        p2_defend_zone=p2_move["defend_zone"],
        p2_armor_at_zone=p2_armor,
    )

    # Update state
    state["player1_hp"] = str(result.p1_hp_after)
    state["player2_hp"] = str(result.p2_hp_after)
    state["player1_move"] = ""
    state["player2_move"] = ""
    state["round"] = str(round_num)

    await _save_battle_state(redis, battle_id, state)

    # Broadcast round_result to each player with their perspective
    room = _connections.get(battle_id, {})
    p1_ws = room.get(p1_id)
    p2_ws = room.get(p2_id)

    # P1 perspective
    if p1_ws:
        await _send(p1_ws, {
            "type": "round_result",
            "round": round_num,
            "your_attack": {
                "zone": p1_move["attack_zone"],
                "damage_dealt": result.p1_damage_dealt,
                "dodged": result.p1_dodged_by_p2,
            },
            "opponent_attack": {
                "zone": p2_move["attack_zone"],
                "damage_dealt": result.p2_damage_dealt,
                "dodged": result.p2_dodged_by_p1,
            },
            "your_hp": result.p1_hp_after,
            "opponent_hp": result.p2_hp_after,
            "your_stamina": int(state.get("player1_stamina", 50)),
            "opponent_stamina": int(state.get("player2_stamina", 50)),
        })

    # P2 perspective (swap your/opponent)
    if p2_ws:
        await _send(p2_ws, {
            "type": "round_result",
            "round": round_num,
            "your_attack": {
                "zone": p2_move["attack_zone"],
                "damage_dealt": result.p2_damage_dealt,
                "dodged": result.p2_dodged_by_p1,
            },
            "opponent_attack": {
                "zone": p1_move["attack_zone"],
                "damage_dealt": result.p1_damage_dealt,
                "dodged": result.p1_dodged_by_p2,
            },
            "your_hp": result.p2_hp_after,
            "opponent_hp": result.p1_hp_after,
            "your_stamina": int(state.get("player2_stamina", 50)),
            "opponent_stamina": int(state.get("player1_stamina", 50)),
        })

    # Check battle end conditions
    p1_dead = result.p1_hp_after <= 0
    p2_dead = result.p2_hp_after <= 0

    if p1_dead or p2_dead:
        # Determine winner (if both die simultaneously, p2 wins by default)
        if p1_dead and not p2_dead:
            winner_id, loser_id = p2_id, p1_id
        elif p2_dead and not p1_dead:
            winner_id, loser_id = p1_id, p2_id
        else:
            # Simultaneous death: higher HP before round wins (tie-breaker)
            winner_id = p1_id if p1_hp >= p2_hp else p2_id
            loser_id = p2_id if winner_id == p1_id else p1_id

        state["status"] = "complete"
        await _save_battle_state(redis, battle_id, state)

        reward_data = await _finalize_battle(
            session, redis, battle_id, winner_id, loser_id, round_num
        )

        # Send game_over to each player
        for pid, ws in [(p1_id, p1_ws), (p2_id, p2_ws)]:
            if ws:
                await _send(ws, {
                    "type": "game_over",
                    "winner_id": winner_id,
                    "you_won": pid == winner_id,
                    "xp_gained": reward_data["winner_xp"] if pid == winner_id else reward_data["loser_xp"],
                    "gold_gained": reward_data["winner_gold"] if pid == winner_id else 0,
                    "total_rounds": round_num,
                })

        # Clean up connection registry
        _connections.pop(battle_id, None)
    else:
        # Start next round
        next_round = round_num + 1
        state["round"] = str(next_round)
        state["status"] = "round"
        await _save_battle_state(redis, battle_id, state)

        await _broadcast(battle_id, {
            "type": "round_start",
            "round": next_round,
            "timer_seconds": ROUND_TIMER_SECONDS,
            "your_hp": result.p1_hp_after,  # Note: each player gets their own value below
            "opponent_hp": result.p2_hp_after,
            "your_stamina": int(state.get("player1_stamina", 50)),
            "opponent_stamina": int(state.get("player2_stamina", 50)),
        })

        # Per-player round_start with correct HP orientation
        if p1_ws:
            await _send(p1_ws, {
                "type": "round_start",
                "round": next_round,
                "timer_seconds": ROUND_TIMER_SECONDS,
                "your_hp": result.p1_hp_after,
                "opponent_hp": result.p2_hp_after,
                "your_stamina": int(state.get("player1_stamina", 50)),
                "opponent_stamina": int(state.get("player2_stamina", 50)),
            })
        if p2_ws:
            await _send(p2_ws, {
                "type": "round_start",
                "round": next_round,
                "timer_seconds": ROUND_TIMER_SECONDS,
                "your_hp": result.p2_hp_after,
                "opponent_hp": result.p1_hp_after,
                "your_stamina": int(state.get("player2_stamina", 50)),
                "opponent_stamina": int(state.get("player1_stamina", 50)),
            })

        # Start timer for next round
        asyncio.create_task(
            _run_round_timer(battle_id, next_round, redis, session)
        )


@router.websocket("/battle/{battle_id}")
async def battle_websocket(
    battle_id: int,
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket endpoint for PvP battle.
    URL: wss://{host}/ws/battle/{battle_id}?token={jwt_token}

    Connection flow:
    1. Validate JWT token
    2. Register player in battle room
    3. When both players connect, start Round 1
    4. Each round: send round_start, wait for moves, resolve, send round_result
    5. On HP <= 0: send game_over, distribute rewards
    """
    # Authenticate
    try:
        payload = decode_jwt(token)
        player_id = int(payload["sub"])
    except Exception:
        await websocket.close(code=4001, reason="unauthorized")
        return

    await websocket.accept()

    redis = get_redis()
    async with async_session_maker() as session:
        # Load battle
        battle_result = await session.execute(select(Battle).where(Battle.id == battle_id))
        battle = battle_result.scalar_one_or_none()

        if battle is None:
            await _send(websocket, {"type": "error", "code": "battle_not_found", "message": "Battle not found"})
            await websocket.close()
            await redis.aclose()
            return

        # Verify player is part of this battle
        if player_id not in (battle.player1_id, battle.player2_id):
            await _send(websocket, {"type": "error", "code": "not_in_battle", "message": "You are not in this battle"})
            await websocket.close()
            await redis.aclose()
            return

        # Register connection
        if battle_id not in _connections:
            _connections[battle_id] = {}
        _connections[battle_id][player_id] = websocket

        # Load state
        state = await _load_battle_state(redis, battle_id)

        if not state:
            # Initialize state if not already done (fallback)
            player_result = await session.execute(select(Player).where(Player.id == player_id))
            player = player_result.scalar_one_or_none()
            state = {
                "player1_id": str(battle.player1_id),
                "player2_id": str(battle.player2_id),
                "player1_hp": str(player.current_hp if player_id == battle.player1_id else 50),
                "player2_hp": str(player.current_hp if player_id == battle.player2_id else 50),
                "player1_stamina": "50",
                "player2_stamina": "50",
                "round": "0",
                "status": "waiting",
                "player1_move": "",
                "player2_move": "",
            }
            await _save_battle_state(redis, battle_id, state)

        room = _connections[battle_id]

        # Send waiting message until both players connected
        if len(room) < 2:
            await _send(websocket, {
                "type": "waiting",
                "message": "Searching for opponent...",
            })

        # When both players are connected, start the battle
        if len(room) == 2:
            p1_id = int(state["player1_id"])
            p2_id = int(state["player2_id"])
            p1_ws = room.get(p1_id)
            p2_ws = room.get(p2_id)

            # Load opponent info for each player
            p1_result = await session.execute(select(Player).where(Player.id == p1_id))
            p2_result = await session.execute(select(Player).where(Player.id == p2_id))
            p1_player = p1_result.scalar_one_or_none()
            p2_player = p2_result.scalar_one_or_none()

            if p1_player and p2_player:
                # Send 'matched' message to both with opponent info
                if p1_ws:
                    await _send(p1_ws, {
                        "type": "matched",
                        "opponent": {
                            "id": p2_player.id,
                            "name": p2_player.name,
                            "level": p2_player.level,
                            "max_hp": p2_player.max_hp,
                            "strength": p2_player.strength,
                            "agility": p2_player.agility,
                        },
                        "your_hp": int(state["player1_hp"]),
                        "your_stamina": int(state["player1_stamina"]),
                    })
                if p2_ws:
                    await _send(p2_ws, {
                        "type": "matched",
                        "opponent": {
                            "id": p1_player.id,
                            "name": p1_player.name,
                            "level": p1_player.level,
                            "max_hp": p1_player.max_hp,
                            "strength": p1_player.strength,
                            "agility": p1_player.agility,
                        },
                        "your_hp": int(state["player2_hp"]),
                        "your_stamina": int(state["player2_stamina"]),
                    })

                # Start Round 1
                state["round"] = "1"
                state["status"] = "round"
                await _save_battle_state(redis, battle_id, state)

                if p1_ws:
                    await _send(p1_ws, {
                        "type": "round_start",
                        "round": 1,
                        "timer_seconds": ROUND_TIMER_SECONDS,
                        "your_hp": int(state["player1_hp"]),
                        "opponent_hp": int(state["player2_hp"]),
                        "your_stamina": int(state["player1_stamina"]),
                        "opponent_stamina": int(state["player2_stamina"]),
                    })
                if p2_ws:
                    await _send(p2_ws, {
                        "type": "round_start",
                        "round": 1,
                        "timer_seconds": ROUND_TIMER_SECONDS,
                        "your_hp": int(state["player2_hp"]),
                        "opponent_hp": int(state["player1_hp"]),
                        "your_stamina": int(state["player2_stamina"]),
                        "opponent_stamina": int(state["player1_stamina"]),
                    })

                # Launch round timer
                asyncio.create_task(
                    _run_round_timer(battle_id, 1, redis, session)
                )

        # Main message receive loop
        try:
            while True:
                raw = await websocket.receive_text()
                msg = json.loads(raw)

                if msg.get("type") != "move":
                    await _send(websocket, {
                        "type": "error",
                        "code": "invalid_message",
                        "message": "Only 'move' messages accepted during battle",
                    })
                    continue

                # Server-side validation of move data (anti-cheat)
                attack_zone = msg.get("attack_zone")
                defend_zone = msg.get("defend_zone")

                if attack_zone not in VALID_ZONES or defend_zone not in VALID_ZONES:
                    await _send(websocket, {
                        "type": "error",
                        "code": "invalid_move",
                        "message": f"attack_zone and defend_zone must be one of {VALID_ZONES}",
                    })
                    continue

                # Reload state (may have changed since connection)
                current_state = await _load_battle_state(redis, battle_id)
                if not current_state or current_state.get("status") == "complete":
                    break

                p1_id = int(current_state["player1_id"])
                p2_id = int(current_state["player2_id"])

                # Store move for this player
                move_data = json.dumps({"attack_zone": attack_zone, "defend_zone": defend_zone})
                if player_id == p1_id:
                    if current_state.get("player1_move"):
                        # Already submitted a move this round — ignore duplicate
                        continue
                    current_state["player1_move"] = move_data
                elif player_id == p2_id:
                    if current_state.get("player2_move"):
                        continue
                    current_state["player2_move"] = move_data

                await _save_battle_state(redis, battle_id, current_state)

                # If both moves submitted, resolve immediately (don't wait for timer)
                if current_state.get("player1_move") and current_state.get("player2_move"):
                    await _resolve_round(battle_id, current_state, redis, session)

        except WebSocketDisconnect:
            logger.info(f"Player {player_id} disconnected from battle {battle_id}")
            room = _connections.get(battle_id, {})
            room.pop(player_id, None)
            if not room:
                _connections.pop(battle_id, None)
        except Exception as e:
            logger.error(f"Battle WebSocket error: {e}")
            await _send(websocket, {
                "type": "error",
                "code": "server_error",
                "message": "Internal server error",
            })
        finally:
            await redis.aclose()
