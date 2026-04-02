# Backend Architect Tasks — Iron Arena

## Agent: engineering-backend-architect
## Priority: Phase 2 (after PM plan, before Frontend)

---

## Deliverables Required

### 1. reports/api-contract.md
Complete REST API contract that Frontend Developer MUST read before writing any code.
Include for every endpoint: HTTP method, path, request body schema, response schema, error codes.

### 2. reports/db-schema.md
Full database schema with:
- SQL CREATE TABLE statements
- All indexes
- Foreign key relationships
- Explanation of each table's purpose

### 3. src/backend/main.py
FastAPI application entry point with:
- CORS configuration for Telegram Mini App
- Router registration
- Database initialization
- Redis connection setup

### 4. src/backend/models/
SQLAlchemy models for all tables from spec:

```
players: id, telegram_id, name, level, xp, gold,
         health_points, stamina, strength, agility,
         wins, losses, last_fight_at

items: id, player_id, type, slot, color, bonus_stat, bonus_value,
       is_equipped, is_broken, enchant_level

auction_lots: id, seller_id, item_id, start_price, current_price,
              winner_id, ends_at, status

auction_bids: id, lot_id, bidder_id, amount, created_at

battles: id, player1_id, player2_id, winner_id, mode,
         xp_gained, gold_gained, created_at
```

### 5. src/backend/api/
REST endpoint modules:
- `auth.py` — POST /auth/telegram (validate initData, create/get player)
- `character.py` — GET /character, POST /character/create, PUT /character/stats
- `inventory.py` — GET /inventory, POST /inventory/equip, POST /inventory/unequip
- `shop.py` — GET /shop/items, POST /shop/buy
- `auction.py` — GET /auction/lots, POST /auction/create, POST /auction/bid, GET /auction/history
- `battle.py` — POST /battle/find, GET /battle/{id}, POST /battle/challenge

### 6. src/backend/websocket/
- `battle_ws.py` — WebSocket handler for PvP battles
  Protocol: connect → waiting → matched → round_input → round_result → game_over

### 7. src/backend/game_logic/
- `formulas.py` — Exact formulas from spec:
  - max_hp(health_points) = health_points * 10
  - damage(strength, armor_zone) = strength * 2 - armor_zone
  - dodge_chance(agility) = min(agility * 1.5, 40.0)  # max 40%
  - xp_for_level(n) = n * 100
  - hp_recovery_per_minute(max_hp) = max_hp * 0.10
  - stamina_recovery_per_minute(max_stamina) = max_stamina * 0.20
- `matchmaking.py` — Random 1v1 + duel invite system
- `auction_logic.py` — Bid processing, gold blocking, 5% platform fee

### 8. requirements.txt
All Python dependencies: fastapi, uvicorn, sqlalchemy, asyncpg, redis, python-telegram-bot, alembic, pydantic, websockets

### 9. alembic.ini + alembic/
Database migration setup

---

## Key Rules
- ALL game logic validation happens server-side only
- Telegram initData must be cryptographically verified (HMAC-SHA256)
- Auction gold must be blocked at bid time, returned if outbid
- 5% platform fee on auction sales
- Battle timer: 10 seconds per round for player input
- Each file starts with comment: who created it and why
