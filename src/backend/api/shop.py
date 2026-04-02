# Iron Arena — Shop API
# Created by: engineering-backend-architect
# Purpose: GET /shop/items (rotating catalog), POST /shop/buy (purchase with gold)

import random
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.models.database import get_session
from src.backend.models.player import Player
from src.backend.models.item import Item, VALID_TYPES, VALID_COLORS
from src.backend.models.shop import ShopItem
from src.backend.api.deps import get_current_player

router = APIRouter()

# Shop refresh interval: 6 hours
SHOP_REFRESH_HOURS = 6
# Shop catalog size per refresh
SHOP_CATALOG_SIZE = 12

# Item name templates for procedural generation
ITEM_NAMES = {
    ("helmet", "red"): "Crimson Helm",
    ("helmet", "blue"): "Azure Helm",
    ("helmet", "green"): "Verdant Helm",
    ("chest", "red"): "Scarlet Plate",
    ("chest", "blue"): "Sapphire Plate",
    ("chest", "green"): "Jade Plate",
    ("bracers", "red"): "Flame Bracers",
    ("bracers", "blue"): "Frost Bracers",
    ("bracers", "green"): "Iron Bracers",
    ("boots", "red"): "Ember Boots",
    ("boots", "blue"): "Tide Boots",
    ("boots", "green"): "Stone Boots",
    ("crystal", "red"): "Ruby Crystal",
    ("crystal", "blue"): "Sapphire Crystal",
    ("crystal", "green"): "Emerald Crystal",
}

COLOR_TO_STAT = {
    "red": "strength",
    "blue": "agility",
    "green": "health_points",
}

ITEM_TYPE_TO_SLOT = {
    "helmet": "head",
    "chest": "chest",
    "bracers": "waist",
    "boots": "legs",
    "crystal": "crystal",
}


def _shop_item_to_dict(shop_item: ShopItem) -> dict:
    return {
        "id": shop_item.id,
        "type": shop_item.type,
        "color": shop_item.color,
        "bonus_stat": shop_item.bonus_stat,
        "bonus_value": shop_item.bonus_value,
        "armor_value": shop_item.armor_value,
        "price": shop_item.price,
        "name": shop_item.name,
        "stock": shop_item.stock,
    }


async def _get_or_seed_shop(session: AsyncSession) -> tuple[list[ShopItem], datetime]:
    """Return current shop items, seeding a new rotation if expired."""
    now = datetime.now(timezone.utc)

    result = await session.execute(
        select(ShopItem).where(ShopItem.refreshes_at > now).where(ShopItem.stock > 0)
    )
    items = result.scalars().all()

    if items:
        refreshes_at = items[0].refreshes_at
        return list(items), refreshes_at

    # Seed new shop rotation
    refreshes_at = now + timedelta(hours=SHOP_REFRESH_HOURS)
    new_items = []

    types = list(VALID_TYPES)
    colors = list(VALID_COLORS)

    for _ in range(SHOP_CATALOG_SIZE):
        item_type = random.choice(types)
        color = random.choice(colors)
        bonus_stat = COLOR_TO_STAT[color]
        slot = ITEM_TYPE_TO_SLOT[item_type]
        bonus_value = random.randint(1, 3)
        armor_value = random.randint(1, 5) if item_type != "crystal" else 0
        price = (bonus_value + armor_value) * random.randint(15, 25)
        name = ITEM_NAMES.get((item_type, color), f"{color.capitalize()} {item_type.capitalize()}")

        shop_item = ShopItem(
            type=item_type,
            color=color,
            bonus_stat=bonus_stat,
            bonus_value=bonus_value,
            armor_value=armor_value,
            price=price,
            name=name,
            stock=10,
            refreshes_at=refreshes_at,
        )
        session.add(shop_item)
        new_items.append(shop_item)

    await session.flush()
    return new_items, refreshes_at


@router.get("/items")
async def get_shop_items(
    player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session),
):
    """Return current shop rotation."""
    items, refreshes_at = await _get_or_seed_shop(session)
    return {
        "items": [_shop_item_to_dict(i) for i in items],
        "refreshes_at": refreshes_at.isoformat(),
    }


class BuyItemRequest(BaseModel):
    shop_item_id: int


@router.post("/buy")
async def buy_item(
    body: BuyItemRequest,
    player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session),
):
    """Purchase an item from the shop. Deducts gold, adds item to inventory."""
    result = await session.execute(select(ShopItem).where(ShopItem.id == body.shop_item_id))
    shop_item = result.scalar_one_or_none()

    if shop_item is None:
        raise HTTPException(status_code=404, detail={"error": "item_not_found"})
    if shop_item.stock <= 0:
        raise HTTPException(status_code=400, detail={"error": "out_of_stock"})
    if player.gold < shop_item.price:
        raise HTTPException(status_code=400, detail={"error": "insufficient_gold"})

    # Deduct gold and stock atomically
    player.gold -= shop_item.price
    shop_item.stock -= 1

    # Create item in player inventory
    new_item = Item(
        player_id=player.id,
        type=shop_item.type,
        slot=ITEM_TYPE_TO_SLOT[shop_item.type],
        color=shop_item.color,
        bonus_stat=shop_item.bonus_stat,
        bonus_value=shop_item.bonus_value,
        armor_value=shop_item.armor_value,
        is_equipped=False,
        is_broken=False,
        enchant_level=0,
        name=shop_item.name,
    )
    session.add(new_item)
    await session.flush()

    return {
        "success": True,
        "item": {
            "id": new_item.id,
            "player_id": new_item.player_id,
            "type": new_item.type,
            "slot": new_item.slot,
            "color": new_item.color,
            "bonus_stat": new_item.bonus_stat,
            "bonus_value": new_item.bonus_value,
            "armor_value": new_item.armor_value,
            "is_equipped": new_item.is_equipped,
            "is_broken": new_item.is_broken,
            "enchant_level": new_item.enchant_level,
            "name": new_item.name,
        },
        "gold_remaining": player.gold,
    }
