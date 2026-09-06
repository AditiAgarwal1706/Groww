interface Props { status: string }

export function FreshnessBadge({ status }: Props) {
  const s = (status ?? 'UNKNOWN').toUpperCase()

  const config: Record<string, { dot: string; label: string; cls: string }> = {
    LIVE:          { dot: '●', label: 'LIVE',          cls: 'live' },
    PRE_MARKET:    { dot: '◑', label: 'PRE-MARKET',   cls: 'premarket' },
    AFTER_HOURS:   { dot: '◑', label: 'AFTER HOURS',  cls: 'afterhours' },
    MARKET_CLOSED: { dot: '○', label: 'MKT CLOSED',   cls: 'closed' },
    DELAYED:       { dot: '◐', label: 'DELAYED',       cls: 'delayed' },
    UNAVAILABLE:   { dot: '✕', label: 'N/A',           cls: 'unavailable' },
  }

  const { dot, label, cls } = config[s] ?? { dot: '○', label: s, cls: 'closed' }

  return (
    <span className={`badge badge-${cls}`} style={{ gap: '0.25rem', whiteSpace: 'nowrap' }}>
      <span>{dot}</span>
      {label}
    </span>
  )
}
