interface Props { score: number; severity: string; size?: number }

const severityColors: Record<string, string> = {
  MAJOR: '#EF4444',
  IMPORTANT: '#F59E0B',
  WATCH: '#7C3AED',
  NORMAL: 'rgba(240,240,255,0.25)',
}

export function AttentionGauge({ score, severity, size = 80 }: Props) {
  const radius = (size - 8) / 2
  const circumference = 2 * Math.PI * radius
  const filled = (score / 100) * circumference
  const color = severityColors[severity] ?? severityColors.NORMAL

  return (
    <div className="attention-gauge" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth={6}
        />
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none"
          stroke={color}
          strokeWidth={6}
          strokeDasharray={`${filled} ${circumference - filled}`}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 1s cubic-bezier(0.34,1.56,0.64,1)', filter: `drop-shadow(0 0 6px ${color})` }}
        />
      </svg>
      <div className="attention-gauge-label">
        <span className="attention-gauge-value" style={{ color, fontSize: size < 70 ? '0.9rem' : '1.25rem' }}>
          {Math.round(score)}
        </span>
        <span style={{ fontSize: '0.6rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          score
        </span>
      </div>
    </div>
  )
}
