import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { watchlistApi } from '../api/watchlists'
import { stocksApi, type Stock } from '../api/stocks'
import { changesApi } from '../api/changes'
import { Plus, Trash2, Search, X, CheckCircle } from 'lucide-react'

export function WatchlistPage() {
  const queryClient = useQueryClient()
  const [searchQ, setSearchQ] = useState('')
  const [searchResults, setSearchResults] = useState<Stock[]>([])
  const [activeWatchlistId, setActiveWatchlistId] = useState<number | null>(null)

  const { data: watchlists = [], isLoading } = useQuery({
    queryKey: ['watchlists'],
    queryFn: watchlistApi.list,
  })

  const createMutation = useMutation({
    mutationFn: () => watchlistApi.create('New Watchlist'),
    onSuccess: (wl) => {
      queryClient.invalidateQueries({ queryKey: ['watchlists'] })
      setActiveWatchlistId(wl.id)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => watchlistApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['watchlists'] }),
  })

  const addStockMutation = useMutation({
    mutationFn: ({ id, symbol }: { id: number; symbol: string }) => watchlistApi.addStock(id, symbol),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlists'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  const removeStockMutation = useMutation({
    mutationFn: ({ id, symbol }: { id: number; symbol: string }) => watchlistApi.removeStock(id, symbol),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlists'] })
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

  const { data: activeWatchlist } = useQuery({
    queryKey: ['watchlist', activeWatchlistId],
    queryFn: () => activeWatchlistId ? watchlistApi.get(activeWatchlistId) : null,
    enabled: !!activeWatchlistId,
  })

  const firstWl = watchlists[0]
  const displayWl = activeWatchlistId ? activeWatchlist : firstWl

  if (isLoading) {
    return <div className="skeleton" style={{ height: '300px', borderRadius: '16px' }} />
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 style={{ marginBottom: '0.25rem' }}>Watchlists</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Manage your market watchlists and stocks</p>
        </div>
        <button className="btn btn-primary" onClick={() => createMutation.mutate()} id="create-watchlist-btn">
          <Plus size={14} /> New Watchlist
        </button>
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
                    {checkpointMutation.isPending ? 'Saving...' : 'Checkpoint'}
                  </button>
                </div>

                {/* Search to add stocks */}
                <div style={{ position: 'relative', marginBottom: '1rem' }}>
                  <Search size={14} style={{
                    position: 'absolute', left: '0.875rem', top: '50%',
                    transform: 'translateY(-50%)', color: 'var(--text-muted)',
                  }} />
                  <input
                    id="stock-search-input"
                    className="input"
                    style={{ paddingLeft: '2.5rem' }}
                    placeholder="Search stocks to add (e.g. NVDA, Apple)"
                    value={searchQ}
                    onChange={e => handleSearch(e.target.value)}
                  />
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
                          onClick={() => {
                            addStockMutation.mutate({ id: displayWl.id, symbol: stock.symbol })
                            setSearchQ('')
                            setSearchResults([])
                          }}
                        >
                          <Plus size={12} /> Add
                        </button>
                      </div>
                    ))}
                    {/* Allow adding any custom ticker directly */}
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
                          onClick={() => {
                            addStockMutation.mutate({ id: displayWl.id, symbol: searchQ.toUpperCase().trim() })
                            setSearchQ('')
                            setSearchResults([])
                          }}
                        >
                          <Plus size={12} /> Add Symbol
                        </button>
                      </div>
                    )}
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
                    {displayWl.stocks.map((ws: any) => (
                      <div key={ws.id} style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        padding: '0.625rem 0.875rem', background: 'rgba(255,255,255,0.03)',
                        borderRadius: 8, border: '1px solid var(--border)',
                      }}>
                        <div>
                          <span style={{ fontWeight: 700 }}>{ws.stock.symbol}</span>
                          <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginLeft: '0.5rem' }}>
                            {ws.stock.company_name}
                          </span>
                        </div>
                        <button
                          className="btn btn-ghost btn-sm"
                          style={{ color: 'var(--severity-major)', opacity: 0.7 }}
                          onClick={() => removeStockMutation.mutate({ id: displayWl.id, symbol: ws.stock.symbol })}
                        >
                          <X size={13} />
                        </button>
                      </div>
                    ))}
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
