# Iron Arena — Auction API
# Created by: engineering-backend-architect
# Purpose: GET /auction/lots, POST /auction/create, POST /auction/bid, GET /auction/history
# Critical: gold locking uses Redis atomic ops to prevent double-spend

import json
import os
from datetime import datetime, timezone, timedelta

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.models.database import get_session
from src.backend.models.player import Player
from src.backend.models.item import Item
from src.backend.models.auction import AuctionLot, AuctionBid
from src.backend.api.deps import get_current_player

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
VALID_DURATIONS = {1, 6, 12, 24}


def get_redis():
    return aioredis.from_url(REDIS_URL, decode_responses=True)


def _item_to_dict(item: Item) -> dict:
    return {
        "id": item.id,
        "player_id": item.player_id,
        "type": item.type,
        "slot": item.slot,
        "color": item.color,
        "bonus_stat": item.bonus_stat,
        "bonus_value": item.bonus_value,
        "armor_value": item.armor_value,
        "is_equipped": item.is_equipped,
        "is_broken": item.is_broken,
        "enchant_level": item.enchant_level,
        "name": item.name,
    }


def _lot_to_dict(lot: AuctionLot, bid_count: int = 0) -> dict:
    return {
        "id": lot.id,
        "seller_id": lot.seller_id,
        "seller_name": lot.seller.name if lot.seller else "Unknown",
        "item": _item_to_dict(lot.item) if lot.item else None,
        "start_price": lot.start_price,
        "current_price": lot.current_price,
        "winner_id": lot.winner_id,
        "winner_name": lot.winner.name if lot.winner else None,
        "ends_at": lot.ends_at.isoformat(),
        "status": lot.status,
        "bid_count": bid_count,
    }


@router.get("/lots")
async def get_auction_lots(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
    status: str = Query(default="active"),
    player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session),
):
    """Return auction lots with pagination."""
    query = (
        select(AuctionLot)
        .join(AuctionLot.seller)
        .join(AuctionLot.item)
    )

    if status != "all":
        query = query.where(AuctionLot.status == status)

    # Count total
    count_result = await session.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    # Paginated results
    query = query.offset((page - 1) * limit).limit(limit).order_by(AuctionLot.ends_at)
    result = await session.execute(query)
    lots = result.scalars().all()

    # Count bids per lot
    lot_ids = [lot.id for lot in lots]
    bid_counts: dict[int, int] = {}
    if lot_ids:
        bc_result = await session.execute(
            select(AuctionBid.lot_id, func.count(AuctionBid.id))
            .where(AuctionBid.lot_id.in_(lot_ids))
            .group_by(AuctionBid.lot_id)
        )
        bid_counts = dict(bc_result.all())

    return {
        "lots": [_lot_to_dict(lot, bid_counts.get(lot.id, 0)) for lot in lots],
        "total": total,
        "page": page,
    }


class CreateLotRequest(BaseModel):
    item_id: int
    start_price: int
    duration_hours: int


