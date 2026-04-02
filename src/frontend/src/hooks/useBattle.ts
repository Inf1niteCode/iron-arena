// Iron Arena — Battle WebSocket Hook
// Created by: engineering-frontend-developer
// Purpose: Manages WebSocket connection for PvP battles, parses all server messages

import { useState, useEffect, useRef, useCallback } from 'react'
import type { WsMessage, WsMatched, WsRoundStart, WsRoundResult, WsGameOver, BattleZone } from '@/types'

const WS_BASE = import.meta.env.VITE_WS_BASE_URL ?? '/ws'

interface BattleState {
  status: 'connecting' | 'waiting' | 'matched' | 'in_round' | 'game_over' | 'error'
  round: number
  timerSeconds: number
  yourHp: number
  opponentHp: number
  yourStamina: number
  opponentStamina: number
  opponent: WsMatched['opponent'] | null
  lastRoundResult: WsRoundResult | null
  gameOver: WsGameOver | null
  error: string | null
}

const INITIAL_STATE: BattleState = {
  status: 'connecting',
  round: 0,
  timerSeconds: 10,
  yourHp: 0,
  opponentHp: 0,
  yourStamina: 0,
  opponentStamina: 0,
  opponent: null,
  lastRoundResult: null,
  gameOver: null,
  error: null,
}

export function useBattle(battleId: number | null, token: string | null) {
  const [state, setState] = useState<BattleState>(INITIAL_STATE)
  const wsRef = useRef<WebSocket | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const sendMove = useCallback((attackZone: BattleZone, defendZone: BattleZone) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'move',
        attack_zone: attackZone,
        defend_zone: defendZone,
      }))
    }
  }, [])

  useEffect(() => {
    if (!battleId || !token) return

    const wsUrl = `${WS_BASE}/battle/${battleId}?token=${token}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setState(prev => ({ ...prev, status: 'connecting' }))
    }

    ws.onmessage = (event: MessageEvent) => {
      const msg = JSON.parse(event.data as string) as WsMessage

      switch (msg.type) {
        case 'waiting':
          setState(prev => ({ ...prev, status: 'waiting' }))
          break

        case 'matched': {
          const m = msg as WsMatched
          setState(prev => ({
            ...prev,
            status: 'matched',
            opponent: m.opponent,
            yourHp: m.your_hp,
            yourStamina: m.your_stamina,
          }))
          break
        }

        case 'round_start': {
          const r = msg as WsRoundStart
          // Clear old timer and start countdown
          if (timerRef.current) clearInterval(timerRef.current)
          let remaining = r.timer_seconds
          setState(prev => ({
            ...prev,
            status: 'in_round',
            round: r.round,
            timerSeconds: remaining,
            yourHp: r.your_hp,
            opponentHp: r.opponent_hp,
            yourStamina: r.your_stamina,
            opponentStamina: r.opponent_stamina,
          }))
          timerRef.current = setInterval(() => {
            remaining -= 1
            setState(prev => ({ ...prev, timerSeconds: Math.max(0, remaining) }))
            if (remaining <= 0 && timerRef.current) {
              clearInterval(timerRef.current)
            }
          }, 1000)
          break
        }

        case 'round_result': {
          const rr = msg as WsRoundResult
          if (timerRef.current) clearInterval(timerRef.current)
          setState(prev => ({
            ...prev,
            lastRoundResult: rr,
            yourHp: rr.your_hp,
            opponentHp: rr.opponent_hp,
          }))
          break
        }

        case 'game_over': {
          const go = msg as WsGameOver
          if (timerRef.current) clearInterval(timerRef.current)
          setState(prev => ({ ...prev, status: 'game_over', gameOver: go }))
          ws.close()
          break
        }

        case 'error':
          setState(prev => ({ ...prev, status: 'error', error: msg.message }))
          break
      }
    }

    ws.onerror = () => {
      setState(prev => ({ ...prev, status: 'error', error: 'Connection error' }))
    }

    ws.onclose = () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }

    return () => {
      ws.close()
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [battleId, token])

  return { state, sendMove }
}
