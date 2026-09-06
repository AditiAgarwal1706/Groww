import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { WatchlistTable } from './WatchlistTable'
import { type DashboardStock } from '../../api/changes'

const mockStocks: DashboardStock[] = [
  {
    symbol: 'NVDA',
    company_name: 'NVIDIA Corporation',
    price: 128.50,
    change_pct: -4.20,
    volume_ratio: 2.1,
    attention_score: 92,
    severity: 'MAJOR',
    data_status: 'LIVE',
  },
  {
    symbol: 'AAPL',
    company_name: 'Apple Inc.',
    price: 220.10,
    change_pct: 0.85,
    volume_ratio: 0.9,
    attention_score: 15,
    severity: 'NORMAL',
    data_status: 'LIVE',
  },
]

describe('WatchlistTable Component', () => {
  it('renders table headers and stock rows correctly', () => {
    render(
      <MemoryRouter>
        <WatchlistTable stocks={mockStocks} />
      </MemoryRouter>
    )

    expect(screen.getByText('NVDA')).toBeInTheDocument()
    expect(screen.getByText('NVIDIA Corporation')).toBeInTheDocument()
    expect(screen.getByText('AAPL')).toBeInTheDocument()
    expect(screen.getByText('Apple Inc.')).toBeInTheDocument()
    expect(screen.getByText('$128.50')).toBeInTheDocument()
    expect(screen.getByText('-4.20%')).toBeInTheDocument()
    expect(screen.getByText('+0.85%')).toBeInTheDocument()
  })

  it('overrides static price with real-time WebSocket liveQuotes data', () => {
    const liveQuotes = {
      NVDA: {
        symbol: 'NVDA',
        price: 135.00,
        change_pct: 5.06,
        volume: 80000000,
        open: 128.00,
        high: 136.00,
        low: 127.50,
        previous_close: 128.50,
        timestamp: Date.now(),
        data_status: 'LIVE',
      },
    }

    render(
      <MemoryRouter>
        <WatchlistTable stocks={mockStocks} liveQuotes={liveQuotes} />
      </MemoryRouter>
    )

    expect(screen.getByText('$135.00')).toBeInTheDocument()
    expect(screen.getByText('+5.06%')).toBeInTheDocument()
  })
})
