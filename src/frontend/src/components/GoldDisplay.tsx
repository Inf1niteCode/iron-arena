// Iron Arena — Gold Display Component
// Created by: design-ui-designer
// Purpose: Shows gold amount with coin icon, used across all screens

import React from 'react'

interface GoldDisplayProps {
  amount: number
  size?: 'sm' | 'md' | 'lg'
}

const SIZE_STYLES = {
  sm: { fontSize: 13, iconSize: 14 },
  md: { fontSize: 16, iconSize: 18 },
  lg: { fontSize: 22, iconSize: 24 },
}

export const GoldDisplay: React.FC<GoldDisplayProps> = ({ amount, size = 'md' }) => {
  const { fontSize, iconSize } = SIZE_STYLES[size]
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: '#f1c40f' }}>
      <span style={{ fontSize: iconSize }}>&#9734;</span>
      <span style={{ fontSize, fontWeight: 600 }}>{amount.toLocaleString()}</span>
    </span>
  )
}