@router.post("/create")
async def create_auction_lot(
    body: CreateLotRequest,
    player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session),
):
    """List an item on auction. Item must be unequipped and not already listed."""
    if body.start_price < 1:
        raise HTTPException(status_code=400, detail={"error": "invalid_price"})
    if body.duration_hours not in VALID_DURATIONS:
        raise HTTPException(status_code=400, detail={"error": "invalid_duration"})

    result = await session.execute(select(Item).where(Item.id == body.item_id))
    item = result.scalar_one_or_none()

    if item is None:
        raise HTTPException(status_code=404, detail={"error": "item_not_found"})
    if item.player_id != player.id:
        raise HTTPException(status_code=400, detail={"error": "item_not_owned"})
    if item.is_equipped:
        raise HTTPException(status_code=400, detail={"error": "item_equipped"})

    # Check not already listed
    existing = await session.execute(
        select(AuctionLot).where(
            AuctionLot.item_id == body.item_id,
            AuctionLot.status == "active",
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail={"error": "item_already_listed"})

    ends_at = datetime.now(timezone.utc) + timedelta(hours=body.duration_hours)
    lot = AuctionLot(
        seller_id=player.id,
        item_id=item.id,
        start_price=body.start_price,
        current_price=body.start_price,
        ends_at=ends_at,
        status="active",
    )
    session.add(lot)
    await session.flush()

    # Reload with relationships
    lot_result = await session.execute(
        select(AuctionLot)
        .join(AuctionLot.seller)
        .join(AuctionLot.item)
        .where(AuctionLot.id == lot.id)
    )
    lot = lot_result.scalar_one()

    return {
        "success": True,
        "lot": _lot_to_dict(lot, 0),
    }


class BidRequest(BaseModel):
    lot_id: int
    amount: int


@router.post("/bid")
async def place_bid(
    body: BidRequest,
    player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session),
):
    """
    Place a bid on an auction lot.
    Gold locking: bid amount deducted from player.gold immediately.
    Previous highest bidder's gold is returned atomically via Redis lock.
    """
    redis = get_redis()

    # Load lot
    lot_result = await session.execute(
        select(AuctionLot)
        .join(AuctionLot.seller)
        .join(AuctionLot.item)
        .where(AuctionLot.id == body.lot_id)
    )
    lot = lot_result.scalar_one_or_none()

    if lot is None:
        raise HTTPException(status_code=404, detail={"error": "lot_not_found"})
    if lot.status != "active":
        raise HTTPException(status_code=400, detail={"error": "auction_ended"})
    if datetime.now(timezone.utc) >= lot.ends_at:
        lot.status = "completed"
        await session.flush()
        raise HTTPException(status_code=400, detail={"error": "auction_ended"})
    if lot.seller_id == player.id:
        raise HTTPException(status_code=400, detail={"error": "own_auction"})
    if body.amount <= lot.current_price:
        raise HTTPException(status_code=400, detail={"error": "bid_too_low"})

    # Check available gold (gold - locked gold)
    locked_key = f"gold:locked:{player.id}"
    locked_str = await redis.get(locked_key)
    locked_gold = int(locked_str) if locked_str else 0
    available_gold = player.gold - locked_gold

    if available_gold < body.amount:
        await redis.aclose()
        raise HTTPException(status_code=400, detail={"error": "insufficient_gold"})

    # Find previous highest bidder to refund their locked gold
    prev_bid_result = await session.execute(
        select(AuctionBid)
        .where(AuctionBid.lot_id == lot.id)
        .order_by(AuctionBid.amount.desc())
        .limit(1)
    )
    prev_bid = prev_bid_result.scalar_one_or_none()

    # Use Redis pipeline for atomic gold lock operations
    async with redis.pipeline(transaction=True) as pipe:
        # Lock new bidder's gold
        new_locked = locked_gold + body.amount
        pipe.set(f"gold:locked:{player.id}", new_locked)

        # Unlock previous highest bidder's gold
        if prev_bid and prev_bid.bidder_id != player.id:
            prev_locked_key = f"gold:locked:{prev_bid.bidder_id}"
            prev_locked_str = await redis.get(prev_locked_key)
            prev_locked = int(prev_locked_str) if prev_locked_str else 0
            refund = max(0, prev_locked - prev_bid.amount)
            pipe.set(prev_locked_key, refund)

        await pipe.execute()

    # Record bid
    new_bid = AuctionBid(
        lot_id=lot.id,
        bidder_id=player.id,
        amount=body.amount,
    )
    session.add(new_bid)

    # Update lot current price and winner
    lot.current_price = body.amount
    lot.winner_id = player.id
    await session.flush()

    await redis.aclose()

    return {
        "success": True,
        "new_price": lot.current_price,
        "gold_blocked": body.amount,
        "gold_remaining": player.gold - locked_gold - body.amount,
    }


@router.get("/history")
async def get_auction_history(
    lot_id: int = Query(...),
    player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session),
):
    """Return bid history for a specific lot."""
    result = await session.execute(
        select(AuctionBid)
        .join(AuctionBid.bidder)
        .where(AuctionBid.lot_id == lot_id)
        .order_by(AuctionBid.created_at.desc())
    )
    bids = result.scalars().all()

    return {
        "bids": [
            {
                "id": bid.id,
                "bidder_id": bid.bidder_id,
                "bidder_name": bid.bidder.name if bid.bidder else "Unknown",
                "amount": bid.amount,
                "created_at": bid.created_at.isoformat(),
            }
            for bid in bids
        ]
    }
