import { formatDistanceToNow, parseISO } from 'date-fns'
import { type DashboardResponse } from '../../api/changes'
import { Clock, CheckCircle } from 'lucide-react'

interface Props {
  dashboard: DashboardResponse
  onCheckpoint: () => void
  isCheckpointing: boolean
}

export function MarketBrief({ dashboard, onCheckpoint, isCheckpointing }: Props) {
  const { last_checked_at, summary, watchlist_name } = dashboard
  const lastChecked = last_checked_at
    ? formatDistanceToNow(parseISO(last_checked_at), { addSuffix: true })
    : 'Never'

  const hasChanges = summary.major + summary.important + summary.watch > 0

  return (
    <div className="market-brief animate-fadeInUp">
      <div className="flex items-center justify-between" style={{ flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <Clock size={14} style={{ color: 'var(--text-muted)' }} />
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Last checked {lastChecked}
            </span>
          </div>
          {hasChanges ? (
            <h2 style={{ fontWeight: 800, fontSize: '1.75rem', letterSpacing: '-0.03em', marginBottom: '0.25rem' }}>
              {summary.major + summary.important} meaningful changes
              <span style={{ color: 'var(--text-secondary)', fontWeight: 400 }}> since your last visit</span>
            </h2>
          ) : (
            <h2 style={{ fontWeight: 800, fontSize: '1.75rem', letterSpacing: '-0.03em', marginBottom: '0.25rem' }}>
              ✓ Nothing important changed
            </h2>
          )}
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            {watchlist_name || 'My Watchlist'} · {summary.total} stocks monitored
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            {summary.major > 0 && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--severity-major)' }}>{summary.major}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Major</div>
              </div>
            )}
            {summary.important > 0 && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--severity-important)' }}>{summary.important}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Important</div>
              </div>
            )}
            {summary.watch > 0 && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#A78BFA' }}>{summary.watch}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Watch</div>
              </div>
            )}
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-muted)' }}>{summary.normal}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Normal</div>
            </div>
          </div>
          <button
            className="btn btn-secondary btn-sm"
            onClick={onCheckpoint}
            disabled={isCheckpointing}
            id="save-checkpoint-btn"
            style={{ marginTop: '0.25rem' }}
          >
            <CheckCircle size={14} />
            {isCheckpointing ? 'Saving...' : 'Save Checkpoint'}
          </button>
        </div>
      </div>
    </div>
  )
}
