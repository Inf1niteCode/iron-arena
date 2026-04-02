// Iron Arena — Create Character Page
// Created by: engineering-frontend-developer
// Purpose: Shown to new players on first login. Name input + 3 stat point allocation.

import React, { useState } from 'react'
import { characterApi } from '@/api/client'
import type { Player } from '@/types'

interface Props {
  onCreated: (player: Player) => void
}

type Stat = 'health_points' | 'strength' | 'agility'

const STAT_INFO: { key: Stat; label: string; icon: string; desc: string }[] = [
  { key: 'health_points', label: 'Health', icon: '❤', desc: '+10 Max HP' },
  { key: 'strength', label: 'Strength', icon: '⚔', desc: '+2 Damage per point' },
  { key: 'agility', label: 'Agility', icon: '💨', desc: '+1.5% Dodge (max 40%)' },
]

export const CreateCharacterPage: React.FC<Props> = ({ onCreated }) => {
  const [name, setName] = useState('')
  const [points, setPoints] = useState<Record<Stat, number>>({
    health_points: 1, strength: 1, agility: 1,
  })
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const totalSpent = points.health_points + points.strength + points.agility
  const remaining = 3 - totalSpent

  function adjust(stat: Stat, delta: number) {
    const next = points[stat] + delta
    if (next < 0) return
    if (delta > 0 && remaining <= 0) return
    setPoints(prev => ({ ...prev, [stat]: next }))
  }

  async function handleCreate() {
    if (name.trim().length < 2) { setError('Name must be at least 2 characters'); return }
    if (remaining !== 0) { setError('Distribute all 3 stat points'); return }
    setCreating(true)
    setError(null)
    try {
      const result = await characterApi.create(name.trim(), points)
      onCreated(result.character)
    } catch (e: unknown) {
      const err = e as { code?: string }
      if (err?.code === 'character_already_exists') setError('Character already created')
      else if (err?.code === 'invalid_stat_distribution') setError('Invalid stat distribution')
      else setError('Failed to create character')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: '#1a1a2e', color: '#fff', minWidth: 360, padding: 24 }}>
      <div style={{ maxWidth: 360, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: 64, marginBottom: 12 }}>⚔</div>
          <h1 style={{ fontSize: 24, fontWeight: 700 }}>Create Your Warrior</h1>
          <p style={{ color: '#888', fontSize: 14, marginTop: 8 }}>
            Name your hero and allocate starting stat points
          </p>
        </div>

        {/* Name input */}
        <div style={{ marginBottom: 24 }}>
          <label style={{ display: 'block', fontSize: 13, color: '#888', marginBottom: 8 }}>Warrior Name</label>
          <input
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="2-20 characters"
            maxLength={20}
            style={{
              width: '100%', padding: '12px 14px',
              background: 'rgba(255,255,255,0.08)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: 10, color: '#fff', fontSize: 16,
            }}
          />
        </div>

        {/* Stat allocation */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: 13, color: '#888' }}>Stat Points</span>
            <span style={{
              fontSize: 14, fontWeight: 700,
              color: remaining === 0 ? '#2ecc71' : '#f1c40f',
            }}>
              {remaining} remaining
            </span>
          </div>

          {STAT_INFO.map(s => (
            <div key={s.key} style={{
              background: 'rgba(255,255,255,0.05)', borderRadius: 10,
              padding: '12px 14px', marginBottom: 8,
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 24 }}>{s.icon}</span>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{s.label}</div>
                  <div style={{ fontSize: 11, color: '#888' }}>{s.desc}</div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <button onClick={() => adjust(s.key, -1)} style={adjustBtn} disabled={points[s.key] <= 0}>−</button>
                <span style={{ fontSize: 18, fontWeight: 700, minWidth: 24, textAlign: 'center' }}>
                  {points[s.key]}
                </span>
                <button onClick={() => adjust(s.key, 1)} style={adjustBtn} disabled={remaining <= 0}>+</button>
              </div>
            </div>
          ))}
        </div>

        {/* Base stats reminder */}
        <div style={{ background: 'rgba(52,152,219,0.1)', borderRadius: 8, padding: 12, marginBottom: 24, fontSize: 12, color: '#888' }}>
          Base stats: 5 in all stats. +3 points to distribute. Starting gold: 100.
        </div>

        {error && (
          <div style={{ color: '#e74c3c', fontSize: 13, marginBottom: 12, textAlign: 'center' }}>
            {error}
          </div>
        )}

        <button
          onClick={handleCreate}
          disabled={creating || remaining !== 0 || name.trim().length < 2}
          style={{
            width: '100%', padding: '14px', background: '#e74c3c',
            color: '#fff', border: 'none', borderRadius: 10,
            fontSize: 16, fontWeight: 700, cursor: 'pointer',
            opacity: (creating || remaining !== 0 || name.trim().length < 2) ? 0.5 : 1,
          }}
        >
          {creating ? 'Creating...' : 'Enter the Arena'}
        </button>
      </div>
    </div>
  )
}

const adjustBtn: React.CSSProperties = {
  width: 32, height: 32, borderRadius: '50%',
  background: 'rgba(255,255,255,0.1)',
  color: '#fff', border: 'none',
  fontSize: 18, cursor: 'pointer',
  display: 'flex', alignItems: 'center', justifyContent: 'center',
}
