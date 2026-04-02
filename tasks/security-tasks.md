# Security Engineer Tasks — Iron Arena

## Agent: engineering-security-engineer
## Priority: Phase 4 (after all development phases complete)
## Read: all src/backend/ code before writing report

---

## Deliverables Required

### 1. reports/security-audit.md
Complete security audit with:
- PASS/FAIL for each check
- Code snippets showing issues found
- Fixes applied (or recommended if not applied)

---

## Security Checks Required

### 1. Telegram initData Authentication
- Verify HMAC-SHA256 signature check is implemented
- Verify bot token is used as secret key (never exposed to client)
- Verify auth_date is checked (reject if older than 24 hours)
- Verify telegram_id from initData is used, never from request body

Code to look for in src/backend/api/auth.py:
```python
# Must exist:
import hmac, hashlib
# Must verify: hmac.compare_digest(computed_hash, received_hash)
```

### 2. PvP Battle Anti-Cheat
- Verify all move validation happens in server code only
- Verify HP/stamina values come from server Redis state, NOT from client
- Verify damage calculation uses server-side player stats, NOT client data
- Verify battle timer enforced server-side (random move if timeout)
- Check for: can player send moves for opponent? (must be impossible)

### 3. Auction Double-Spend Prevention
- Verify gold is blocked atomically when bid placed
- Verify outbid player gets gold returned before new bid accepted
- Check for race condition: two players bidding at exact same millisecond
- Verify seller cannot bid on own auction
- Verify auction fee (5%) is calculated server-side

### 4. SQL Injection
- Verify all DB queries use SQLAlchemy ORM or parameterized queries
- Check for any raw SQL string concatenation with user input
- Verify item IDs validated before DB queries

### 5. Authorization Checks
- Verify player can only access their own inventory (not others')
- Verify player can only equip items they own
- Verify player can only remove their own auction lots
- Verify battle ID validated before WebSocket allows connection

### 6. Rate Limiting
- Check for rate limiting on: bid submission, battle join, shop purchase
- Recommend if not implemented

---

## Fix Requirements
If issues found: apply fixes directly to the source files AND document what was changed.
If fixes cannot be applied: clearly document as CRITICAL/HIGH/MEDIUM severity.
