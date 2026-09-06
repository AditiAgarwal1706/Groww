import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { changesApi } from '../api/changes'
import { stocksApi } from '../api/stocks'
import { AttentionGauge } from '../components/common/AttentionGauge'
import { SeverityBadge } from '../components/common/SeverityBadge'
import { FreshnessBadge } from '../components/common/FreshnessBadge'
import { formatDistanceToNow, parseISO, format } from 'date-fns'
import { ArrowLeft, TrendingUp, TrendingDown, Newspaper, Clock, Zap } from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts'

function fmt(n?: number | null, d = 2) {
  if (n === undefined || n === null) return '—'
  return n.toFixed(d)
}

function fmtChange(pct?: number | null) {
  if (pct === undefined || pct === null) return '—'
  return `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%`
}

// Attribution bars component
function AttributionBars({ attribution }: { attribution: any }) {
  const bars = [
    { label: 'Company-specific', pct: attribution.company_specific_pct, cls: 'attribution-bar-company' },
    { label: 'Sector effect',    pct: attribution.sector_effect_pct,    cls: 'attribution-bar-sector' },
    { label: 'Market effect',    pct: attribution.market_pct,           cls: 'attribution-bar-market' },
  ]
  return (
    <div className="attribution-bar-container">
      {bars.map(({ label, pct, cls }) => (
        <div key={label} className="attribution-row">
          <span className="attribution-label">{label}</span>
          <div className="attribution-bar-track">
            <div className={`attribution-bar-fill ${cls}`} style={{ width: `${pct}%` }} />
          </div>
          <span className="attribution-pct">{pct.toFixed(0)}%</span>
        </div>
      ))}
    </div>
  )
}

