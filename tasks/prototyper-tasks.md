# Rapid Prototyper Tasks — Iron Arena

## Agent: engineering-rapid-prototyper
## Priority: Phase 3 (PARALLEL with Frontend, Senior Dev, UI Designer)

---

## Deliverables Required

### 1. src/prototypes/battle_prototype.py
Standalone Python script that simulates a complete PvP battle.
Run with: python battle_prototype.py

Must demonstrate:
- Two player objects with stats (HP, strength, agility, armor per zone)
- Full battle loop: round selection -> damage calculation -> result display
- Exact formulas: Damage = strength * 2 - armor_zone, Dodge = agility * 1.5 (max 40%)
- Terminal output showing each round clearly
- Battle ends when one player reaches 0 HP
- XP and gold reward calculation at end

Example output format:
```
=== Iron Arena Battle Prototype ===
Player 1: HP=100, STR=15, AGI=10
Player 2: HP=80, STR=12, AGI=8

Round 1:
  P1 attacks HEAD, defends CHEST
  P2 attacks CHEST, defends HEAD
  P1 damage dealt: 30-5=25 (no dodge)
  P2 damage dealt: 24-8=16 (dodged!) 
  P1 HP: 84, P2 HP: 75
...
=== GAME OVER: Player 1 wins! ===
XP gained: 600, Gold: 400
```

### 2. src/prototypes/auction_prototype.py
Standalone Python script simulating auction mechanics.
Run with: python auction_prototype.py

Must demonstrate:
- Creating an auction lot with start price and timer
- Multiple players placing bids
- Gold blocking when bid placed
- Gold return when outbid
- 5% platform fee deducted from final sale
- Seller receives: final_price * 0.95
- Winner receives the item

Example output:
```
=== Iron Arena Auction Prototype ===
Lot: Iron Sword (start: 100 gold, 60 sec timer)

Player A bids 150 gold -> gold blocked: 150
Player B bids 200 gold -> gold blocked: 200, Player A refunded: 150
Player C bids 180 gold -> BID TOO LOW, rejected

Timer expires...
Winner: Player B (200 gold bid)
Platform fee: 10 gold (5%)
Seller receives: 190 gold
Player B receives: Iron Sword
```

---

## Rules
- No external dependencies (pure Python stdlib only)
- Code must run immediately without setup
- Focus on correctness of game mechanics, not code elegance
- Add comments explaining each mechanic
- These prototypes will be used by QA to verify game logic
