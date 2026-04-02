# Frontend Developer Tasks — Iron Arena

## Agent: engineering-frontend-developer
## Priority: Phase 3 (PARALLEL with Senior Dev, Prototyper, UI Designer)
## CRITICAL: Read reports/api-contract.md FIRST before writing any code

---

## Deliverables Required

### 1. package.json
Dependencies including:
- react, react-dom, typescript
- @telegram-apps/sdk (Telegram Mini App SDK)
- tailwindcss
- vite
- react-dnd or @dnd-kit/core (for drag & drop inventory)
- react-router-dom
- axios or fetch wrapper

### 2. tsconfig.json
Strict TypeScript configuration (strict: true)

### 3. vite.config.ts
Vite build configuration

### 4. src/frontend/pages/
- `ProfilePage.tsx` — Player level, XP bar, gold, HP, stamina with timers
- `InventoryPage.tsx` — 8 armor slots + 8 crystal slots, drag & drop
- `ArenaPage.tsx` — Matchmaking button, duel, battle UI with zone selection
- `ShopPage.tsx` — Item grid with buy buttons
- `AuctionPage.tsx` — Active lots, bid form, history

### 5. src/frontend/hooks/
- `useTelegram.ts` — Telegram WebApp SDK initialization and user data
- `useWebSocket.ts` — WebSocket connection for PvP battles
- `useInventory.ts` — Inventory state management with drag & drop
- `useCharacter.ts` — Character stats fetching and caching
- `useAuction.ts` — Auction lots and real-time bid updates

### 6. src/frontend/components/
(Will be supplemented by UI Designer — coordinate via ui-screens.md report)

### 7. WebSocket Client
- Connect to ws://backend/ws/battle/{battle_id}
- Handle messages: waiting, matched, round_input, round_result, game_over
- Send: { attack_zone: "head"|"chest"|"waist"|"legs", defend_zone: "..." }
- Display round countdown timer (10 seconds)

---

## API Integration Rules
- ALL endpoints from reports/api-contract.md must be called exactly as specified
- Handle authentication token from Telegram initData
- Show loading states during API calls
- Show error messages on API failures
- No game logic calculations on frontend — only display server results

## UI Requirements
- Mobile-first: min-width 360px (Telegram standard)
- Dark gaming theme
- Drag & drop inventory must work on mobile touch events
- Item color coding: red/blue/green items
- HP and stamina bars with real-time countdown recovery timers
