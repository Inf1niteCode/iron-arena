// Iron Arena — Auth Hook
// Created by: engineering-frontend-developer
// Purpose: Telegram WebApp SDK authentication + JWT management

import { useState, useEffect } from 'react'
import { authApi, setToken, clearToken } from '@/api/client'
import type { Player } from '@/types'

interface AuthState {
  player: Player | null
  loading: boolean
  error: string | null
  isNew: boolean
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    player: null,
    loading: true,
    error: null,
    isNew: false,
  })

  useEffect(() => {
    async function authenticate() {
      try {
        // Get Telegram WebApp initData
        // @ts-ignore — Telegram WebApp is injected by Telegram client
        const tg = window.Telegram?.WebApp
        let initData = tg?.initData ?? ''

        // Development fallback: use test initData
        if (!initData) {
          console.warn('Telegram WebApp not available, using dev mode')
          initData = `user=${encodeURIComponent(JSON.stringify({ id: 12345, first_name: 'DevUser' }))}&auth_date=${Math.floor(Date.now() / 1000)}&hash=dev`
        }

        const result = await authApi.telegram(initData)
        setToken(result.token)

        setState({
          player: result.player,
          loading: false,
          error: null,
          isNew: result.player.is_new ?? false,
        })

        // Configure Telegram WebApp
        if (tg) {
          tg.ready()
          tg.expand()
        }
      } catch (err) {
        clearToken()
        setState({
          player: null,
          loading: false,
          error: err instanceof Error ? err.message : 'Authentication failed',
          isNew: false,
        })
      }
    }

    authenticate()
  }, [])

  function updatePlayer(player: Player) {
    setState(prev => ({ ...prev, player }))
  }

  return { ...state, updatePlayer }
}
