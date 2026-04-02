// Iron Arena — ItemCard Component
// Created by: design-ui-designer
// Purpose: Displays a single inventory item with stats and equipped/broken status

import React from 'react'
import type { Item } from '@/types'

interface ItemCardProps {
  item: Item
  onEquip?: (item: Item) => void
  onUnequip?: (item: Item) => void
  onList?: (item: Item) => void
  compact?: boolean
}

const COLOR_ACCENT: Record<string, string> = {
  red: '#e74c3c',
  blue: '#3498db',
  green: '#2ecc71',
}

const TYPE_ICONS: Record<string, string> = {
  helmet: '⛑',
  chest: '🛡',
  bracers: '🦺',
  boots: '👟',
  crystal: '💎',
}

export const ItemCard: React.FC<ItemCardProps> = ({ item, onEquip, onUnequip, onList, compact = false }) => {
  const accent = COLOR_ACCENT[item.color] ?? '#888'
  const icon = TYPE_ICONS[item.type] ?? '?'

  return (
    <div style={{
      background: 'rgba(255,255,255,0.06)',
      border: `1px solid ${item.is_equipped ? accent : 'rgba(255,255,255,0.1)'}`,
      borderRadius: 8,
      padding: compact ? '8px' : '12px',
      position: 'relative',
      opacity: item.is_broken ? 0.5 : 1,
    }}>
      {/* Status badges */}
      {item.is_equipped && (
        <span style={{
          position: 'absolute', top: 4, right: 4,
          fontSize: 10, background: accent, color: '#fff',
          padding: '1px 5px', borderRadius: 4,
        }}>EQUIPPED</span>
      )}
      {item.is_broken && (
        <span style={{
          position: 'absolute', top: 4, left: 4,
          fontSize: 10, background: '#e74c3c', color: '#fff',
          padding: '1px 5px', borderRadius: 4,
        }}>BROKEN</span>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: compact ? 4 : 8 }}>
        <span style={{ fontSize: compact ? 20 : 28 }}>{icon}</span>
        <div>
          <div style={{ fontWeight: 600, fontSize: compact ? 13 : 14, color: accent }}>{item.name}</div>
          <div style={{ fontSize: 11, color: '#999', textTransform: 'capitalize' }}>{item.type} · {item.color}</div>
        </div>
      </div>

      {!compact && (
        <div style={{ fontSize: 12, color: '#ccc', marginBottom: 8 }}>
          {item.armor_value > 0 && <div>Armor: <strong>{item.armor_value}</strong></div>}
          <div>+{item.bonus_value} {item.bonus_stat.replace('_', ' ')}</div>
          {item.enchant_level > 0 && <div style={{ color: '#9b59b6' }}>Enchant +{item.enchant_level}</div>}
        </div>
      )}

      {!compact && !item.is_broken && (
        <div style={{ display: 'flex', gap: 6 }}>
          {item.is_equipped ? (
            onUnequip && (
              <button onClick={() => onUnequip(item)} style={btnStyle('#555')}>Unequip</button>
            )
          ) : (
            onEquip && (
              <button onClick={() => onEquip(item)} style={btnStyle(accent)}>Equip</button>
            )
          )}
          {!item.is_equipped && onList && (
            <button onClick={() => onList(item)} style={btnStyle('#7f8c8d')}>Sell</button>
          )}
        </div>
      )}
    </div>
  )
}

function btnStyle(bg: string): React.CSSProperties {
  return {
    flex: 1,
    padding: '5px 0',
    background: bg,
    color: '#fff',
    border: 'none',
    borderRadius: 5,
    fontSize: 12,
    cursor: 'pointer',
    fontWeight: 600,
  }
}
