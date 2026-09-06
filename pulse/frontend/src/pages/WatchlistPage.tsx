import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { watchlistApi } from '../api/watchlists'
import { stocksApi, type Stock } from '../api/stocks'
import { changesApi } from '../api/changes'
import { useAuthStore } from '../stores/authStore'
import { useRealtimeQuotes } from '../hooks/useRealtimeQuotes'
import { Plus, Trash2, Search, X, CheckCircle, Radio, TrendingUp, TrendingDown, Minus } from 'lucide-react'

import { formatPrice, formatChangePct } from '../utils/format'

function StockPriceFlash({ symbol, price, changePct }: { symbol: string; price: number; changePct?: number | null }) {
  const changeClass = changePct == null ? 'neutral' : changePct >= 0 ? 'positive' : 'negative'
  const Icon = changePct == null ? Minus : changePct >= 0 ? TrendingUp : TrendingDown

  return (
    <div style={{ textAlign: 'right' }}>
      <div style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '0.9375rem' }}>
        {formatPrice(price, symbol)}
      </div>
      <div className={changeClass} style={{ fontSize: '0.75rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
        <Icon size={11} />
        {formatChangePct(changePct)}
      </div>
    </div>
  )
}


export function WatchlistPage() {
  const queryClient = useQueryClient()
  const { token } = useAuthStore()
  const [searchQ, setSearchQ] = useState('')
  const [searchResults, setSearchResults] = useState<Stock[]>([])
  const [activeWatchlistId, setActiveWatchlistId] = useState<number | null>(null)
  const [addMsg, setAddMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const { data: watchlists = [], isLoading } = useQuery({
    queryKey: ['watchlists'],
    queryFn: watchlistApi.list,
  })

  const firstWl = watchlists[0]
  const effectiveWlId = activeWatchlistId ?? firstWl?.id

  const { data: activeWatchlist } = useQuery({
    queryKey: ['watchlist', effectiveWlId],
    queryFn: () => (effectiveWlId ? watchlistApi.get(effectiveWlId) : null),
    enabled: !!effectiveWlId,
  })

  const displayWl = activeWatchlist

  const createMutation = useMutation({
    mutationFn: (name: string = 'My Watchlist') => watchlistApi.create(name),
    onSuccess: (wl) => {
      queryClient.invalidateQueries({ queryKey: ['watchlists'] })
      setActiveWatchlistId(wl.id)
    },
  })

  // Auto-create default watchlist if user has none
  useEffect(() => {
    if (!isLoading && watchlists.length === 0 && !createMutation.isPending) {
      createMutation.mutate('My Watchlist')
    }
  }, [isLoading, watchlists.length])

  const deleteMutation = useMutation({
    mutationFn: (id: number) => watchlistApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['watchlists'] }),
  })

  const addStockMutation = useMutation({
    mutationFn: ({ id, symbol }: { id: number; symbol: string }) => watchlistApi.addStock(id, symbol),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['watchlists'] })
      queryClient.invalidateQueries({ queryKey: ['watchlist', variables.id] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      setSearchQ('')
      setSearchResults([])
      setAddMsg({ type: 'success', text: `✅ ${variables.symbol} added to watchlist` })
      setTimeout(() => setAddMsg(null), 3000)
    },
    onError: (error: any, variables) => {
      const status = error?.response?.status
      const detail = error?.response?.data?.detail
      if (status === 409) {
        setAddMsg({ type: 'error', text: `⚠️ ${variables.symbol} is already in your watchlist` })
      } else if (status === 422) {
        setAddMsg({ type: 'error', text: `❌ Invalid symbol: ${variables.symbol}` })
      } else if (status === 503) {
        setAddMsg({ type: 'error', text: `❌ Market data unavailable for ${variables.symbol} — check the symbol is correct` })
      } else {
        setAddMsg({ type: 'error', text: detail || `❌ Failed to add ${variables.symbol}` })
      }
      setTimeout(() => setAddMsg(null), 5000)
    },
  })

  const removeStockMutation = useMutation({
    mutationFn: ({ id, symbol }: { id: number; symbol: string }) => watchlistApi.removeStock(id, symbol),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['watchlists'] })
      queryClient.invalidateQueries({ queryKey: ['watchlist', variables.id] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  const checkpointMutation = useMutation({
    mutationFn: (id: number) => changesApi.saveCheckpoint(id),
  })

  const handleSearch = async (q: string) => {
    setSearchQ(q)
    if (q.length < 1) { setSearchResults([]); return }
    try {
      const results = await stocksApi.search(q)
      setSearchResults(results)
    } catch { setSearchResults([]) }
  }

  // Connect Realtime Quotes for active Watchlist
  const { quotes: liveQuotes, isConnected, marketStatus } = useRealtimeQuotes({
    watchlistId: effectiveWlId,
    token,
    enabled: !!effectiveWlId,
  })


  const marketBannerClass =
    marketStatus === 'PRE_MARKET' ? 'premarket'
    : marketStatus === 'AFTER_HOURS' ? 'afterhours'
    : 'closed'
  const marketBannerText =
    marketStatus === 'PRE_MARKET' ? '🕘 Pre-market session — prices from last pre-market data'
    : marketStatus === 'AFTER_HOURS' ? '🌙 After-hours session — showing extended-hours data'
    : marketStatus === 'LIVE' ? null
    : '📴 Markets are closed — showing last known closing prices (real data, no simulation)'

  if (isLoading) {
    return <div className="skeleton" style={{ height: '300px', borderRadius: '16px' }} />
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 style={{ marginBottom: '0.25rem' }}>Watchlists</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Manage your market watchlists and real-time stocks</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '0.4rem',
            padding: '0.3rem 0.75rem', borderRadius: '100px',
            background: isConnected ? 'rgba(16,185,129,0.12)' : 'rgba(255,255,255,0.05)',
            border: `1px solid ${isConnected ? 'rgba(16,185,129,0.3)' : 'rgba(255,255,255,0.08)'}`,
            fontSize: '0.75rem', fontWeight: 600,
            color: isConnected ? '#10B981' : 'var(--text-muted)',
          }}>
            <Radio size={11} style={{ animation: isConnected ? 'pulse-live 2s ease-in-out infinite' : 'none' }} />
            {isConnected ? 'LIVE FEED' : 'Connecting...'}
          </div>
          <button className="btn btn-primary" onClick={() => createMutation.mutate()} id="create-watchlist-btn">
            <Plus size={14} /> New Watchlist
          </button>
        </div>
      </div>

      <div className="grid-2" style={{ alignItems: 'flex-start' }}>
        {/* Watchlist List */}
        <div className="card">
          <h4 className="mb-4">Your Watchlists</h4>
          {watchlists.length === 0 ? (
            <div className="empty-state" style={{ padding: '2rem' }}>
              <div className="empty-state-icon" style={{ fontSize: '2rem' }}>📋</div>
              <p>No watchlists yet. Create one!</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {watchlists.map(wl => (
                <div key={wl.id}
                  onClick={() => setActiveWatchlistId(wl.id)}
                  style={{
                    padding: '0.875rem', borderRadius: '10px', cursor: 'pointer',
                    border: `1px solid ${activeWatchlistId === wl.id || (!activeWatchlistId && wl.id === firstWl?.id) ? 'rgba(124,58,237,0.4)' : 'var(--border)'}`,
                    background: activeWatchlistId === wl.id || (!activeWatchlistId && wl.id === firstWl?.id) ? 'rgba(124,58,237,0.08)' : 'rgba(255,255,255,0.03)',
                    transition: 'all 0.15s',
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div style={{ fontWeight: 600 }}>{wl.name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {wl.stock_count} stocks
                      </div>
                    </div>
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={e => { e.stopPropagation(); deleteMutation.mutate(wl.id) }}
                      style={{ opacity: 0.5 }}
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Watchlist Detail */}
        <div>
          {displayWl ? (
            <>
              <div className="card mb-4">
                <div className="flex items-center justify-between mb-4">
                  <h4 style={{ margin: 0 }}>{displayWl.name}</h4>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => checkpointMutation.mutate(displayWl.id)}
                    disabled={checkpointMutation.isPending}
                  >
                    <CheckCircle size={13} />
                    {checkpointMutation.isPending ? 'Saving...' : 'Save Checkpoint'}
                  </button>
                </div>

                {/* Search to add stocks */}
                <div style={{ position: 'relative', marginBottom: '0.5rem' }}>
                  <Search size={14} style={{
                    position: 'absolute', left: '0.875rem', top: '50%',
                    transform: 'translateY(-50%)', color: 'var(--text-muted)',
                  }} />
                  <input
                    id="stock-search-input"
                    className="input"
                    style={{ paddingLeft: '2.5rem' }}
                    placeholder="Search stocks (e.g. RELIANCE.NS, TCS.NS, NVDA)"
                    value={searchQ}
                    onChange={e => handleSearch(e.target.value)}
                  />
                </div>

                {/* Feedback message */}
                {addMsg && (
                  <div style={{
                    padding: '0.625rem 1rem',
                    borderRadius: 8,
                    marginBottom: '0.75rem',
                    fontSize: '0.875rem',
                    fontWeight: 500,
                    background: addMsg.type === 'success'
                      ? 'rgba(16,185,129,0.1)'
                      : 'rgba(239,68,68,0.1)',
                    border: `1px solid ${
                      addMsg.type === 'success'
                        ? 'rgba(16,185,129,0.3)'
                        : 'rgba(239,68,68,0.3)'
                    }`,
                    color: addMsg.type === 'success' ? '#10B981' : '#EF4444',
                  }}>
                    {addMsg.text}
                  </div>
                )}

                {/* Popular Indian Quick Add Chips */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>🇮🇳 Quick Add:</span>
                  {[
                    { symbol: 'RELIANCE.NS', label: 'Reliance' },
                    { symbol: 'TCS.NS', label: 'TCS' },
                    { symbol: 'INFY.NS', label: 'Infosys' },
                    { symbol: 'HDFCBANK.NS', label: 'HDFC Bank' },
                    { symbol: 'MARUTI.NS', label: 'Maruti' },
                    { symbol: 'ICICIBANK.NS', label: 'ICICI Bank' },
                    { symbol: 'SBIN.NS', label: 'SBI' },
                    { symbol: 'BAJFINANCE.NS', label: 'Bajaj Finance' },
                  ].map(item => (
                    <button
                      key={item.symbol}
                      className="btn btn-ghost btn-sm"
                      style={{ fontSize: '0.7rem', padding: '0.15rem 0.5rem', background: 'rgba(124,58,237,0.08)', borderRadius: '100px', border: '1px solid rgba(124,58,237,0.2)' }}
                      onClick={() => displayWl && addStockMutation.mutate({ id: displayWl.id, symbol: item.symbol })}
                    >
                      + {item.label}
                    </button>
                  ))}
                </div>


                {/* Search results */}
                {searchQ.trim().length > 0 && (
                  <div style={{
                    border: '1px solid var(--border)', borderRadius: 10,
                    overflow: 'hidden', marginBottom: '1rem',
                  }}>
                    {searchResults.map(stock => (
                      <div key={stock.id}
                        style={{
                          padding: '0.625rem 1rem',
                          borderBottom: '1px solid var(--border)',
                          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        }}
                      >
                        <div>
                          <span style={{ fontWeight: 700, marginRight: '0.5rem' }}>{stock.symbol}</span>
                          <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>{stock.company_name}</span>
                        </div>
                        <button
                          className="btn btn-primary btn-sm"
                          disabled={addStockMutation.isPending}
                          onClick={() =>
                            addStockMutation.mutate({ id: displayWl.id, symbol: stock.symbol })
                          }
                        >
                          <Plus size={12} /> {addStockMutation.isPending ? 'Adding...' : 'Add'}
                        </button>
                      </div>
                    ))}
                    {!searchResults.some(s => s.symbol === searchQ.toUpperCase().trim()) && (
                      <div
                        style={{
                          padding: '0.625rem 1rem',
                          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                          background: 'rgba(124,58,237,0.06)',
                        }}
                      >
                        <div>
                          <span style={{ fontWeight: 700, color: 'var(--accent-violet)', marginRight: '0.5rem' }}>
                            Add "{searchQ.toUpperCase().trim()}"
                          </span>
                          <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                            Fetch live real-world data from market
                          </span>
                        </div>
                        <button
                          className="btn btn-primary btn-sm"
                          disabled={addStockMutation.isPending}
                          onClick={() =>
                            addStockMutation.mutate({ id: displayWl.id, symbol: searchQ.toUpperCase().trim() })
                          }
                        >
                          <Plus size={12} /> {addStockMutation.isPending ? 'Adding...' : 'Add Symbol'}
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Market status banner */}
                {marketBannerText && (
                  <div className={`market-status-banner ${marketBannerClass}`}>
                    <span>{marketBannerText}</span>
                  </div>
                )}

                {/* Stocks list */}
                <h4 className="mb-3">Stocks in this watchlist</h4>
                {(!displayWl.stocks || displayWl.stocks.length === 0) ? (
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                    Search above to add stocks
                  </p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {displayWl.stocks.map((ws: any) => {
                      const live = liveQuotes[ws.stock.symbol]
                      const price = live?.price ?? ws.stock.price ?? 150.0
                      const changePct = live?.change_pct ?? ws.stock.change_pct

                      return (
                        <div key={ws.id} style={{
                          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                          padding: '0.75rem 0.875rem', background: 'rgba(255,255,255,0.03)',
                          borderRadius: 10, border: '1px solid var(--border)',
                        }}>
                          <div>
                            <span style={{ fontWeight: 700, fontSize: '0.9375rem' }}>{ws.stock.symbol}</span>
                            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginLeft: '0.5rem' }}>
                              {ws.stock.company_name}
                            </span>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                        <StockPriceFlash symbol={ws.stock.symbol} price={price} changePct={changePct} />
                            <button
                              className="btn btn-ghost btn-sm"
                              style={{ color: 'var(--severity-major)', opacity: 0.7 }}
                              onClick={() => removeStockMutation.mutate({ id: displayWl.id, symbol: ws.stock.symbol })}
                            >
                              <X size={13} />
                            </button>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="empty-state card">
              <div className="empty-state-icon" style={{ fontSize: '2rem' }}>👈</div>
              <p>Select or create a watchlist</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

