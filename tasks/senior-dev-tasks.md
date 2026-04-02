# Senior Developer Tasks — Iron Arena PvP Engine

## Agent: engineering-senior-developer
## Priority: Phase 3 (PARALLEL with Frontend, Prototyper, UI Designer)
## Read: reports/api-contract.md and reports/db-schema.md before coding

---

## Deliverables Required

### 1. src/backend/websocket/battle_ws.py (ENHANCE/REWRITE)
Complete WebSocket PvP battle engine:

```
Battle Flow:
1. Player connects: ws://backend/ws/battle/{player_id}
2. Server adds to matchmaking queue
3. When 2 players matched: send "matched" message with opponent info
4. Round loop:
   a. Server sends "round_start" with 10-second timer
   b. Both players send their moves: { attack_zone, defend_zone }
   c. Server waits for BOTH moves (or timer expires = random move)
   d. Server calculates damage for both players
   e. Server sends "round_result" to BOTH players
   f. Repeat until one player HP = 0
5. Server sends "game_over" with winner, XP gained, gold gained
6. Server saves battle to DB, updates player stats
```

### 2. src/backend/game_logic/formulas.py (EXACT FORMULAS — DO NOT MODIFY)
```python
def max_hp(health_points: int) -> int:
    return health_points * 10

def calculate_damage(strength: int, armor_zone: int) -> int:
    damage = strength * 2 - armor_zone
    return max(0, damage)  # damage cannot be negative

def dodge_chance(agility: int) -> float:
    return min(agility * 1.5, 40.0)  # max 40%

def xp_for_level(n: int) -> int:
    return n * 100

def hp_recovery_per_minute(max_hp: int) -> float:
    return max_hp * 0.10

def stamina_recovery_per_minute(max_stamina: int) -> float:
    return max_stamina * 0.20
```

### 3. src/backend/game_logic/matchmaking.py
- Random 1v1: Add player to waiting queue in Redis, match with first available
- Duel: Store duel invitation in Redis, notify target via WebSocket
- Handle disconnections: remove from queue, forfeit if in battle
- Rating-based matching optional but not required for MVP

### 4. src/backend/game_logic/battle_engine.py
Complete round calculation:
- Apply equipped armor values by zone (helmet=head, chest=chest, bracers=waist, boots=legs)
- Calculate dodge: if random() < dodge_chance(agility)/100: attack misses
- Apply damage to defender HP
- Both players attack simultaneously (both can take damage in same round)
- Stamina cost: 10 stamina per attack, 5 stamina per block
- If stamina = 0: player cannot block (defend_zone ignored)

### 5. Anti-Cheat Validation
- Server NEVER trusts client for damage values
- All moves validated: attack_zone and defend_zone must be valid values
- Timer enforcement: if player doesn't submit in 10s, random move assigned
- Player HP/stamina stored in Redis during battle, not client-side
- After battle ends, verify results match Redis state before saving to DB

---

## Stamina Mechanics
- Starting stamina: stamina stat × 10 (similar to HP formula)
- Attack costs 10 stamina
- Block costs 5 stamina
- 0 stamina = cannot block this round (attack still works)
- Stamina recovers 20% per minute OUTSIDE of battle

## Battle Rewards
- Winner XP = loser_level × 50
- Loser XP = winner_level × 10  
- Winner gold = loser_level × 20
- Loser gold = 0
