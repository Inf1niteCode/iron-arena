#!/usr/bin/env python3
# Iron Arena — Auction Simulator Prototype
# Created by: engineering-rapid-prototyper
# Purpose: Standalone auction simulator to validate gold locking, fee calculations,
#          double-spend prevention, and settlement logic. No DB/Redis dependencies.
# Run: python src/prototypes/auction_prototype.py

import time
import random
from dataclasses import dataclass, field
from typing import Optional

# ============================================================
# EXACT FORMULA FROM SPEC
# ============================================================

AUCTION_FEE_RATE = 0.05  # 5% platform fee

def seller_payout(final_price: int) -> int:
    """Seller receives final_price * 0.95. Rounds down."""
    return int(final_price * (1 - AUCTION_FEE_RATE))

# ============================================================
# DOMAIN MODELS (simplified, no DB)
# ============================================================

@dataclass
class Item:
    id: int
    name: str
    type: str
    color: str

@dataclass
class Player:
    id: int
    name: str
    gold: int
    locked_gold: int = 0  # gold blocked in active bids
    items: list = field(default_factory=list)

    @property
    def available_gold(self) -> int:
        return self.gold - self.locked_gold

    def lock_gold(self, amount: int) -> bool:
        if self.available_gold < amount:
            return False
        self.locked_gold += amount
        return True

    def unlock_gold(self, amount: int) -> None:
        self.locked_gold = max(0, self.locked_gold - amount)

    def deduct_gold(self, amount: int) -> None:
        """Permanently deduct gold (auction won)."""
        self.gold -= amount
        self.locked_gold = max(0, self.locked_gold - amount)

    def credit_gold(self, amount: int) -> None:
        self.gold += amount

@dataclass
class Bid:
    bidder: Player
    amount: int
    timestamp: float = field(default_factory=time.time)

@dataclass
class AuctionLot:
    id: int
    seller: Player
    item: Item
    start_price: int
    ends_at: float  # Unix timestamp
    bids: list[Bid] = field(default_factory=list)
    status: str = "active"  # active | completed | cancelled
    winner: Optional[Player] = None

    @property
    def current_price(self) -> int:
        if not self.bids:
            return self.start_price
        return max(b.amount for b in self.bids)

    @property
    def is_expired(self) -> bool:
        return time.time() >= self.ends_at

    @property
    def highest_bidder(self) -> Optional[Player]:
        if not self.bids:
            return None
        return max(self.bids, key=lambda b: b.amount).bidder

# ============================================================
# AUCTION ENGINE
# ============================================================

