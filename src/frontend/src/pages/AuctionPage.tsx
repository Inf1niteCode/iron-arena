// Iron Arena — Auction Page
// Created by: engineering-frontend-developer
// Purpose: Browse active auction lots, place bids, list items for sale.
// Reads from api-contract.md: GET /auction/lots, POST /auction/bid, POST /auction/create

import React, { useEffect, useState, useCallback } from 'react'
import { auctionApi } from '@/api/client'
import type { AuctionLot } from '@/types'
import { GoldDisplay } from '@/components/GoldDisplay'

interface AuctionState {
  lots: AuctionLot[]
  total: number
  page: number
  loading: boolean
  error: string | null
}

const COLOR_ACCENT: Record<string, string> = {
  red: '#e74c3c', blue: '#3498db', green: '#2ecc71',
}

function timeLeft(endsAt: string): string {
  const ms = new Date(endsAt).getTime() - Date.now()
  if (ms <= 0) return 'Ended'
  const h = Math.floor(ms / 3600000)
  const m = Math.floor((ms % 3600000) / 60000)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

export const AuctionPage: React.FC = () => {
  const [state, setState] = useState<AuctionState>({
    lots: [], total: 0, page: 1, loading: true, error: null,
  })
  const [selectedLot, setSelectedLot] = useState<AuctionLot | null>(null)
  const [bidAmount, setBidAmount] = useState('')
  const [bidding, setBidding] = useState(false)
  const [toast, setToast] = useState<string | null>(null)

  const showToast = (msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(null), 2500)
  }

  const load = useCallback(async (page = 1) => {
    setState(prev => ({ ...prev, loading: true }))
    try {
      const data = await auctionApi.lots(page)
      setState({ lots: data.lots, total: data.total, page: data.page, loading: false, error: null })
    } catch {
      setState(prev => ({ ...prev, loading: false, error: 'Failed to load auction' }))
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleBid = async () => {
    if (!selectedLot || !bidAmount) return
    const amount = parseInt(bidAmount, 10)
    if (isNaN(amount) || amount <= selectedLot.current_price) {
      showToast(`Bid must be > ${selectedLot.current_price}`)
      return
    }
    setBidding(true)
    try {
      await auctionApi.bid(selectedLot.id, amount)
      showToast('Bid placed!')
      setSelectedLot(null)
      setBidAmount('')
      await load(state.page)
    } catch (e: unknown) {
      const err = e as { code?: string }
      if (err?.code === 'bid_too_low') showToast('Bid too low!')
      else if (err?.code === 'insufficient_gold') showToast('Not enough gold!')
      else if (err?.code === 'own_auction') showToast("Can't bid on your own auction")
      else showToast('Bid failed')
    } finally {
      setBidding(false)
    }
  }

  if (state.loading) return <div style={centeredStyle}>Loading auction...</div>
  if (state.error) return <div style={{ ...centeredStyle, color: '#e74c3c' }}>{state.error}</div>

  return (
    <div style={pageStyle}>
      {toast && <div style={toastStyle}>{toast}</div>}

      {/* Bid modal */}
      {selectedLot && (
        <div style={modalOverlay}>
          <div style={modalBox}>
            <h2 style={{ fontSize: 16, marginBottom: 12 }}>Place Bid</h2>
            <div style={{ marginBottom: 12, fontSize: 13 }}>
              <div style={{ color: '#888' }}>{selectedLot.item.name}</div>
              <div style={{ color: '#f1c40f', marginTop: 4 }}>
                Current price: &#9734; {selectedLot.current_price}
              </div>
              <div style={{ color: '#555', fontSize: 11 }}>Time left: {timeLeft(selectedLot.ends_at)}</div>
            </div>
            <input
              type="number"
              value={bidAmount}
              onChange={e => setBidAmount(e.target.value)}
              placeholder={`Min: ${selectedLot.current_price + 1}`}
              style={inputStyle}
            />
            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
              <button onClick={() => setSelectedLot(null)} style={cancelBtn}>Cancel</button>
              <button onClick={handleBid} disabled={bidding} style={primaryBtn}>
                {bidding ? 'Bidding...' : 'Confirm Bid'}
              </button>
            </div>
          </div>
        </div>
      )}

      <div style={{ padding: '16px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        <h1 style={{ fontSize: 18, fontWeight: 700 }}>Auction House</h1>
        <p style={{ fontSize: 12, color: '#888', marginTop: 4 }}>{state.total} active lots</p>
      </div>

      <div style={{ padding: 12, paddingBottom: 80 }}>
        {state.lots.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#555', padding: '40px 0' }}>
            No active lots
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {state.lots.map(lot => {
              const accent = COLOR_ACCENT[lot.item.color] ?? '#888'
              return (
                <div
                  key={lot.id}
                  style={{
                    background: 'rgba(255,255,255,0.04)',
                    border: `1px solid rgba(255,255,255,0.1)`,
                    borderLeft: `3px solid ${accent}`,
                    borderRadius: 10,
                    padding: 12,
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 14, color: accent }}>{lot.item.name}</div>
                      <div style={{ fontSize: 11, color: '#888' }}>by {lot.seller_name}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <GoldDisplay amount={lot.current_price} size="sm" />
                      <div style={{ fontSize: 10, color: '#555', marginTop: 2 }}>{timeLeft(lot.ends_at)}</div>
                    </div>
                  </div>

                  <div style={{ fontSize: 11, color: '#ccc', marginBottom: 10 }}>
                    {lot.item.armor_value > 0 && <span>Armor {lot.item.armor_value} · </span>}
                    <span>+{lot.item.bonus_value} {lot.item.bonus_stat.replace('_', ' ')}</span>
                    {lot.bid_count > 0 && <span style={{ color: '#888' }}> · {lot.bid_count} bids</span>}
                  </div>

                  <button
                    onClick={() => { setSelectedLot(lot); setBidAmount(String(lot.current_price + 1)) }}
                    style={{ ...primaryBtn, fontSize: 13, padding: '7px 16px' }}
                  >
                    Place Bid
                  </button>
                </div>
              )
            })}
          </div>
        )}

        {/* Pagination */}
        {state.total > 20 && (
          <div style={{ display: 'flex', justifyContent: 'center', gap: 12, marginTop: 16 }}>
            <button
              onClick={() => load(state.page - 1)}
              disabled={state.page <= 1}
              style={{ ...cancelBtn, opacity: state.page <= 1 ? 0.4 : 1 }}
            >
              Prev
            </button>
            <span style={{ color: '#888', alignSelf: 'center', fontSize: 13 }}>
              Page {state.page}
            </span>
            <button
              onClick={() => load(state.page + 1)}
              disabled={state.lots.length < 20}
              style={{ ...cancelBtn, opacity: state.lots.length < 20 ? 0.4 : 1 }}
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

const pageStyle: React.CSSProperties = {
  minHeight: '100vh', background: '#1a1a2e', color: '#fff',
  minWidth: 360, position: 'relative',
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

const modalOverlay: React.CSSProperties = {
  position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
  display: 'flex', alignItems: 'flex-end', zIndex: 150,
}

const modalBox: React.CSSProperties = {
  background: '#16213e', borderRadius: '16px 16px 0 0',
  padding: 24, width: '100%',
}

const inputStyle: React.CSSProperties = {
  width: '100%', padding: '10px 12px',
  background: 'rgba(255,255,255,0.08)',
  border: '1px solid rgba(255,255,255,0.2)',
  borderRadius: 8, color: '#fff', fontSize: 16,
}

const primaryBtn: React.CSSProperties = {
  background: '#e74c3c', color: '#fff', border: 'none',
  borderRadius: 8, padding: '10px 20px', fontSize: 14,
  fontWeight: 600, cursor: 'pointer', flex: 1,
}

const cancelBtn: React.CSSProperties = {
  background: 'rgba(255,255,255,0.1)', color: '#fff', border: 'none',
  borderRadius: 8, padding: '10px 20px', fontSize: 14,
  cursor: 'pointer', flex: 1,
}
