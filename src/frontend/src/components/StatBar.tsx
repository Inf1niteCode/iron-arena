// Iron Arena — StatBar Component
// Created by: design-ui-designer
// Purpose: Visual progress bar for HP and Stamina, mobile-optimized

import React from 'react'

interface StatBarProps {
  current: number
  max: number
  color: 'red' | 'green' | 'blue' | 'yellow'
  label: string
  showNumbers?: boolean
}

const COLOR_MAP: Record<string, string> = {
  red: '#e74c3c',
  green: '#2ecc71',
  blue: '#3498db',
  yellow: '#f39c12',
}

export const StatBar: React.FC<StatBarProps> = ({ current, max, color, label, showNumbers = true }) => {
  const pct = max > 0 ? Math.max(0, Math.min(100, (current / max) * 100)) : 0
  const barColor = COLOR_MAP[color] ?? '#888'

  return (
    <div style={{ marginBottom: 6 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 3, color: '#ccc' }}>
        <span>{label}</span>
        {showNumbers && <span>{current} / {max}</span>}
      </div>
      <div style={{
        height: 10,
        background: 'rgba(255,255,255,0.1)',
        borderRadius: 5,
        overflow: 'hidden',
      }}>
        <div style={{
          width: `${pct}%`,
          height: '100%',
          background: barColor,
          borderRadius: 5,
          transition: 'width 0.3s ease',
        }} />
      </div>
    </div>
  )
}
