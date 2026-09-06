interface Props { status: string }

export function FreshnessBadge({ status }: Props) {
  const cls = status.toLowerCase()
  const dot = status === 'LIVE' ? '●' : status === 'DELAYED' ? '◐' : '○'
  return (
    <span className={`badge badge-${cls}`} style={{ gap: '0.25rem' }}>
      <span>{dot}</span>
      {status}
    </span>
  )
}
