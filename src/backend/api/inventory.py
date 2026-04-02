# Iron Arena — Inventory API
# Created by: engineering-backend-architect
# Purpose: GET /inventory, POST /inventory/equip, POST /inventory/unequip

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.models.database import get_session
from src.backend.models.item import Item, ARMOR_ZONE_MAP
from src.backend.models.player import Player
from src.backend.api.deps import get_current_player

router = APIRouter()

# Map item type -> equipment slot key in the "equipped" response object
ITEM_TYPE_TO_SLOT_KEY = {
    "helmet": "head",
    "chest": "chest",
    "bracers": "waist",
    "boots": "legs",
}


def _item_to_dict(item: Item) -> dict:
    return {
        "id": item.id,
        "player_id": item.player_id,
        "type": item.type,
        "slot": item.slot,
        "color": item.color,
        "bonus_stat": item.bonus_stat,
        "bonus_value": item.bonus_value,
        "is_equipped": item.is_equipped,
        "is_broken": item.is_broken,
        "enchant_level": item.enchant_level,
        "armor_value": item.armor_value,
        "name": item.name,
    }


def _build_equipped_map(items: list[Item]) -> dict:
    """Build the 'equipped' slot map from the player's item list."""
    equipped: dict = {
        "head": None, "chest": None, "waist": None, "legs": None,
        **{f"crystal_{i}": None for i in range(1, 9)},
    }
    crystal_idx = 1
    for item in items:
        if not item.is_equipped:
            continue
        if item.type == "crystal":
            if crystal_idx <= 8:
                equipped[f"crystal_{crystal_idx}"] = item.id
                crystal_idx += 1
        else:
            slot_key = ITEM_TYPE_TO_SLOT_KEY.get(item.type)
            if slot_key:
                equipped[slot_key] = item.id
    return equipped


@router.get("")
async def get_inventory(
    player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session),
):
    """Return player's full inventory."""
    result = await session.execute(select(Item).where(Item.player_id == player.id))
    items = result.scalars().all()
    return {
        "items": [_item_to_dict(i) for i in items],
        "equipped": _build_equipped_map(list(items)),
    }


class EquipRequest(BaseModel):
    item_id: int


class UnequipRequest(BaseModel):
    item_id: int


@router.post("/equip")
async def equip_item(
    body: EquipRequest,
    player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session),
):
    """Equip an item. Unequips whatever was previously in that slot."""
    result = await session.execute(select(Item).where(Item.id == body.item_id))
    item = result.scalar_one_or_none()

    if item is None:
        raise HTTPException(status_code=404, detail={"error": "item_not_found"})
    if item.player_id != player.id:
        raise HTTPException(status_code=400, detail={"error": "item_not_owned"})
    if item.is_broken:
        raise HTTPException(status_code=400, detail={"error": "item_broken"})

    unequipped_item_id = None

    if item.type == "crystal":
        # Crystals fill open crystal slots; up to 8 crystals
        crystal_result = await session.execute(
            select(Item).where(
                Item.player_id == player.id,
                Item.type == "crystal",
                Item.is_equipped == True,
            )
        )
        equipped_crystals = crystal_result.scalars().all()
        if len(equipped_crystals) >= 8 and not item.is_equipped:
            # Unequip the oldest crystal to make room
            oldest = min(equipped_crystals, key=lambda c: c.id)
            oldest.is_equipped = False
            unequipped_item_id = oldest.id
    else:
        # Armor slots: unequip existing item in the same slot
        slot_result = await session.execute(
            select(Item).where(
                Item.player_id == player.id,
                Item.type == item.type,
                Item.is_equipped == True,
            )
        )
        currently_equipped = slot_result.scalar_one_or_none()
        if currently_equipped and currently_equipped.id != item.id:
            currently_equipped.is_equipped = False
            unequipped_item_id = currently_equipped.id

    item.is_equipped = True
    await session.flush()

    return {
        "success": True,
        "unequipped_item_id": unequipped_item_id,
        "character": {
            "id": player.id,
            "strength": player.strength,
            "agility": player.agility,
            "health_points": player.health_points,
            "max_hp": player.max_hp,
            "current_hp": player.current_hp,
        },
    }


@router.post("/unequip")
async def unequip_item(
    body: UnequipRequest,
    player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session),
):
    """Unequip an item from its slot."""
    result = await session.execute(select(Item).where(Item.id == body.item_id))
    item = result.scalar_one_or_none()

    if item is None:
        raise HTTPException(status_code=404, detail={"error": "item_not_found"})
    if item.player_id != player.id:
        raise HTTPException(status_code=400, detail={"error": "item_not_owned"})

    item.is_equipped = False
    await session.flush()

    return {
        "success": True,
        "character": {
            "id": player.id,
            "strength": player.strength,
            "agility": player.agility,
            "health_points": player.health_points,
            "max_hp": player.max_hp,
            "current_hp": player.current_hp,
        },
    }
