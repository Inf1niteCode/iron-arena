// Iron Arena — Character Profile Page
// Created by: engineering-frontend-developer
// Purpose: Shows player stats, XP bar, HP/Stamina bars, win/loss record

import React, { useEffect, useState } from 'react'
import { characterApi } from '@/api/client'
import type { Player } from '@/types'
import { StatBar } from '@/components/StatBar'
import { GoldDisplay } from '@/components/GoldDisplay'

export const CharacterPage: React.FC = () => {
  const [player, setPlayer] = useState<Player | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    characterApi.get()
      .then(setPlayer)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingScreen />
  if (error) return <ErrorScreen message={error} />
  if (!player) return null

  const xpPct = player.xp_to_next_level > 0
    ? Math.round((player.xp / player.xp_to_next_level) * 100)
    : 0

  return (
    <div style={pageStyle}>
      {/* Header */}
      <div style={{ textAlign: 'center', padding: '20px 16px 12px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        <div style={{ fontSize: 48, marginBottom: 8 }}>⚔</div>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: '#e74c3c', marginBottom: 4 }}>{player.name}</h1>
        <div style={{ display: 'flex', justifyContent: 'center', gap: 12, alignItems: 'center' }}>
          <span style={{ background: 'rgba(231,76,60,0.2)', color: '#e74c3c', padding: '2px 10px', borderRadius: 12, fontSize: 13, fontWeight: 600 }}>
            Level {player.level}
          </span>
          <GoldDisplay amount={player.gold} size="sm" />
        </div>
      </div>

      <div style={{ padding: '16px', paddingBottom: 80 }}>
        {/* XP Bar */}
        <section style={cardStyle}>
          <h2 style={sectionTitle}>Experience</h2>
          <StatBar current={player.xp} max={player.xp_to_next_level} color="blue" label={`XP (${xpPct}% to level ${player.level + 1})`} />
        </section>

        {/* Resources */}
        <section style={cardStyle}>
          <h2 style={sectionTitle}>Resources</h2>
          <StatBar current={player.current_hp} max={player.max_hp} color="red" label="Hit Points" />
          <StatBar current={player.current_stamina} max={player.max_stamina} color="yellow" label="Stamina" />
        </section>

        {/* Battle Stats */}
        <section style={cardStyle}>
          <h2 style={sectionTitle}>Combat Stats</h2>
          <div style={statGrid}>
            <Stat label="Strength" value={player.strength} icon="⚔" />
            <Stat label="Agility" value={player.agility} icon="💨" />
            <Stat label="Health" value={player.health_points} icon="❤" />
            <Stat label="Stamina" value={player.stamina} icon="⚡" />
            <Stat label="Dodge" value={`${player.dodge_chance.toFixed(1)}%`} icon="🌀" />
            <Stat label="Max HP" value={player.max_hp} icon="🛡" />
          </div>
        </section>

        {/* Battle Record */}
        <section style={cardStyle}>
          <h2 style={sectionTitle}>Battle Record</h2>
          <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center' }}>
            <div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#2ecc71' }}>{player.wins}</div>
              <div style={{ fontSize: 12, color: '#999' }}>Wins</div>
            </div>
            <div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#e74c3c' }}>{player.losses}</div>
              <div style={{ fontSize: 12, color: '#999' }}>Losses</div>
            </div>
            <div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#3498db' }}>
                {player.wins + player.losses > 0
                  ? Math.round((player.wins / (player.wins + player.losses)) * 100)
                  : 0}%
              </div>
              <div style={{ fontSize: 12, color: '#999' }}>Win Rate</div>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

// ── Sub-components ──────────────────────────────────────────────────────────────

const Stat: React.FC<{ label: string; value: number | string; icon: string }> = ({ label, value, icon }) => (
  <div style={{ background: 'rgba(255,255,255,0.04)', borderRadius: 8, padding: '10px 8px', textAlign: 'center' }}>
    <div style={{ fontSize: 18, marginBottom: 4 }}>{icon}</div>
    <div style={{ fontSize: 16, fontWeight: 700 }}>{value}</div>
    <div style={{ fontSize: 11, color: '#999' }}>{label}</div>
  </div>
)

const LoadingScreen: React.FC = () => (
  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', color: '#888' }}>
    Loading...
  </div>
)

const ErrorScreen: React.FC<{ message: string }> = ({ message }) => (
  <div style={{ padding: 20, color: '#e74c3c', textAlign: 'center', marginTop: 40 }}>
    {message}
  </div>
)

// ── Styles ──────────────────────────────────────────────────────────────────────
const pageStyle: React.CSSProperties = {
  minHeight: '100vh',
  background: '#1a1a2e',
  color: '#fff',
  minWidth: 360,
}

const cardStyle: React.CSSProperties = {
  background: 'rgba(255,255,255,0.04)',
  borderRadius: 12,
  padding: 16,
  marginBottom: 12,
}

const sectionTitle: React.CSSProperties = {
  fontSize: 13,
  fontWeight: 600,
  color: '#888',
  textTransform: 'uppercase',
  letterSpacing: 1,
  marginBottom: 12,
}

const statGrid: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(3, 1fr)',
  gap: 8,
}
