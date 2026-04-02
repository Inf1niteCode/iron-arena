// Iron Arena — Shop Page
// Created by: engineering-frontend-developer
// Purpose: Rotating item shop with gold purchase. Countdown to next refresh.

import React, { useEffect, useState, useCallback } from 'react'
import { shopApi } from '@/api/client'
import type { ShopItem } from '@/types'
import { GoldDisplay } from '@/components/GoldDisplay'

interface ShopState {
  items: ShopItem[]
  refreshesAt: string | null
  playerGold: number
  loading: boolean
  error: string | null
}

const COLOR_ACCENT: Record<string, string> = {
  red: '#e74c3c',
  blue: '#3498db',
  green: '#2ecc71',
}

const TYPE_ICONS: Record<string, string> = {
  helmet: '⛑', chest: '🛡', bracers: '🦺', boots: '👟', crystal: '💎',
}

export const ShopPage: React.FC = () => {
  const [state, setState] = useState<ShopState>({
    items: [], refreshesAt: null, playerGold: 0, loading: true, error: null,
  })
  const [buying, setBuying] = useState<number | null>(null)
  const [toast, setToast] = useState<string | null>(null)

  const showToast = (msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(null), 2500)
  }

  const load = useCallback(async () => {
    try {
      const data = await shopApi.items()
      setState(prev => ({
        ...prev,
        items: data.items,
        refreshesAt: data.refreshes_at,
        loading: false,
      }))
    } catch {
      setState(prev => ({ ...prev, loading: false, error: 'Failed to load shop' }))
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleBuy = async (item: ShopItem) => {
    if (buying) return
    setBuying(item.id)
    try {
      const result = await shopApi.buy(item.id)
      showToast(`Bought ${item.name}!`)
      setState(prev => ({
        ...prev,
        playerGold: result.gold_remaining,
        items: prev.items.map(i =>
          i.id === item.id ? { ...i, stock: i.stock - 1 } : i
        ),
      }))
    } catch (e: unknown) {
      const err = e as { code?: string }
      if (err?.code === 'insufficient_gold') showToast('Not enough gold!')
      else if (err?.code === 'out_of_stock') showToast('Out of stock!')
      else showToast('Purchase failed')
    } finally {
      setBuying(null)
    }
  }

  if (state.loading) return <div style={centeredStyle}>Loading shop...</div>
  if (state.error) return <div style={{ ...centeredStyle, color: '#e74c3c' }}>{state.error}</div>

  return (
    <div style={pageStyle}>
      {toast && <div style={toastStyle}>{toast}</div>}

      <div style={{ padding: '16px', borderBottom: '1px solid rgba(255,255,255,0.08)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: 18, fontWeight: 700 }}>Shop</h1>
          {state.refreshesAt && (
            <p style={{ fontSize: 11, color: '#555', marginTop: 2 }}>
              Refreshes: {new Date(state.refreshesAt).toLocaleTimeString()}
            </p>
          )}
        </div>
        <GoldDisplay amount={state.playerGold} />
      </div>

      <div style={{ padding: 16, paddingBottom: 80 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          {state.items.map(item => {
            const accent = COLOR_ACCENT[item.color] ?? '#888'
            const icon = TYPE_ICONS[item.type] ?? '?'
            const outOfStock = item.stock <= 0
            return (
              <div
                key={item.id}
                style={{
                  background: 'rgba(255,255,255,0.04)',
                  border: `1px solid ${outOfStock ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.12)'}`,
                  borderRadius: 10,
                  padding: 12,
                  opacity: outOfStock ? 0.5 : 1,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <span style={{ fontSize: 24 }}>{icon}</span>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: accent }}>{item.name}</div>
                    <div style={{ fontSize: 10, color: '#888', textTransform: 'capitalize' }}>{item.color} {item.type}</div>
                  </div>
                </div>

                <div style={{ fontSize: 11, color: '#ccc', marginBottom: 8 }}>
                  {item.armor_value > 0 && <div>Armor: {item.armor_value}</div>}
                  <div>+{item.bonus_value} {item.bonus_stat.replace('_', ' ')}</div>
                  <div style={{ color: '#555' }}>Stock: {item.stock}</div>
                </div>

                <button
                  onClick={() => handleBuy(item)}
                  disabled={outOfStock || buying === item.id}
                  style={{
                    width: '100%',
                    background: outOfStock ? '#333' : accent,
                    color: '#fff',
                    border: 'none',
                    borderRadius: 6,
                    padding: '7px 0',
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: outOfStock ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 4,
                  }}
                >
                  <span style={{ color: '#f1c40f' }}>&#9734;</span>
                  {item.price}
                </button>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

const pageStyle: React.CSSProperties = {
  minHeight: '100vh',
  background: '#1a1a2e',
  color: '#fff',
  minWidth: 360,
  position: 'relative',
}

const centeredStyle: React.CSSProperties = {
  display: 'flex', alignItems: 'center', justifyContent: 'center',
  height: '100vh', color: '#888',
}

const toastStyle: React.CSSProperties = {
  position: 'fixed', top: 20, left: '50%', transform: 'translateX(-50%)',
  background: 'rgba(0,0,0,0.85)', color: '#fff',
  padding: '8px 18px', borderRadius: 20,
  fontSize: 13, fontWeight: 500, zIndex: 200,
}
