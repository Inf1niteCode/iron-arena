// Iron Arena — Shared TypeScript Types
// Created by: engineering-frontend-developer
// Purpose: All domain types derived from api-contract.md. Single source of truth for frontend.

export interface Player {
  id: number
  telegram_id: number
  name: string
  level: number
  xp: number
  xp_to_next_level: number
  gold: number
  max_hp: number
  current_hp: number
  max_stamina: number
  current_stamina: number
  health_points: number
  stamina: number
  strength: number
  agility: number
  dodge_chance: number
  wins: number
  losses: number
  last_fight_at: string | null
  hp_recovery_at: string | null
  stamina_recovery_at: string | null
}

export interface Item {
  id: number
  player_id: number
  type: 'helmet' | 'chest' | 'bracers' | 'boots' | 'crystal'
  slot: string
  color: 'red' | 'blue' | 'green'
  bonus_stat: 'strength' | 'agility' | 'health_points' | 'stamina'
  bonus_value: number
  is_equipped: boolean
  is_broken: boolean
  enchant_level: number
  armor_value: number
  name: string
}

export interface EquippedSlots {
  head: number | null
  chest: number | null
  waist: number | null
  legs: number | null
  crystal_1: number | null
  crystal_2: number | null
  crystal_3: number | null
  crystal_4: number | null
  crystal_5: number | null
  crystal_6: number | null
  crystal_7: number | null
  crystal_8: number | null
}

export interface ShopItem {
  id: number
  type: string
  color: 'red' | 'blue' | 'green'
  bonus_stat: string
  bonus_value: number
  armor_value: number
  price: number
  name: string
  stock: number
}

export interface AuctionLot {
  id: number
  seller_id: number
  seller_name: string
  item: Item
  start_price: number
  current_price: number
  winner_id: number | null
  winner_name: string | null
  ends_at: string
  status: 'active' | 'completed' | 'cancelled'
  bid_count: number
}

export interface Battle {
  id: number
  player1_id: number
  player1_name: string
  player2_id: number
  player2_name: string
  winner_id: number | null
  mode: 'random' | 'duel'
  xp_gained: number
  gold_gained: number
  rounds: number
  created_at: string
}

// WebSocket message types (from api-contract.md)
export type BattleZone = 'head' | 'chest' | 'waist' | 'legs'

export interface WsWaiting {
  type: 'waiting'
  message: string
}

export interface WsMatched {
  type: 'matched'
  opponent: {
    id: number
    name: string
    level: number
    max_hp: number
    strength: number
    agility: number
  }
  your_hp: number
  your_stamina: number
}

export interface WsRoundStart {
  type: 'round_start'
  round: number
  timer_seconds: number
  your_hp: number
  opponent_hp: number
  your_stamina: number
  opponent_stamina: number
}

export interface WsRoundResult {
  type: 'round_result'
  round: number
  your_attack: { zone: string; damage_dealt: number; dodged: boolean }
  opponent_attack: { zone: string; damage_dealt: number; dodged: boolean }
  your_hp: number
  opponent_hp: number
  your_stamina: number
  opponent_stamina: number
}

export interface WsGameOver {
  type: 'game_over'
  winner_id: number
  you_won: boolean
  xp_gained: number
  gold_gained: number
  total_rounds: number
}

export interface WsError {
  type: 'error'
  code: string
  message: string
}

export type WsMessage = WsWaiting | WsMatched | WsRoundStart | WsRoundResult | WsGameOver | WsError
