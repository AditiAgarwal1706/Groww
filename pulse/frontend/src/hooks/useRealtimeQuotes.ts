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
  timestamp: string | number
  data_status: string
}

export type QuoteMap = Record<string, LiveQuote>

interface UseRealtimeQuotesOptions {
  watchlistId?: number | null
  symbols?: string[]
  token: string | null | undefined
  enabled?: boolean
}

interface UseRealtimeQuotesResult {
  quotes: QuoteMap
  isConnected: boolean
  lastUpdated: Date | null
  tickCount: number
  marketStatus: string
  sendPing: () => void
  subscribeSymbols: (symbols: string[]) => void
}

const RECONNECT_DELAY_MS = 2000
const MAX_RECONNECT_ATTEMPTS = 10

export function useRealtimeQuotes({
  watchlistId,
  symbols,
  token,
  enabled = true,
}: UseRealtimeQuotesOptions): UseRealtimeQuotesResult {
  const [quotes, setQuotes] = useState<QuoteMap>({})
  const [isConnected, setIsConnected] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [tickCount, setTickCount] = useState(0)
  const [marketStatus, setMarketStatus] = useState<string>('UNKNOWN')

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttempts = useRef(0)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isMounted = useRef(true)

  const sendPing = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'ping' }))
    }
  }, [])

  const subscribeSymbols = useCallback((syms: string[]) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'subscribe', symbols: syms }))
    }
  }, [])

  const connect = useCallback(() => {
    if (!token || !enabled || !isMounted.current) return
    if (!watchlistId && (!symbols || symbols.length === 0)) return

    if (wsRef.current) {
      wsRef.current.onclose = null
      wsRef.current.close()
    }

    let url = `${WS_BASE}/ws/quotes?token=${encodeURIComponent(token)}`
    if (watchlistId) {
      url += `&watchlist_id=${watchlistId}`
    }

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      if (!isMounted.current) return
      setIsConnected(true)
      reconnectAttempts.current = 0

      if (symbols && symbols.length > 0) {
        ws.send(JSON.stringify({ action: 'subscribe', symbols }))
      }
    }

    ws.onmessage = (event) => {
      if (!isMounted.current) return
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'quotes' && msg.data) {
          setQuotes(prev => ({ ...prev, ...msg.data }))
          setLastUpdated(new Date())
          setTickCount(c => c + 1)
          if (msg.market_status) setMarketStatus(msg.market_status)
        }
      } catch {
        // Ignore JSON parse error
      }
    }

    ws.onerror = () => {
      if (isMounted.current) setIsConnected(false)
    }

    ws.onclose = () => {
      if (!isMounted.current) return
      setIsConnected(false)

      if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = Math.min(
          RECONNECT_DELAY_MS * Math.pow(1.3, reconnectAttempts.current),
          15_000,
        )
        reconnectAttempts.current++
        reconnectTimer.current = setTimeout(() => {
          if (isMounted.current) connect()
        }, delay)
      }
    }
  }, [watchlistId, symbols, token, enabled])

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

  return { quotes, isConnected, lastUpdated, tickCount, sendPing, subscribeSymbols, marketStatus }
}