class AuctionHouse:
    def __init__(self):
        self.lots: dict[int, AuctionLot] = {}
        self._next_lot_id = 1

    def create_lot(self, seller: Player, item: Item, start_price: int, duration_secs: int) -> AuctionLot:
        """Create a new auction lot. Item moves to 'in auction' state."""
        if item not in seller.items:
            raise ValueError(f"Player {seller.name} does not own item {item.name}")

        lot = AuctionLot(
            id=self._next_lot_id,
            seller=seller,
            item=item,
            start_price=start_price,
            ends_at=time.time() + duration_secs,
        )
        self._next_lot_id += 1
        self.lots[lot.id] = lot

        # Remove from seller's inventory (in auction)
        seller.items.remove(item)
        print(f"[AUCTION] {seller.name} listed '{item.name}' starting at {start_price}g for {duration_secs}s")
        return lot

    def place_bid(self, bidder: Player, lot: AuctionLot, amount: int) -> dict:
        """
        Place a bid. Gold locking prevents double-spend.
        Previous highest bidder's gold is immediately unlocked.
        """
        if lot.status != "active":
            return {"success": False, "error": "auction_ended"}
        if lot.is_expired:
            return {"success": False, "error": "auction_ended"}
        if bidder == lot.seller:
            return {"success": False, "error": "own_auction"}
        if amount <= lot.current_price:
            return {"success": False, "error": "bid_too_low", "min": lot.current_price + 1}
        if bidder.available_gold < amount:
            return {"success": False, "error": "insufficient_gold",
                    "available": bidder.available_gold, "needed": amount}

        # Unlock previous highest bidder's gold
        prev_highest = lot.highest_bidder
        if prev_highest and prev_highest != bidder:
            # Find their highest bid amount to unlock
            prev_amount = max(b.amount for b in lot.bids if b.bidder == prev_highest)
            prev_highest.unlock_gold(prev_amount)
            print(f"[AUCTION] {prev_highest.name}'s {prev_amount}g unlocked (outbid)")

        # Lock new bidder's gold
        if not bidder.lock_gold(amount):
            return {"success": False, "error": "insufficient_gold"}

        bid = Bid(bidder=bidder, amount=amount)
        lot.bids.append(bid)
        lot.winner = bidder

        print(f"[AUCTION] {bidder.name} bid {amount}g on '{lot.item.name}' (available: {bidder.available_gold}g)")
        return {"success": True, "new_price": amount, "gold_blocked": amount}

    def settle_lot(self, lot: AuctionLot) -> dict:
        """
        Settle expired auction.
        - Winner: deduct gold, receive item, unlock remaining locked gold
        - Seller: receive price * 0.95
        - Losing bidders: unlock their gold
        """
        if lot.status != "active":
            return {"status": lot.status}

        lot.status = "completed"

        if not lot.bids or not lot.winner:
            # No bids: return item to seller, mark cancelled
            lot.status = "cancelled"
            lot.seller.items.append(lot.item)
            print(f"[SETTLEMENT] Lot {lot.id}: No bids, item returned to {lot.seller.name}")
            return {"status": "cancelled"}

        winner = lot.winner
        final_price = lot.current_price
        payout = seller_payout(final_price)
        fee = final_price - payout

        # Consume winner's locked gold (deduct from actual gold balance)
        winner.deduct_gold(final_price)
        winner.items.append(lot.item)

        # Credit seller
        lot.seller.credit_gold(payout)

        # Unlock all losing bidders' gold
        refunded: set[int] = {winner.id}
        for bid in sorted(lot.bids, key=lambda b: b.amount, reverse=True):
            if bid.bidder.id not in refunded:
                bid.bidder.unlock_gold(bid.amount)
                refunded.add(bid.bidder.id)

        print(f"[SETTLEMENT] Lot {lot.id}: '{lot.item.name}'")
        print(f"  Winner: {winner.name} paid {final_price}g, received item")
        print(f"  Seller: {lot.seller.name} received {payout}g (fee: {fee}g = {AUCTION_FEE_RATE*100:.0f}%)")

        return {
            "status": "completed",
            "winner": winner.name,
            "final_price": final_price,
            "seller_payout": payout,
            "fee": fee,
        }

# ============================================================
# FORMULA VERIFICATION
# ============================================================

def verify_auction_formulas():
    print("\n=== Auction Formula Verification ===")

    # 5% fee
    assert seller_payout(100) == 95, f"Expected 95, got {seller_payout(100)}"
    assert seller_payout(200) == 190
    assert seller_payout(1) == 0  # rounds down for 1g
    assert seller_payout(21) == 19  # int(21 * 0.95) = 19
    print("seller_payout (5% fee): PASS")

    # Verify fee rate
    price = 1000
    payout = seller_payout(price)
    fee = price - payout
    assert fee == 50, f"Expected 50g fee on 1000g, got {fee}"
    print("5% fee on 1000g = 50g: PASS")

    print("\nAll auction formula verifications PASSED\n")

# ============================================================
# ANTI-DOUBLE-SPEND VERIFICATION
# ============================================================

