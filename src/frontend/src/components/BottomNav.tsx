// Iron Arena — Bottom Navigation
// Created by: design-ui-designer
// Purpose: Mobile tab bar navigation — always visible at bottom, 360px min-width

import React from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

interface NavItem {
  path: string
  label: string
  icon: string
}

const NAV_ITEMS: NavItem[] = [
  { path: '/character', label: 'Hero', icon: '⚔' },
  { path: '/inventory', label: 'Bag', icon: '🎒' },
  { path: '/arena', label: 'Arena', icon: '🏟' },
  { path: '/shop', label: 'Shop', icon: '🛒' },
  { path: '/auction', label: 'Auction', icon: '🔨' },
]

export const BottomNav: React.FC = () => {
  const location = useLocation()
  const navigate = useNavigate()

  return (
    <nav style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      height: 60,
      background: '#16213e',
      borderTop: '1px solid rgba(255,255,255,0.08)',
      display: 'flex',
      alignItems: 'stretch',
      zIndex: 100,
    }}>
      {NAV_ITEMS.map(item => {
        const active = location.pathname.startsWith(item.path)
        return (
          <button
            key={item.path}
            onClick={() => navigate(item.path)}
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 2,
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: active ? '#e74c3c' : '#888',
              transition: 'color 0.2s',
            }}
          >
            <span style={{ fontSize: 20 }}>{item.icon}</span>
            <span style={{ fontSize: 10, fontWeight: active ? 700 : 400 }}>{item.label}</span>
          </button>
        )
      })}
    </nav>
  )
}
