import { useNavigate } from 'react-router-dom'
import { type DetectedChange } from '../../api/changes'
import { AttentionGauge } from '../common/AttentionGauge'
import { SeverityBadge } from '../common/SeverityBadge'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface Props { change: DetectedChange; index?: number }

function formatChange(pct?: number) {
  if (pct === undefined || pct === null) return '—'
  const sign = pct >= 0 ? '+' : ''
  return `${sign}${pct.toFixed(2)}%`
}

export function AttentionCard({ change, index = 0 }: Props) {
  const navigate = useNavigate()
  const severity = change.severity.toLowerCase()
  const changePct = change.change_pct

  const Icon = changePct === undefined ? Minus : changePct >= 0 ? TrendingUp : TrendingDown
  const changeClass = changePct === undefined ? 'neutral' : changePct >= 0 ? 'positive' : 'negative'

  return (
    <div
      className={`attention-card ${severity} animate-fadeInUp stagger-${Math.min(index + 1, 5)}`}
      onClick={() => navigate(`/stocks/${change.symbol}`)}
      style={{ cursor: 'pointer' }}
    >
      <div className="flex items-center justify-between mb-2">
        <div>
          <div style={{ fontWeight: 800, fontSize: '1.25rem', letterSpacing: '-0.02em' }}>
            {change.symbol}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {change.company_name}
          </div>
        </div>
        <AttentionGauge score={change.attention_score} severity={change.severity} size={64} />
      </div>

      <div className="flex items-center gap-2 mt-3">
        <Icon size={14} className={changeClass} />
        <span className={`${changeClass} font-bold text-lg`}>
          {formatChange(changePct)}
        </span>
        <SeverityBadge severity={change.severity} />
      </div>

      <div style={{
        fontSize: '0.8rem', color: 'var(--text-secondary)',
        marginTop: '0.625rem', lineHeight: 1.4,
      }}>
        {change.summary}
      </div>

      {change.signals.length > 0 && (
        <div className="flex gap-2 mt-3" style={{ flexWrap: 'wrap' }}>
          {change.signals.slice(0, 2).map((sig, i) => (
            <span key={i} style={{
              fontSize: '0.7rem', padding: '0.2rem 0.5rem',
              background: 'rgba(255,255,255,0.06)',
              borderRadius: '100px', color: 'var(--text-secondary)',
            }}>
              {sig.type}: {sig.label.split(' ').slice(0, 3).join(' ')}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
