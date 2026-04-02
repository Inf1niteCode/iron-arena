// Iron Arena — Arena Page
// Created by: engineering-frontend-developer
// Purpose: PvP matchmaking UI, real-time battle screen with zone selection.
// Connects to WebSocket battle engine after finding a match.

import React, { useState, useCallback } from 'react'
import { battleApi } from '@/api/client'
import { useBattle } from '@/hooks/useBattle'
import type { BattleZone } from '@/types'
import { StatBar } from '@/components/StatBar'
import { GoldDisplay } from '@/components/GoldDisplay'

type ArenaView = 'lobby' | 'searching' | 'battle' | 'result'

const ZONES: { zone: BattleZone; label: string; icon: string }[] = [
  { zone: 'head', label: 'Head', icon: '⛑' },
  { zone: 'chest', label: 'Chest', icon: '🛡' },
  { zone: 'waist', label: 'Waist', icon: '🦺' },
  { zone: 'legs', label: 'Legs', icon: '👟' },
]

export const ArenaPage: React.FC = () => {
  const [view, setView] = useState<ArenaView>('lobby')
  const [battleId, setBattleId] = useState<number | null>(null)
  const [token] = useState<string | null>(() => localStorage.getItem('iron_arena_token'))
  const [attackZone, setAttackZone] = useState<BattleZone | null>(null)
  const [defendZone, setDefendZone] = useState<BattleZone | null>(null)
  const [moveSent, setMoveSent] = useState(false)

  const { state: battle, sendMove } = useBattle(battleId, token)

  const handleFindMatch = useCallback(async () => {
    setView('searching')
    try {
      const result = await battleApi.find()
      if (result.battle_id) {
        setBattleId(result.battle_id)
        setView('battle')
      }
    } catch {
      setView('lobby')
    }
  }, [])

  const handleSendMove = useCallback(() => {
    if (!attackZone || !defendZone || moveSent) return
    sendMove(attackZone, defendZone)
    setMoveSent(true)
  }, [attackZone, defendZone, moveSent, sendMove])

  // Reset move when new round starts
  React.useEffect(() => {
    if (battle.status === 'in_round') {
      setMoveSent(false)
      setAttackZone(null)
      setDefendZone(null)
    }
    if (battle.status === 'game_over') {
      setView('result')
    }
  }, [battle.status, battle.round])

  if (view === 'lobby') {
    return (
      <div style={pageStyle}>
        <div style={{ textAlign: 'center', padding: '60px 24px' }}>
          <div style={{ fontSize: 72, marginBottom: 16 }}>🏟</div>
          <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Iron Arena</h1>
          <p style={{ color: '#888', fontSize: 14, marginBottom: 32 }}>
            Find a random opponent and fight for glory and gold!
          </p>
          <button onClick={handleFindMatch} style={primaryBtn}>
            Find Match
          </button>
        </div>
      </div>
    )
  }

  if (view === 'searching') {
    return (
      <div style={{ ...pageStyle, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 16, animation: 'pulse 1s infinite' }}>⚔</div>
          <p style={{ color: '#888' }}>Searching for opponent...</p>
          {battle.status === 'waiting' && <p style={{ color: '#555', fontSize: 12, marginTop: 8 }}>Waiting in queue</p>}
        </div>
      </div>
    )
  }

  if (view === 'result' && battle.gameOver) {
    const go = battle.gameOver
    return (
      <div style={pageStyle}>
        <div style={{ textAlign: 'center', padding: '48px 24px' }}>
          <div style={{ fontSize: 64, marginBottom: 16 }}>
            {go.you_won ? '🏆' : '💀'}
          </div>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: go.you_won ? '#f1c40f' : '#e74c3c', marginBottom: 8 }}>
            {go.you_won ? 'Victory!' : 'Defeated'}
          </h1>
          <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: 12, padding: 20, marginBottom: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-around' }}>
              <div>
                <div style={{ fontSize: 22, fontWeight: 700, color: '#3498db' }}>+{go.xp_gained}</div>
                <div style={{ fontSize: 12, color: '#888' }}>XP</div>
              </div>
              <div>
                <div style={{ fontSize: 22, fontWeight: 700, color: '#f1c40f' }}>
                  +{go.gold_gained}
                </div>
                <div style={{ fontSize: 12, color: '#888' }}>Gold</div>
              </div>
              <div>
                <div style={{ fontSize: 22, fontWeight: 700, color: '#2ecc71' }}>{go.total_rounds}</div>
                <div style={{ fontSize: 12, color: '#888' }}>Rounds</div>
              </div>
            </div>
          </div>
          <button onClick={() => { setView('lobby'); setBattleId(null) }} style={primaryBtn}>
            Back to Arena
          </button>
        </div>
      </div>
    )
  }

  // Battle screen
  return (
    <div style={pageStyle}>
      {/* Opponent info */}
      {battle.opponent && (
        <div style={{ padding: '12px 16px', background: 'rgba(231,76,60,0.08)', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <span style={{ fontWeight: 600, fontSize: 14 }}>vs {battle.opponent.name}</span>
            <span style={{ fontSize: 12, color: '#888' }}>Lv.{battle.opponent.level}</span>
          </div>
          <StatBar current={battle.opponentHp} max={battle.opponent.max_hp} color="red" label="Opponent HP" />
        </div>
      )}

      {/* Your HP */}
      <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <StatBar current={battle.yourHp} max={100} color="green" label="Your HP" />
        <StatBar current={battle.yourStamina} max={100} color="yellow" label="Stamina" />
      </div>

      {/* Round indicator + timer */}
      {battle.status === 'in_round' && (
        <div style={{ textAlign: 'center', padding: '10px', background: 'rgba(0,0,0,0.2)' }}>
          <span style={{ color: '#888', fontSize: 13 }}>Round {battle.round}</span>
          <span style={{
            marginLeft: 12, fontSize: 18, fontWeight: 700,
            color: battle.timerSeconds <= 3 ? '#e74c3c' : '#f1c40f',
          }}>
            {battle.timerSeconds}s
          </span>
        </div>
      )}

      {/* Last round result */}
      {battle.lastRoundResult && (
        <div style={{ padding: '8px 16px', fontSize: 12, background: 'rgba(255,255,255,0.03)' }}>
          <div style={{ color: '#2ecc71' }}>
            Your attack: {battle.lastRoundResult.your_attack.zone}
            {battle.lastRoundResult.your_attack.dodged
              ? ' — DODGED'
              : ` — ${battle.lastRoundResult.your_attack.damage_dealt} dmg`}
          </div>
          <div style={{ color: '#e74c3c' }}>
            Opponent: {battle.lastRoundResult.opponent_attack.zone}
            {battle.lastRoundResult.opponent_attack.dodged
              ? ' — DODGED'
              : ` — ${battle.lastRoundResult.opponent_attack.damage_dealt} dmg`}
          </div>
        </div>
      )}

      {/* Move Selection */}
      {battle.status === 'in_round' && !moveSent && (
        <div style={{ padding: 16 }}>
          <div style={{ marginBottom: 16 }}>
            <p style={{ fontSize: 13, color: '#888', marginBottom: 8 }}>Attack zone:</p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {ZONES.map(z => (
                <button
                  key={z.zone}
                  onClick={() => setAttackZone(z.zone)}
                  style={{
                    ...zoneBtn,
                    background: attackZone === z.zone ? 'rgba(231,76,60,0.3)' : 'rgba(255,255,255,0.06)',
                    border: attackZone === z.zone ? '2px solid #e74c3c' : '2px solid transparent',
                  }}
                >
                  {z.icon} {z.label}
                </button>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: 16 }}>
            <p style={{ fontSize: 13, color: '#888', marginBottom: 8 }}>Defend zone:</p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {ZONES.map(z => (
                <button
                  key={z.zone}
                  onClick={() => setDefendZone(z.zone)}
                  style={{
                    ...zoneBtn,
                    background: defendZone === z.zone ? 'rgba(52,152,219,0.3)' : 'rgba(255,255,255,0.06)',
                    border: defendZone === z.zone ? '2px solid #3498db' : '2px solid transparent',
                  }}
                >
                  {z.icon} {z.label}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleSendMove}
            disabled={!attackZone || !defendZone}
            style={{
              ...primaryBtn,
              width: '100%',
              opacity: (!attackZone || !defendZone) ? 0.4 : 1,
            }}
          >
            Confirm Move
          </button>
        </div>
      )}

      {battle.status === 'in_round' && moveSent && (
        <div style={{ textAlign: 'center', padding: 24, color: '#888' }}>
          Waiting for opponent...
        </div>
      )}

      {battle.status === 'waiting' && (
        <div style={{ textAlign: 'center', padding: 24, color: '#888' }}>
          Searching for opponent...
        </div>
      )}

      {battle.status === 'matched' && (
        <div style={{ textAlign: 'center', padding: 24, color: '#2ecc71' }}>
          Opponent found! Preparing battle...
        </div>
      )}
    </div>
  )
}

const pageStyle: React.CSSProperties = {
  minHeight: '100vh',
  background: '#1a1a2e',
  color: '#fff',
  minWidth: 360,
  paddingBottom: 80,
}

const primaryBtn: React.CSSProperties = {
  background: '#e74c3c',
  color: '#fff',
  border: 'none',
  borderRadius: 10,
  padding: '14px 32px',
  fontSize: 16,
  fontWeight: 700,
  cursor: 'pointer',
  display: 'inline-block',
}

const zoneBtn: React.CSSProperties = {
  padding: '12px 0',
  borderRadius: 8,
  color: '#fff',
  cursor: 'pointer',
  fontSize: 14,
  fontWeight: 500,
  transition: 'all 0.15s',
}
