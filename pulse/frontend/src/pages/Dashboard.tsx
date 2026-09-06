import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { changesApi, type DashboardResponse } from '../api/changes'
import { MarketBrief } from '../components/dashboard/MarketBrief'
import { AttentionCard } from '../components/dashboard/AttentionCard'
import { WatchlistTable } from '../components/dashboard/WatchlistTable'
import { useAuthStore } from '../stores/authStore'
import { useRealtimeQuotes } from '../hooks/useRealtimeQuotes'
import { RefreshCw, Plus, Radio } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { watchlistApi } from '../api/watchlists'

export function Dashboard() {
  const { user, token } = useAuthStore()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // ALL hooks must be called unconditionally at the top
  const [isRefreshing, setIsRefreshing] = useState(false)

  const { data: dashboard, isLoading, error, refetch } = useQuery<DashboardResponse>({
    queryKey: ['dashboard'],
    queryFn: changesApi.getDashboard,
    refetchInterval: 60_000,
    staleTime: 30_000,
  })

  // Real-time WebSocket quotes — enabled only once we have a watchlist id
  const { quotes: liveQuotes, isConnected, lastUpdated } = useRealtimeQuotes({
    watchlistId: dashboard?.watchlist_id,
    token,
    enabled: !!dashboard?.watchlist_id,
  })

  const checkpointMutation = useMutation({
    mutationFn: async () => {
      if (!dashboard?.watchlist_id) return
      return changesApi.saveCheckpoint(dashboard.watchlist_id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  const createWatchlistMutation = useMutation({
    mutationFn: () => watchlistApi.create('My Portfolio'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      const liveData = await changesApi.getDashboard(true)
      queryClient.setQueryData(['dashboard'], liveData)
    } catch (err) {
      console.error('Failed to sync live data:', err)
      refetch()
    } finally {
      setIsRefreshing(false)
    }
  }

  const greeting = () => {
    const h = new Date().getHours()
    if (h < 12) return 'Good morning'
    if (h < 17) return 'Good afternoon'
    return 'Good evening'
  }

  // ─── Conditional rendering AFTER all hooks ────────────────────
  if (isLoading) {
    return (
      <div>
        <div style={{ marginBottom: '2rem' }}>
          <div className="skeleton" style={{ height: '2rem', width: '200px', marginBottom: '0.5rem' }} />
          <div className="skeleton" style={{ height: '1rem', width: '300px' }} />
        </div>
        <div className="skeleton" style={{ height: '140px', borderRadius: '24px', marginBottom: '2rem' }} />
        <div className="grid-3">
          {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: '160px', borderRadius: '16px' }} />)}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">⚠️</div>
        <h3>Could not load dashboard</h3>
        <p>Check your backend connection</p>
        <button className="btn btn-primary mt-4" onClick={() => refetch()}>
          <RefreshCw size={14} /> Retry
        </button>
      </div>
    )
  }

  if (!dashboard || !dashboard.watchlist_id) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">📋</div>
        <h3>No watchlist yet</h3>
        <p>Create your first watchlist to get started</p>
        <button
          className="btn btn-primary mt-4"
          onClick={() => createWatchlistMutation.mutate()}
          disabled={createWatchlistMutation.isPending}
        >
          <Plus size={14} />
          {createWatchlistMutation.isPending ? 'Creating...' : 'Create Watchlist'}
        </button>
      </div>
    )
  }

  const topChanges = dashboard.top_attention.slice(0, 3)

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 style={{ marginBottom: '0.25rem' }}>
            {greeting()}{user?.name ? `, ${user.name.split(' ')[0]}` : ''}.
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Here's what's moved in your market since you last checked.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {/* Live connection indicator */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: '0.4rem',
            padding: '0.3rem 0.75rem',
            borderRadius: '100px',
            background: isConnected ? 'rgba(16,185,129,0.12)' : 'rgba(255,255,255,0.05)',
            border: `1px solid ${isConnected ? 'rgba(16,185,129,0.3)' : 'rgba(255,255,255,0.08)'}`,
            fontSize: '0.75rem',
            fontWeight: 600,
            color: isConnected ? '#10B981' : 'var(--text-muted)',
            transition: 'all 0.3s',
          }}>
            <Radio size={11} style={{
              animation: isConnected ? 'pulse-live 2s ease-in-out infinite' : 'none',
            }} />
            {isConnected ? (
              <>
                LIVE
                {lastUpdated && (
                  <span style={{ fontWeight: 400, opacity: 0.7, marginLeft: '0.2rem' }}>
                    · {lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </span>
                )}
              </>
            ) : 'Connecting...'}
          </div>

          <button
            className="btn btn-ghost btn-sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw size={14} className={isRefreshing ? 'animate-spin' : ''} />
            {isRefreshing ? 'Syncing Live...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Market Brief */}
      <MarketBrief
        dashboard={dashboard}
        onCheckpoint={() => checkpointMutation.mutate()}
        isCheckpointing={checkpointMutation.isPending}
      />

      {/* Top Attention */}
      {topChanges.length > 0 && (
        <section className="mb-6">
          <h4 className="mb-4">Requires Attention</h4>
          <div className="grid-3">
            {topChanges.map((change, i) => (
              <AttentionCard key={change.symbol} change={change} index={i} />
            ))}
          </div>
        </section>
      )}

      {/* Full Watchlist */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h4>{dashboard.watchlist_name}</h4>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/watchlist')}>
            Manage →
          </button>
        </div>
        {dashboard.watchlist.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📈</div>
            <h3>No stocks in watchlist</h3>
            <p>Go to Watchlist to add stocks</p>
            <button className="btn btn-primary mt-4" onClick={() => navigate('/watchlist')}>
              <Plus size={14} /> Add Stocks
            </button>
          </div>
        ) : (
          <WatchlistTable stocks={dashboard.watchlist} liveQuotes={liveQuotes} />
        )}
      </section>
    </div>
  )
}
