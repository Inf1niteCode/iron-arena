// Iron Arena — Inventory Page
// Created by: engineering-frontend-developer
// Purpose: Drag-and-drop inventory with equipment slots and item management.
// Uses HTML5 drag-and-drop API for mobile-compatible item equipping.

import React, { useEffect, useState, useCallback } from 'react'
import { inventoryApi } from '@/api/client'
import type { Item, EquippedSlots } from '@/types'
import { ItemCard } from '@/components/ItemCard'

interface InventoryState {
  items: Item[]
  equipped: EquippedSlots
  loading: boolean
  error: string | null
}

const EQUIPMENT_SLOTS = [
  { key: 'head', label: 'Head', icon: '⛑' },
  { key: 'chest', label: 'Chest', icon: '🛡' },
  { key: 'waist', label: 'Waist', icon: '🦺' },
  { key: 'legs', label: 'Legs', icon: '👟' },
]

export const InventoryPage: React.FC = () => {
  const [state, setState] = useState<InventoryState>({
    items: [],
    equipped: {
      head: null, chest: null, waist: null, legs: null,
      crystal_1: null, crystal_2: null, crystal_3: null, crystal_4: null,
      crystal_5: null, crystal_6: null, crystal_7: null, crystal_8: null,
    },
    loading: true,
    error: null,
  })
  const [dragging, setDragging] = useState<number | null>(null)
  const [actionMsg, setActionMsg] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const data = await inventoryApi.get()
      setState(prev => ({ ...prev, items: data.items, equipped: data.equipped, loading: false }))
    } catch (e) {
      setState(prev => ({ ...prev, loading: false, error: 'Failed to load inventory' }))
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleEquip = async (item: Item) => {
    try {
      await inventoryApi.equip(item.id)
      showMsg(`Equipped ${item.name}`)
      await load()
    } catch (e: unknown) {
      const err = e as { code?: string }
      showMsg(err?.code === 'item_broken' ? 'Item is broken!' : 'Cannot equip')
    }
  }

  const handleUnequip = async (item: Item) => {
    try {
      await inventoryApi.unequip(item.id)
      showMsg(`Unequipped ${item.name}`)
      await load()
    } catch {
      showMsg('Cannot unequip')
    }
  }

  function showMsg(msg: string) {
    setActionMsg(msg)
    setTimeout(() => setActionMsg(null), 2500)
  }

  // Drag & Drop handlers
  const onDragStart = (itemId: number) => setDragging(itemId)
  const onDragEnd = () => setDragging(null)
  const onDrop = (slotKey: string) => {
    if (!dragging) return
    const item = state.items.find(i => i.id === dragging)
    if (item && !item.is_equipped) {
      handleEquip(item)
    }
    setDragging(null)
  }

  if (state.loading) return <div style={centeredStyle}>Loading...</div>
  if (state.error) return <div style={{ ...centeredStyle, color: '#e74c3c' }}>{state.error}</div>

  const unequippedItems = state.items.filter(i => !i.is_equipped)
  const crystals = state.items.filter(i => i.is_equipped && i.type === 'crystal')

  return (
    <div style={pageStyle}>
      {/* Toast */}
      {actionMsg && (
        <div style={toastStyle}>{actionMsg}</div>
      )}

      <div style={{ padding: '16px 16px 0', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: 12 }}>
        <h1 style={{ fontSize: 18, fontWeight: 700 }}>Inventory</h1>
        <p style={{ fontSize: 12, color: '#888', marginTop: 4 }}>Drag items to equipment slots or tap to equip</p>
      </div>

      <div style={{ padding: 16, paddingBottom: 80 }}>
        {/* Armor Equipment Slots */}
        <section style={{ marginBottom: 16 }}>
          <h2 style={sectionTitle}>Armor Slots</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {EQUIPMENT_SLOTS.map(slot => {
              const itemId = state.equipped[slot.key as keyof EquippedSlots]
              const item = itemId ? state.items.find(i => i.id === itemId) : null
              return (
                <div
                  key={slot.key}
                  onDragOver={e => e.preventDefault()}
                  onDrop={() => onDrop(slot.key)}
                  style={{
                    background: dragging ? 'rgba(231,76,60,0.1)' : 'rgba(255,255,255,0.04)',
                    border: '2px dashed rgba(255,255,255,0.15)',
                    borderRadius: 10,
                    padding: 10,
                    minHeight: 80,
                    transition: 'background 0.2s',
                  }}
                >
                  <div style={{ fontSize: 11, color: '#888', marginBottom: 6 }}>
                    {slot.icon} {slot.label}
                  </div>
                  {item ? (
                    <ItemCard item={item} onUnequip={handleUnequip} compact />
                  ) : (
                    <div style={{ color: '#555', fontSize: 11, textAlign: 'center', paddingTop: 10 }}>Empty</div>
                  )}
                </div>
              )
            })}
          </div>
        </section>

        {/* Crystal Slots */}
        <section style={{ marginBottom: 16 }}>
          <h2 style={sectionTitle}>Crystal Slots ({crystals.length}/8)</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 6 }}>
            {Array.from({ length: 8 }, (_, i) => {
              const key = `crystal_${i + 1}` as keyof EquippedSlots
              const itemId = state.equipped[key]
              const item = itemId ? state.items.find(it => it.id === itemId) : null
              return (
                <div
                  key={i}
                  onDragOver={e => e.preventDefault()}
                  onDrop={() => onDrop(key)}
                  style={{
                    background: 'rgba(255,255,255,0.04)',
                    border: '1px dashed rgba(255,255,255,0.1)',
                    borderRadius: 8,
                    padding: 6,
                    minHeight: 52,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {item ? (
                    <div onClick={() => handleUnequip(item)} style={{ cursor: 'pointer', textAlign: 'center' }}>
                      <div style={{ fontSize: 18 }}>💎</div>
                      <div style={{ fontSize: 9, color: '#9b59b6' }}>+{item.bonus_value}</div>
                    </div>
                  ) : (
                    <div style={{ fontSize: 20, opacity: 0.2 }}>💎</div>
                  )}
                </div>
              )
            })}
          </div>
        </section>

        {/* Unequipped Items */}
        <section>
          <h2 style={sectionTitle}>Bag ({unequippedItems.length} items)</h2>
          {unequippedItems.length === 0 ? (
            <div style={{ color: '#555', textAlign: 'center', padding: '20px 0', fontSize: 14 }}>
              No items in bag
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {unequippedItems.map(item => (
                <div
                  key={item.id}
                  draggable
                  onDragStart={() => onDragStart(item.id)}
                  onDragEnd={onDragEnd}
                  style={{ opacity: dragging === item.id ? 0.5 : 1, transition: 'opacity 0.2s' }}
                >
                  <ItemCard item={item} onEquip={handleEquip} />
                </div>
              ))}
            </div>
          )}
        </section>
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

const sectionTitle: React.CSSProperties = {
  fontSize: 12,
  fontWeight: 600,
  color: '#888',
  textTransform: 'uppercase',
  letterSpacing: 1,
  marginBottom: 10,
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
  whiteSpace: 'nowrap',
}
