import { useEffect, useRef, useState, useCallback } from 'react'

const WS_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000')
  .replace(/^http/, 'ws')

export interface LiveQuote {
  symbol: string
  price: number
  change_pct: number | null
  volume: number | null
  open: number | null
  high: number | null
  low: number | null
  previous_close: number | null
  timestamp: string
  data_status: string
}

type QuoteMap = Record<string, LiveQuote>

interface UseRealtimeQuotesOptions {
  watchlistId: number | null | undefined
  token: string | null | undefined
  enabled?: boolean
}

interface UseRealtimeQuotesResult {
  quotes: QuoteMap
  isConnected: boolean
  lastUpdated: Date | null
}

const RECONNECT_DELAY_MS = 3000
const MAX_RECONNECT_ATTEMPTS = 10

export function useRealtimeQuotes({
  watchlistId,
  token,
  enabled = true,
}: UseRealtimeQuotesOptions): UseRealtimeQuotesResult {
  const [quotes, setQuotes] = useState<QuoteMap>({})
  const [isConnected, setIsConnected] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttempts = useRef(0)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isMounted = useRef(true)

  const connect = useCallback(() => {
    if (!watchlistId || !token || !enabled || !isMounted.current) return

    // Close existing connection
    if (wsRef.current) {
      wsRef.current.onclose = null // prevent reconnect from old close
      wsRef.current.close()
    }

    const url = `${WS_BASE}/ws/quotes?token=${encodeURIComponent(token)}&watchlist_id=${watchlistId}`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      if (!isMounted.current) return
      setIsConnected(true)
      reconnectAttempts.current = 0
    }

    ws.onmessage = (event) => {
      if (!isMounted.current) return
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'quotes' && msg.data) {
          setQuotes(prev => ({ ...prev, ...msg.data }))
          setLastUpdated(new Date())
        }
      } catch {
        // Ignore parse errors
      }
    }

    ws.onerror = () => {
      setIsConnected(false)
    }

    ws.onclose = () => {
      if (!isMounted.current) return
      setIsConnected(false)

      // Exponential back-off reconnect
      if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = Math.min(
          RECONNECT_DELAY_MS * Math.pow(1.5, reconnectAttempts.current),
          30_000,
        )
        reconnectAttempts.current++
        reconnectTimer.current = setTimeout(() => {
          if (isMounted.current) connect()
        }, delay)
      }
    }
  }, [watchlistId, token, enabled])

  useEffect(() => {
    isMounted.current = true
    connect()
    return () => {
      isMounted.current = false
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
      }
    }
  }, [connect])

  return { quotes, isConnected, lastUpdated }
}
