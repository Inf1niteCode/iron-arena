// Iron Arena — API Client
// Created by: engineering-frontend-developer
// Purpose: Typed fetch wrapper for all REST API calls. Reads token from localStorage.
// All endpoints match api-contract.md exactly.

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

function getToken(): string | null {
  return localStorage.getItem('iron_arena_token')
}

export function setToken(token: string): void {
  localStorage.setItem('iron_arena_token', token)
}

export function clearToken(): void {
  localStorage.removeItem('iron_arena_token')
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> ?? {}),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'network_error' }))
    throw new ApiError(res.status, err?.error ?? 'unknown_error', err)
  }

  return res.json() as Promise<T>
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    public body: unknown,
  ) {
    super(`API error ${status}: ${code}`)
  }
}

// ── Auth ───────────────────────────────────────────────────────────────────────

export const authApi = {
  telegram: (initData: string) =>
    request<{ token: string; player: import('@/types').Player }>('/auth/telegram', {
      method: 'POST',
      body: JSON.stringify({ init_data: initData }),
    }),
}

// ── Character ──────────────────────────────────────────────────────────────────

export const characterApi = {
  get: () => request<import('@/types').Player>('/character'),
  create: (name: string, statPoints: { health_points: number; strength: number; agility: number }) =>
    request<{ success: boolean; character: import('@/types').Player }>('/character/create', {
      method: 'POST',
      body: JSON.stringify({ name, stat_points: statPoints }),
    }),
}

// ── Inventory ──────────────────────────────────────────────────────────────────

export const inventoryApi = {
  get: () =>
    request<{ items: import('@/types').Item[]; equipped: import('@/types').EquippedSlots }>('/inventory'),
  equip: (itemId: number) =>
    request<{ success: boolean; unequipped_item_id: number | null; character: Partial<import('@/types').Player> }>(
      '/inventory/equip',
      { method: 'POST', body: JSON.stringify({ item_id: itemId }) },
    ),
  unequip: (itemId: number) =>
    request<{ success: boolean; character: Partial<import('@/types').Player> }>(
      '/inventory/unequip',
      { method: 'POST', body: JSON.stringify({ item_id: itemId }) },
    ),
}

// ── Shop ────────────────────────────────────────────────────────────────────────

export const shopApi = {
  items: () =>
    request<{ items: import('@/types').ShopItem[]; refreshes_at: string }>('/shop/items'),
  buy: (shopItemId: number) =>
    request<{ success: boolean; item: import('@/types').Item; gold_remaining: number }>(
      '/shop/buy',
      { method: 'POST', body: JSON.stringify({ shop_item_id: shopItemId }) },
    ),
}

// ── Auction ────────────────────────────────────────────────────────────────────

export const auctionApi = {
  lots: (page = 1, limit = 20, status = 'active') =>
    request<{ lots: import('@/types').AuctionLot[]; total: number; page: number }>(
      `/auction/lots?page=${page}&limit=${limit}&status=${status}`,
    ),
  create: (itemId: number, startPrice: number, durationHours: number) =>
    request<{ success: boolean; lot: import('@/types').AuctionLot }>(
      '/auction/create',
      { method: 'POST', body: JSON.stringify({ item_id: itemId, start_price: startPrice, duration_hours: durationHours }) },
    ),
  bid: (lotId: number, amount: number) =>
    request<{ success: boolean; new_price: number; gold_blocked: number; gold_remaining: number }>(
      '/auction/bid',
      { method: 'POST', body: JSON.stringify({ lot_id: lotId, amount }) },
    ),
  history: (lotId: number) =>
    request<{ bids: Array<{ id: number; bidder_id: number; bidder_name: string; amount: number; created_at: string }> }>(
      `/auction/history?lot_id=${lotId}`,
    ),
}

// ── Battle ─────────────────────────────────────────────────────────────────────

export const battleApi = {
  find: () =>
    request<{ battle_id: number | null; status: string; ws_url: string }>(
      '/battle/find',
      { method: 'POST', body: JSON.stringify({}) },
    ),
  challenge: (targetPlayerId: number) =>
    request<{ battle_id: number; status: string; ws_url: string }>(
      '/battle/challenge',
      { method: 'POST', body: JSON.stringify({ target_player_id: targetPlayerId }) },
    ),
  get: (battleId: number) =>
    request<import('@/types').Battle>(`/battle/${battleId}`),
}
