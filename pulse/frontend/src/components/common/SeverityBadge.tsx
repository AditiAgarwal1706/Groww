interface Props {
  severity: 'MAJOR' | 'IMPORTANT' | 'WATCH' | 'NORMAL' | string
}

const labels: Record<string, string> = {
  MAJOR: 'MAJOR', IMPORTANT: 'IMPORTANT', WATCH: 'WATCH', NORMAL: 'NORMAL'
}

export function SeverityBadge({ severity }: Props) {
  const cls = severity.toLowerCase()
  return (
    <span className={`badge badge-${cls}`}>
      {labels[severity] ?? severity}
    </span>
  )
}
