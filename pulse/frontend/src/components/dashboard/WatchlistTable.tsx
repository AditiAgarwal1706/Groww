import { useNavigate } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'
import { type DashboardStock } from '../../api/changes'
import { type LiveQuote } from '../../hooks/useRealtimeQuotes'
import { SeverityBadge } from '../common/SeverityBadge'
import { FreshnessBadge } from '../common/FreshnessBadge'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface Props {
  stocks: DashboardStock[]
  liveQuotes?: Record<string, LiveQuote>
}

function fmt(n?: number | null, decimals = 2) {
  if (n === undefined || n === null) return '—'
  return n.toFixed(decimals)
}

function fmtChange(pct?: number | null) {
  if (pct === undefined || pct === null) return '—'
  return `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%`
}

/** Flashes green/red when the price changes */
function useFlash(value: number | undefined | null) {
  const prevRef = useRef<number | null>(null)
  const [flash, setFlash] = useState<'up' | 'down' | null>(null)

  useEffect(() => {
    if (value == null) return
    if (prevRef.current != null && prevRef.current !== value) {
      setFlash(value > prevRef.current ? 'up' : 'down')
      const t = setTimeout(() => setFlash(null), 800)
      prevRef.current = value
      return () => clearTimeout(t)
    }
    prevRef.current = value
  }, [value])

  return flash
}

function PriceCell({ price, changePct }: { price: number; changePct?: number | null }) {
  const flash = useFlash(price)
  const changeClass = changePct == null ? 'neutral' : changePct >= 0 ? 'positive' : 'negative'
  const Icon = changePct == null ? Minus : changePct >= 0 ? TrendingUp : TrendingDown

  return (
    <td style={{ textAlign: 'right' }}>
      <span
        style={{
          fontFamily: 'monospace',
          fontWeight: 600,
          fontSize: '0.9375rem',
          display: 'inline-block',
          padding: '0.1rem 0.35rem',
          borderRadius: '5px',
          transition: 'background 0.15s, color 0.15s',
          background: flash === 'up'
            ? 'rgba(16,185,129,0.22)'
            : flash === 'down'
            ? 'rgba(239,68,68,0.22)'
            : 'transparent',
          color: flash === 'up'
            ? '#10B981'
            : flash === 'down'
            ? '#EF4444'
            : 'var(--text-primary)',
        }}
      >
        ${fmt(price)}
      </span>
      <div>
        <span
          className={changeClass}
          style={{
            fontWeight: 600,
            fontSize: '0.75rem',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.2rem',
          }}
        >
          <Icon size={11} />
          {fmtChange(changePct)}
        </span>
      </div>
    </td>
  )
}

export function WatchlistTable({ stocks, liveQuotes = {} }: Props) {
  const navigate = useNavigate()

  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>
            <th>Stock</th>
            <th style={{ textAlign: 'right' }}>Price / Change</th>
            <th style={{ textAlign: 'right' }}>Volume ×</th>
            <th style={{ textAlign: 'right' }}>Attention</th>
            <th>Status</th>
            <th>Data</th>
          </tr>
        </thead>
        <tbody>
          {stocks.map((s) => {
            // Merge live quote data over the base dashboard data
            const live = liveQuotes[s.symbol]
            const price = live?.price ?? s.price
            const changePct = live?.change_pct ?? s.change_pct

            return (
              <tr key={s.symbol} onClick={() => navigate(`/stocks/${s.symbol}`)}>
                <td>
                  <div style={{ fontWeight: 700, fontSize: '0.9375rem' }}>{s.symbol}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{s.company_name}</div>
                </td>

                <PriceCell price={price} changePct={changePct} />

                <td style={{
                  textAlign: 'right',
                  color: (s.volume_ratio ?? 1) > 1.5 ? 'var(--accent-amber)' : 'var(--text-secondary)',
                  fontWeight: 500,
                }}>
                  {s.volume_ratio ? `${s.volume_ratio.toFixed(1)}×` : '—'}
                </td>

                <td style={{ textAlign: 'right' }}>
                  <span style={{
                    fontWeight: 800,
                    fontSize: '1rem',
                    color: s.attention_score >= 80 ? 'var(--severity-major)'
                         : s.attention_score >= 60 ? 'var(--severity-important)'
                         : s.attention_score >= 30 ? '#A78BFA'
                         : 'var(--text-muted)',
                  }}>
                    {Math.round(s.attention_score)}
                  </span>
                </td>

                <td><SeverityBadge severity={s.severity} /></td>
                <td>
                  <FreshnessBadge status={live ? 'LIVE' : s.data_status} />
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
