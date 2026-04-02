# UI Designer Tasks — Iron Arena

## Agent: design-ui-designer
## Priority: Phase 3 (PARALLEL with Frontend, Senior Dev, Prototyper)

---

## Deliverables Required

### 1. src/frontend/components/
Implement all UI components with Tailwind CSS, dark gaming theme:

#### Layout Components
- `BottomNav.tsx` — 5-tab navigation: Profile | Inventory | Arena | Shop | Auction
- `PageHeader.tsx` — Page title with player gold/HP display
- `LoadingSpinner.tsx` — Loading state component
- `ErrorBoundary.tsx` — Error display component

#### Character Components
- `StatBar.tsx` — HP/Stamina progress bar with percentage and timer
- `StatCard.tsx` — Individual stat display (level, XP, gold, wins/losses)
- `XPBar.tsx` — XP progress toward next level with current/max display
- `CharacterProfile.tsx` — Full character stats panel

#### Inventory Components
- `ItemSlot.tsx` — Single inventory slot (empty or with item, drag & drop target)
- `ItemCard.tsx` — Item display with color coding (red/blue/green), stats on tap
- `EquipmentGrid.tsx` — 8 armor slots layout (helmet, chest, bracers, boots × 2 sides)
- `CrystalGrid.tsx` — 8 crystal slots layout
- `ItemTooltip.tsx` — Item details popup on tap/hover

#### Battle Components
- `ZoneSelector.tsx` — 4-zone body diagram for attack/defense selection
  Zones: HEAD (top), CHEST (upper), WAIST (middle), LEGS (bottom)
- `BattleTimer.tsx` — 10-second countdown circle animation
- `RoundResult.tsx` — Damage dealt/received display per round
- `BattleLog.tsx` — Scrollable history of all rounds
- `MatchmakingScreen.tsx` — "Searching for opponent..." with cancel button

#### Shop/Auction Components
- `ShopItemCard.tsx` — Item with price, buy button, stock count
- `AuctionLotCard.tsx` — Item with current price, time remaining, bid button
- `BidForm.tsx` — Bid amount input with validation (must exceed current + 1)
- `AuctionTimer.tsx` — Countdown to auction end

### 2. reports/ui-screens.md
Document all screens with:
- Component hierarchy for each page
- Color palette used (dark gaming theme)
- Breakpoint decisions (min 360px)
- Accessibility considerations
- Any UX decisions made and why

---

## Design Requirements from Spec
- Mobile-first: min-width 360px (Telegram standard on mobile)
- Dark theme suitable for gaming (dark backgrounds, bright accents)
- Item colors: RED items, BLUE items, GREEN items — must be visually distinct
- HP bar: green -> yellow -> red as HP decreases
- Stamina bar: blue
- XP bar: purple
- Touch-friendly: minimum tap target 44px
- 5-tab bottom navigation (Telegram Mini App standard pattern)

## Zone Selector Design
```
+----------+
|   HEAD   |  <- Zone 1
+----------+
|  CHEST   |  <- Zone 2
+----------+
|  WAIST   |  <- Zone 3
+----------+
|   LEGS   |  <- Zone 4
+----------+
```
Player selects 1 zone to attack AND 1 zone to defend simultaneously.
