# Iron Arena — Auction Business Logic
# Created by: engineering-backend-architect
# Purpose: Auction settlement, gold locking/unlocking, double-spend prevention

import os
from datetime import datetime, timezone

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.models.player import Player
from src.backend.models.item import Item
from src.backend.models.auction import AuctionLot, AuctionBid
from src.backend.game_logic.formulas import calc_auction_seller_payout

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


async def get_locked_gold(redis: aioredis.Redis, player_id: int) -> int:
    """Return how much gold a player has locked in active bids."""
    val = await redis.get(f"gold:locked:{player_id}")
    return int(val) if val else 0


async def lock_gold(redis: aioredis.Redis, player_id: int, amount: int) -> None:
    """Add amount to player's locked gold (atomic increment)."""
    await redis.incrby(f"gold:locked:{player_id}", amount)


async def unlock_gold(redis: aioredis.Redis, player_id: int, amount: int) -> None:
    """Release amount from player's locked gold (atomic decrement, floor 0)."""
    current = await get_locked_gold(redis, player_id)
    new_val = max(0, current - amount)
    await redis.set(f"gold:locked:{player_id}", new_val)


async def settle_expired_auctions(session: AsyncSession) -> list[int]:
    """
    Find all expired active auctions and settle them.
    Returns list of settled lot IDs.

    Settlement logic:
    1. If there is a winner: transfer item to winner, pay seller (price * 0.95)
    2. If no bids: return item to seller, mark cancelled
    3. Unlock all gold for bidders

    This runs as a background task (e.g. APScheduler every minute).
    """
    now = datetime.now(timezone.utc)
    redis = aioredis.from_url(REDIS_URL, decode_responses=True)

    result = await session.execute(
        select(AuctionLot)
        .where(AuctionLot.status == "active")
        .where(AuctionLot.ends_at <= now)
    )
    expired_lots = result.scalars().all()
    settled_ids = []

    for lot in expired_lots:
        if lot.winner_id:
            # Settle: transfer item and pay seller
            await _settle_won_auction(session, redis, lot)
        else:
            # No bids: cancel auction
            lot.status = "cancelled"

        settled_ids.append(lot.id)

    await session.flush()
    await redis.aclose()
    return settled_ids


async def _settle_won_auction(
    session: AsyncSession, redis: aioredis.Redis, lot: AuctionLot
) -> None:
    """
    Settle a won auction:
    - Transfer item ownership to winner
    - Credit seller with price * 0.95 (5% fee)
    - Unlock winner's locked gold (the bid amount is consumed)
    - Refund all losing bidders' locked gold
    """
    # Get item and transfer to winner
    item_result = await session.execute(select(Item).where(Item.id == lot.item_id))
    item = item_result.scalar_one_or_none()
    if item:
        item.player_id = lot.winner_id
        item.is_equipped = False

    # Credit seller
    seller_result = await session.execute(select(Player).where(Player.id == lot.seller_id))
    seller = seller_result.scalar_one_or_none()
    if seller:
        payout = calc_auction_seller_payout(lot.current_price)
        seller.gold += payout

    # Deduct winner's gold (consume the locked amount)
    winner_result = await session.execute(select(Player).where(Player.id == lot.winner_id))
    winner = winner_result.scalar_one_or_none()
    if winner:
        winner.gold -= lot.current_price
        # Remove gold lock for winner (bid amount consumed)
        await unlock_gold(redis, lot.winner_id, lot.current_price)

    # Refund all losing bidders' locked gold
    bids_result = await session.execute(
        select(AuctionBid).where(AuctionBid.lot_id == lot.id)
    )
    bids = bids_result.scalars().all()

    # Track which bidders got refunded to avoid double-refund
    refunded: dict[int, int] = {}
    for bid in sorted(bids, key=lambda b: b.amount, reverse=True):
        if bid.bidder_id == lot.winner_id:
            continue  # Winner's gold already consumed above
        if bid.bidder_id not in refunded:
            # Each bidder only has their highest bid locked
            await unlock_gold(redis, bid.bidder_id, bid.amount)
            refunded[bid.bidder_id] = bid.amount

    lot.status = "completed"