def verify_no_double_spend():
    """Test that gold locking prevents spending same gold twice."""
    print("=== Anti-Double-Spend Test ===")

    seller = Player(id=1, name="Seller", gold=0)
    buyer = Player(id=2, name="Buyer", gold=500)
    outbidder = Player(id=3, name="Outbidder", gold=500)

    sword = Item(id=1, name="Iron Sword", type="chest", color="red")
    seller.items.append(sword)
    house = AuctionHouse()

    lot = house.create_lot(seller, sword, start_price=100, duration_secs=5)

    # Buyer bids 200g
    r1 = house.place_bid(buyer, lot, 200)
    assert r1["success"], f"Bid 1 failed: {r1}"
    assert buyer.available_gold == 300, f"Expected 300 available, got {buyer.available_gold}"
    print(f"Buyer bids 200g: available={buyer.available_gold}g (locked={buyer.locked_gold}g)")

    # Buyer tries to bid again on another hypothetical lot (testing available gold)
    assert buyer.available_gold < 400, "Gold locking is working"
    print("Gold lock prevents double-spend: PASS")

    # Outbidder bids 300g
    r2 = house.place_bid(outbidder, lot, 300)
    assert r2["success"], f"Bid 2 failed: {r2}"
    # Buyer's gold should be unlocked
    assert buyer.locked_gold == 0, f"Expected buyer locked_gold=0 after outbid, got {buyer.locked_gold}"
    assert buyer.available_gold == 500, f"Expected buyer available=500 after unlock, got {buyer.available_gold}"
    print(f"After outbid: Buyer gold returned (available={buyer.available_gold}g): PASS")

    # Wait for expiry and settle
    time.sleep(5.1)
    result = house.settle_lot(lot)
    assert result["status"] == "completed"
    assert outbidder.gold == 200, f"Expected outbidder gold=200 (500-300), got {outbidder.gold}"
    assert outbidder.locked_gold == 0, f"Expected locked_gold=0 after settlement"
    assert len(outbidder.items) == 1, "Outbidder should have received item"
    expected_payout = seller_payout(300)  # 285g
    assert seller.gold == expected_payout, f"Expected seller {expected_payout}g, got {seller.gold}"
    print(f"Settlement correct: winner={outbidder.name} paid 300g, seller got {seller.gold}g: PASS")
    print("\nAnti-double-spend verification PASSED\n")


# ============================================================
# DEMO SCENARIO
# ============================================================

def run_demo():
    print("=== Auction Demo Scenario ===\n")

    # Create players
    alice = Player(id=1, name="Alice", gold=1000)
    bob = Player(id=2, name="Bob", gold=500)
    carol = Player(id=3, name="Carol", gold=800)

    # Alice has an item to sell
    crystal = Item(id=1, name="Ruby Crystal", type="crystal", color="red")
    alice.items.append(crystal)

    house = AuctionHouse()

    # Alice lists for 2 seconds (quick demo)
    lot = house.create_lot(alice, crystal, start_price=50, duration_secs=2)

    print(f"\nInitial state:")
    print(f"  Alice: {alice.gold}g available={alice.available_gold}g")
    print(f"  Bob:   {bob.gold}g available={bob.available_gold}g")
    print(f"  Carol: {carol.gold}g available={carol.available_gold}g\n")

    # Bob bids
    house.place_bid(bob, lot, 100)
    print(f"  Bob available after bid: {bob.available_gold}g")

    # Carol outbids
    house.place_bid(carol, lot, 200)
    print(f"  Bob available after outbid: {bob.available_gold}g (should be 500g)")
    print(f"  Carol locked: {carol.locked_gold}g")

    # Bob bids again
    house.place_bid(bob, lot, 300)
    print(f"  Carol available after outbid: {carol.available_gold}g (should be 800g)")

    # Settle
    time.sleep(2.1)
    print("\nAuction expired, settling...")
    result = house.settle_lot(lot)

    print(f"\nFinal state:")
    print(f"  Alice: {alice.gold}g (started 1000g, sold for {result['final_price']}g, got {result['seller_payout']}g)")
    print(f"  Bob: {bob.gold}g (won with {result['final_price']}g, item: {[i.name for i in bob.items]})")
    print(f"  Carol: {carol.gold}g (lost bid, gold returned)")
    print(f"  Platform fee collected: {result['fee']}g")


if __name__ == "__main__":
    verify_auction_formulas()
    print("Running demo (takes ~2 seconds for auction expiry)...")
    run_demo()
    print("\nRunning anti-double-spend verification (takes ~5 seconds)...")
    verify_no_double_spend()
