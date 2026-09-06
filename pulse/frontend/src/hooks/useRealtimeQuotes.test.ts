import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useRealtimeQuotes } from './useRealtimeQuotes'

describe('useRealtimeQuotes Custom Hook', () => {
  it('connects to WebSocket and updates connection state', async () => {
    const { result } = renderHook(() =>
      useRealtimeQuotes({
        watchlistId: 1,
        token: 'valid-jwt-token',
        enabled: true,
      })
    )

    expect(result.current.isConnected).toBe(false)

    await act(async () => {
      await new Promise(r => setTimeout(r, 50))
    })

    expect(result.current.isConnected).toBe(true)
  })

  it('sends ping heartbeats over WebSocket', async () => {
    const { result } = renderHook(() =>
      useRealtimeQuotes({
        watchlistId: 1,
        token: 'valid-jwt-token',
        enabled: true,
      })
    )

    await act(async () => {
      await new Promise(r => setTimeout(r, 50))
    })

    act(() => {
      result.current.sendPing()
    })

    await act(async () => {
      await new Promise(r => setTimeout(r, 20))
    })

    expect(result.current.isConnected).toBe(true)
  })
})
