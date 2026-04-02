# Iron Arena — Character API
# Created by: engineering-backend-architect
# Purpose: GET /character (profile), POST /character/create (name + stat distribution)

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.models.database import get_session
from src.backend.models.player import Player
from src.backend.api.deps import get_current_player

router = APIRouter()


def _character_response(player: Player) -> dict:
    """Build full character profile response matching api-contract.md."""
    return {
        "id": player.id,
        "telegram_id": player.telegram_id,
        "name": player.name,
        "level": player.level,
        "xp": player.xp,
        "xp_to_next_level": player.xp_to_next_level,   # level * 100
        "gold": player.gold,
        "max_hp": player.max_hp,                         # health_points * 10
        "current_hp": player.current_hp,
        "max_stamina": player.max_stamina,               # stamina * 10
        "current_stamina": player.current_stamina,
        "health_points": player.health_points,
        "stamina": player.stamina,
        "strength": player.strength,
        "agility": player.agility,
        "dodge_chance": player.dodge_chance,             # agility * 1.5, max 40.0
        "wins": player.wins,
        "losses": player.losses,
        "last_fight_at": player.last_fight_at.isoformat() if player.last_fight_at else None,
        "hp_recovery_at": None,      # TODO: calculate from last_fight_at + regen time
        "stamina_recovery_at": None,
    }


@router.get("")
async def get_character(
    player: Player = Depends(get_current_player),
):
    """Return current player's full profile."""
    return _character_response(player)


class StatPoints(BaseModel):
    health_points: int = 0
    strength: int = 0
    agility: int = 0


class CreateCharacterRequest(BaseModel):
    name: str
    stat_points: StatPoints

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2 or len(v) > 20:
            raise ValueError("Name must be 2-20 characters")
        return v


@router.post("/create")
async def create_character(
    body: CreateCharacterRequest,
    player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session),
):
    """
    Set character name and distribute 3 starting stat points.
    Allowed stats: health_points, strength, agility.
    Players start with base 5 in each stat; these 3 points are bonuses.
    """
    # Guard: character already named (name was set from Telegram on first auth;
    # consider "created" if name was explicitly set via this endpoint before)
    # We track this by checking if the player already has a non-default name set via creation
    # Simple approach: allow re-creation only if level == 1 and wins == 0
    # In production this would need a separate 'character_created' flag
    if player.wins > 0 or player.losses > 0:
        raise HTTPException(status_code=400, detail={"error": "character_already_exists"})

    sp = body.stat_points
    total = sp.health_points + sp.strength + sp.agility
    if total != 3:
        raise HTTPException(status_code=400, detail={"error": "invalid_stat_distribution"})

    if sp.health_points < 0 or sp.strength < 0 or sp.agility < 0:
        raise HTTPException(status_code=400, detail={"error": "invalid_stat_distribution"})

    # Apply stat distribution on top of base 5
    player.name = body.name
    player.health_points = 5 + sp.health_points
    player.strength = 5 + sp.strength
    player.agility = 5 + sp.agility
    # Reset current HP/stamina to new max
    player.current_hp = player.max_hp
    player.current_stamina = player.max_stamina

    await session.flush()

    return {
        "success": True,
        "character": _character_response(player),
    }