// Timeline component
function EventTimeline({ events }: { events: any[] }) {
  if (!events || events.length === 0) {
    return <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>No significant events in the last 24 hours.</p>
  }

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'NEWS': return '📰'
      case 'PRICE_MOVE': return '📉'
      case 'VOLUME_SPIKE': return '📊'
      case 'SECTOR_MOVE': return '🏭'
      default: return '•'
    }
  }

  const getDotClass = (type: string) => {
    switch (type) {
      case 'NEWS': return 'news'
      case 'PRICE_MOVE': return 'price'
      case 'VOLUME_SPIKE': return 'volume'
      default: return 'sector'
    }
  }

  return (
    <div className="timeline">
      {events.map((event, i) => (
        <div key={i} className="timeline-item">
          <div className={`timeline-dot ${getDotClass(event.event_type)}`} />
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
            <span style={{ fontSize: '1rem' }}>{getEventIcon(event.event_type)}</span>
            <div>
              <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
                {format(parseISO(event.timestamp), 'h:mm a')}
                {event.severity && (
                  <span style={{ marginLeft: '0.5rem' }}>
                    <SeverityBadge severity={event.severity} />
                  </span>
                )}
              </div>
              <div style={{ fontSize: '0.875rem', color: 'var(--text-primary)', marginTop: '0.125rem' }}>
                {event.description}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

// AI Explanation component with typewriter
function AIExplanationPanel({ explanation }: { explanation: any }) {
  return (
    <div style={{
      background: 'rgba(124,58,237,0.06)',
      border: '1px solid rgba(124,58,237,0.2)',
      borderRadius: '12px',
      padding: '1.5rem',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
        <Zap size={16} color="var(--accent-violet)" />
        <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--accent-violet)' }}>
          AI Analysis
        </span>
        <span style={{
          marginLeft: 'auto', fontSize: '0.7rem', padding: '0.15rem 0.5rem',
          background: 'rgba(124,58,237,0.15)', borderRadius: '100px',
          color: '#A78BFA',
        }}>
          Confidence {explanation.confidence}%
        </span>
      </div>

      <p style={{ fontSize: '0.9375rem', lineHeight: 1.6, color: 'var(--text-primary)', marginBottom: '1rem' }}>
        "{explanation.summary}"
      </p>

      {explanation.drivers?.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
          {explanation.drivers.map((d: any, i: number) => (
            <div key={i} style={{ display: 'flex', gap: '0.75rem' }}>
              <div style={{
                width: `${Math.round(d.weight * 100)}%`, maxWidth: '60px', minWidth: '30px',
                height: '4px', background: 'var(--accent-violet)',
                borderRadius: '100px', marginTop: '0.4rem', flexShrink: 0,
              }} />
              <div>
                <span style={{ fontWeight: 600, fontSize: '0.8125rem' }}>{d.factor}</span>
                {d.description && (
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}> — {d.description}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={{
        fontSize: '0.75rem', color: 'var(--text-muted)',
        borderTop: '1px solid rgba(255,255,255,0.06)',
        paddingTop: '0.75rem',
        fontStyle: 'italic',
      }}>
        ⚠ {explanation.caveat}
      </div>
    </div>
  )
}

export function StockDetail() {
  const { symbol } = useParams<{ symbol: string }>()
  const navigate = useNavigate()

  const sym = symbol?.toUpperCase() ?? ''

  const { data: quote, isLoading: quoteLoading } = useQuery({
    queryKey: ['quote', sym],
    queryFn: () => stocksApi.getQuote(sym),
    enabled: !!sym,
    refetchInterval: 15_000,  // refresh every 15 seconds for near-real-time
  })

  const { data: history } = useQuery({
    queryKey: ['history', sym],
    queryFn: () => stocksApi.getHistory(sym, 30),
    enabled: !!sym,
  })

  const { data: analysis } = useQuery({
    queryKey: ['analysis', sym],
    queryFn: () => changesApi.getAnalysis(sym),
    enabled: !!sym,
  })

  const { data: explanation, isLoading: explLoading } = useQuery({
    queryKey: ['explanation', sym],
    queryFn: () => changesApi.getExplanation(sym),
    enabled: !!sym,
  })

  const { data: timeline } = useQuery({
    queryKey: ['timeline', sym],
    queryFn: () => changesApi.getTimeline(sym),
    enabled: !!sym,
  })

  const { data: news } = useQuery({
    queryKey: ['news', sym],
    queryFn: () => changesApi.getNews(sym),
    enabled: !!sym,
  })

  if (quoteLoading) {
    return (
      <div>
        <button className="btn btn-ghost btn-sm mb-4" onClick={() => navigate(-1)}>
          <ArrowLeft size={14} /> Back
        </button>
        <div className="skeleton" style={{ height: '120px', borderRadius: '16px' }} />
      </div>
    )
  }

  const changePct = quote?.change_pct
  const changeClass = !changePct ? 'neutral' : changePct >= 0 ? 'positive' : 'negative'
  const ChangeIcon = !changePct ? null : changePct >= 0 ? TrendingUp : TrendingDown

  const chartData = history?.history?.map(h => ({
    date: h.date.slice(5),
    price: h.close,
    volume: h.volume,
  })) ?? []

  return (
    <div>
      {/* Back */}
      <button className="btn btn-ghost btn-sm mb-4" onClick={() => navigate(-1)} id="back-btn">
        <ArrowLeft size={14} /> Back to Dashboard
      </button>

      {/* Header */}
      <div className="card mb-4">
        <div className="flex items-center justify-between" style={{ flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
              <h1 style={{ fontSize: '2rem' }}>{sym}</h1>
              {/* Pulsing LIVE dot */}
              <span style={{
                display: 'inline-flex', alignItems: 'center', gap: '0.35rem',
                fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase',
                letterSpacing: '0.06em', color: '#10B981',
                padding: '0.2rem 0.55rem', borderRadius: '100px',
                background: 'rgba(16,185,129,0.12)',
                border: '1px solid rgba(16,185,129,0.25)',
              }}>
                <span style={{
                  width: 6, height: 6, borderRadius: '50%',
                  background: '#10B981',
                  animation: 'pulse-live 2s ease-in-out infinite',
                  display: 'inline-block',
                }} />
                Live
              </span>
              {quote && <FreshnessBadge status={quote.data_status} />}
              {analysis && <SeverityBadge severity={analysis.severity} />}
            </div>
            <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
              {quote?.company_name}
              {quote?.sector && ` · ${quote.sector}`}
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.75rem' }}>
              <span style={{ fontSize: '2.5rem', fontWeight: 800, fontFamily: 'monospace', letterSpacing: '-0.03em' }}>
                ${fmt(quote?.price)}
              </span>
              {changePct !== undefined && ChangeIcon && (
                <span className={`${changeClass} flex items-center gap-1`} style={{ fontSize: '1.125rem', fontWeight: 700 }}>
                  <ChangeIcon size={18} />
                  {fmtChange(changePct)}
                </span>
              )}
            </div>
          </div>

          {analysis && (
            <div style={{ textAlign: 'center' }}>
              <AttentionGauge score={analysis.attention_score} severity={analysis.severity} size={100} />
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Attention Score
              </div>
            </div>
          )}
        </div>

        {/* Key stats */}
        <div className="divider" />
        <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
          {[
            { label: 'Open', value: `$${fmt(quote?.open)}` },
            { label: 'High', value: `$${fmt(quote?.high)}` },
            { label: 'Low',  value: `$${fmt(quote?.low)}` },
            { label: 'Prev Close', value: `$${fmt(quote?.previous_close)}` },
            { label: 'Volume', value: quote?.volume ? `${(quote.volume / 1e6).toFixed(1)}M` : '—' },
            analysis ? { label: 'Volume Ratio', value: `${fmt(analysis.volume_ratio, 1)}×`, color: analysis.volume_ratio > 1.5 ? 'var(--accent-amber)' : undefined } : null,
            analysis ? { label: 'Z-Score', value: fmt(analysis.price_z_score), color: Math.abs(analysis.price_z_score) > 2 ? 'var(--severity-major)' : undefined } : null,
          ].filter(Boolean).map((stat: any) => (
            <div key={stat.label}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>
                {stat.label}
              </div>
              <div style={{ fontWeight: 700, fontFamily: 'monospace', color: stat.color || 'var(--text-primary)' }}>
                {stat.value}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Price Chart */}
      {chartData.length > 0 && (
        <div className="card mb-4">
          <h4 className="mb-4">30-Day Price History</h4>
          <div style={{ height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={changePct && changePct >= 0 ? '#10B981' : '#EF4444'} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={changePct && changePct >= 0 ? '#10B981' : '#EF4444'} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="date" tick={{ fill: 'rgba(240,240,255,0.35)', fontSize: 11 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fill: 'rgba(240,240,255,0.35)', fontSize: 11 }} tickLine={false} axisLine={false} domain={['auto', 'auto']} />
                <Tooltip
                  contentStyle={{ background: '#0D0D1A', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 13 }}
                  labelStyle={{ color: 'rgba(240,240,255,0.55)' }}
                  itemStyle={{ color: '#F0F0FF' }}
                  formatter={(v: any) => [`$${Number(v).toFixed(2)}`, 'Price']}
                />
                <Area
                  type="monotone" dataKey="price"
                  stroke={changePct && changePct >= 0 ? '#10B981' : '#EF4444'}
                  strokeWidth={2}
                  fill="url(#priceGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="grid-2 mb-4">
        {/* Movement Attribution */}
        {analysis && (
          <div className="card">
            <h4 className="mb-2">Movement Attribution</h4>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
              Available evidence suggests how today's move was distributed:
            </p>
            <AttributionBars attribution={analysis.attribution} />
            <div style={{
              marginTop: '0.75rem', padding: '0.625rem 0.875rem',
              background: 'rgba(255,255,255,0.04)', borderRadius: 8,
              fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic',
            }}>
              Attribution is evidence-based estimation, not proof of causation.
            </div>
          </div>
        )}

        {/* Market Time Machine */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <Clock size={16} style={{ color: 'var(--accent-violet)' }} />
            <h4 style={{ margin: 0 }}>Market Time Machine</h4>
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
            Events in the last 24 hours:
          </p>
          <EventTimeline events={timeline ?? []} />
        </div>
      </div>

      {/* AI Explanation */}
      <div className="mb-4">
        <h4 className="mb-3">Why Did It Move?</h4>
        {explLoading ? (
          <div className="skeleton" style={{ height: '150px', borderRadius: '12px' }} />
        ) : explanation ? (
          <AIExplanationPanel explanation={explanation} />
        ) : null}
      </div>

      {/* News */}
      {news && news.length > 0 && (
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <Newspaper size={16} style={{ color: 'var(--accent-violet)' }} />
            <h4 style={{ margin: 0 }}>Recent News</h4>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {news.slice(0, 5).map((item) => (
              <div key={item.id} style={{
                padding: '0.875rem', background: 'rgba(255,255,255,0.03)',
                borderRadius: '10px', border: '1px solid var(--border)',
              }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem', marginBottom: '0.375rem' }}>
                  <span className={`badge badge-${(item.sentiment ?? 'neutral').toLowerCase()}`} style={{ flexShrink: 0 }}>
                    {item.sentiment ?? 'NEUTRAL'}
                  </span>
                  {item.event_type && (
                    <span className="badge badge-watch">{item.event_type}</span>
                  )}
                  <span style={{ marginLeft: 'auto', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {formatDistanceToNow(parseISO(item.published_at), { addSuffix: true })}
                  </span>
                </div>
                <a href={item.url ?? '#'} target="_blank" rel="noreferrer"
                  style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-primary)', lineHeight: 1.4, display: 'block' }}>
                  {item.title}
                </a>
                {item.source && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                    {item.source} · Impact: {(item.impact_score * 100).toFixed(0)}%
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
