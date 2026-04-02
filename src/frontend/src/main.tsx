// Iron Arena — Application Entry Point
// Created by: engineering-frontend-developer
// Purpose: React app root, Telegram WebApp initialization, routing setup

import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { CharacterPage } from '@/pages/CharacterPage'
import { InventoryPage } from '@/pages/InventoryPage'
import { ArenaPage } from '@/pages/ArenaPage'
import { ShopPage } from '@/pages/ShopPage'
import { AuctionPage } from '@/pages/AuctionPage'
import { CreateCharacterPage } from '@/pages/CreateCharacterPage'
import { BottomNav } from '@/components/BottomNav'
import type { Player } from '@/types'

function App() {
  const { player, loading, error, isNew, updatePlayer } = useAuth()

  if (loading) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        height: '100vh', background: '#1a1a2e', color: '#888', fontSize: 16,
      }}>
        Loading Iron Arena...
      </div>
    )
  }

  if (error) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        height: '100vh', background: '#1a1a2e', color: '#e74c3c',
        flexDirection: 'column', gap: 12, padding: 24, textAlign: 'center',
      }}>
        <span style={{ fontSize: 48 }}>⚠</span>
        <p>{error}</p>
        <button
          onClick={() => window.location.reload()}
          style={{ background: '#e74c3c', color: '#fff', border: 'none', borderRadius: 8, padding: '10px 24px', cursor: 'pointer' }}
        >
          Retry
        </button>
      </div>
    )
  }

  // New player: needs to create character
  if (isNew || (player && player.wins === 0 && player.losses === 0 && player.level === 1)) {
    return (
      <CreateCharacterPage
        onCreated={(p: Player) => updatePlayer(p)}
      />
    )
  }

  return (
    <BrowserRouter>
      <div style={{ minWidth: 360, minHeight: '100vh', background: '#1a1a2e' }}>
        <Routes>
          <Route path="/" element={<Navigate to="/character" replace />} />
          <Route path="/character" element={<CharacterPage />} />
          <Route path="/inventory" element={<InventoryPage />} />
          <Route path="/arena" element={<ArenaPage />} />
          <Route path="/shop" element={<ShopPage />} />
          <Route path="/auction" element={<AuctionPage />} />
        </Routes>
        <BottomNav />
      </div>
    </BrowserRouter>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
