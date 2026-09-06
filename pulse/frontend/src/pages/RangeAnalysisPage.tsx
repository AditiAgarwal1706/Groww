import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Sparkles,
  Calendar,
  Search,
  TrendingUp,
  TrendingDown,
  Newspaper,
  ShieldAlert,
  ArrowRight,
  Info,
  Clock,
  ChevronRight
} from 'lucide-react'
import { changesApi, type RangeAnalysisResponse } from '../api/changes'
import { stocksApi } from '../api/stocks'

const QUICK_STOCKS = [
  { symbol: 'RELIANCE.NS', name: 'Reliance Industries' },
  { symbol: 'TCS.NS', name: 'Tata Consultancy Services' },
  { symbol: 'TATAMOTORS.NS', name: 'Tata Motors' },
  { symbol: 'INFY.NS', name: 'Infosys' },
  { symbol: 'AAPL', name: 'Apple Inc.' },
  { symbol: 'NVDA', name: 'NVIDIA Corp.' },
]

export function RangeAnalysisPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()

  // Default dates: last 14 days
  const todayStr = new Date().toISOString().split('T')[0]
  const fourteenDaysAgo = new Date(Date.now() - 14 * 24 * 60 * 60 * 1000)
    .toISOString()
    .split('T')[0]

  const [symbolInput, setSymbolInput] = useState(
    searchParams.get('symbol') || 'RELIANCE.NS'
  )
  const [activeSymbol, setActiveSymbol] = useState(
    searchParams.get('symbol') || 'RELIANCE.NS'
  )
  const [startDate, setStartDate] = useState(
    searchParams.get('start_date') || fourteenDaysAgo
  )
  const [endDate, setEndDate] = useState(
    searchParams.get('end_date') || todayStr
  )

  // Auto-complete stock search
  const [searchQuery, setSearchQuery] = useState('')
  const [showSearchResults, setShowSearchResults] = useState(false)

  const { data: searchResults } = useQuery({
    queryKey: ['stock-search', searchQuery],
    queryFn: () => stocksApi.search(searchQuery),
    enabled: searchQuery.length >= 2,
  })

  // Date range analysis query
  const {
    data: analysis,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<RangeAnalysisResponse>({
    queryKey: ['range-analysis', activeSymbol, startDate, endDate],
    queryFn: () => changesApi.getRangeAnalysis(activeSymbol, startDate, endDate),
    enabled: !!activeSymbol && !!startDate && !!endDate,
  })

  const handleAnalyze = (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!symbolInput.trim()) return

    const cleanSymbol = symbolInput.trim().toUpperCase()
    setActiveSymbol(cleanSymbol)
    setShowSearchResults(false)

    setSearchParams({
      symbol: cleanSymbol,
      start_date: startDate,
      end_date: endDate,
    })
  }

  const applyPreset = (days: number) => {
    const end = new Date().toISOString().split('T')[0]
    const start = new Date(Date.now() - days * 24 * 60 * 60 * 1000)
      .toISOString()
      .split('T')[0]
    setStartDate(start)
    setEndDate(end)
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '1.5rem 1rem' }}>
      {/* Header Banner */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <div
            style={{
              padding: '0.5rem',
              borderRadius: '0.75rem',
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(168, 85, 247, 0.2))',
              border: '1px solid rgba(129, 140, 248, 0.3)',
              color: '#818cf8',
              display: 'flex',
            }}
          >
            <Sparkles size={24} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
              AI Date Range Cause Analyzer
            </h1>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: 0 }}>
              Select a stock and timeframe to discover news events and market drivers behind price changes.
            </p>
          </div>
        </div>
      </div>

      {/* Control Card */}
      <div
        className="card"
        style={{
          padding: '1.5rem',
          marginBottom: '2rem',
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: '1rem',
          boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
        }}
      >
        <form onSubmit={handleAnalyze}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem', alignItems: 'end' }}>
            {/* Stock Search Input */}
            <div style={{ position: 'relative' }}>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                Stock Ticker / Company
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g. RELIANCE.NS, TCS.NS, AAPL..."
                  value={symbolInput}
                  onChange={e => {
                    setSymbolInput(e.target.value)
                    setSearchQuery(e.target.value)
                    setShowSearchResults(true)
                  }}
                  onFocus={() => setShowSearchResults(true)}
                  style={{ width: '100%', paddingLeft: '2.5rem' }}
                />
                <Search
                  size={16}
                  style={{
                    position: 'absolute',
                    left: '0.875rem',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--text-muted)',
                  }}
                />
              </div>

              {/* Search Dropdown */}
              {showSearchResults && searchResults && searchResults.length > 0 && (
                <div
                  style={{
                    position: 'absolute',
                    top: '100%',
                    left: 0,
                    right: 0,
                    zIndex: 50,
                    marginTop: '0.375rem',
                    background: 'var(--bg-elevated, #1e293b)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '0.75rem',
                    boxShadow: '0 10px 25px rgba(0,0,0,0.3)',
                    maxHeight: '220px',
                    overflowY: 'auto',
                  }}
                >
                  {searchResults.map(item => (
                    <div
                      key={item.symbol}
                      onClick={() => {
                        setSymbolInput(item.symbol)
                        setActiveSymbol(item.symbol)
                        setShowSearchResults(false)
                      }}
                      style={{
                        padding: '0.625rem 1rem',
                        cursor: 'pointer',
                        display: 'flex',
                        justify: 'space-between',
                        alignItems: 'center',
                        borderBottom: '1px solid rgba(255,255,255,0.05)',
                      }}
                      className="search-item-hover"
                    >
                      <div>
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{item.symbol}</span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginLeft: '0.5rem' }}>
                          {item.company_name}
                        </span>
                      </div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--accent-color, #6366f1)' }}>Select</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Start Date Picker */}
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                Start Date
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type="date"
                  className="input"
                  value={startDate}
                  onChange={e => setStartDate(e.target.value)}
                  style={{ width: '100%', paddingLeft: '2.5rem' }}
                />
                <Calendar
                  size={16}
                  style={{
                    position: 'absolute',
                    left: '0.875rem',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--text-muted)',
                  }}
                />
              </div>
            </div>

            {/* End Date Picker */}
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                End Date
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type="date"
                  className="input"
                  value={endDate}
                  onChange={e => setEndDate(e.target.value)}
                  style={{ width: '100%', paddingLeft: '2.5rem' }}
                />
                <Calendar
                  size={16}
                  style={{
                    position: 'absolute',
                    left: '0.875rem',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--text-muted)',
                  }}
                />
              </div>
            </div>

            {/* Submit Button */}
            <div>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isLoading}
                style={{
                  width: '100%',
                  padding: '0.625rem 1.25rem',
                  fontWeight: 600,
                  background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                  border: 'none',
                  boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                }}
              >
                {isLoading ? (
                  <>
                    <div className="spinner-sm" /> Analyzing News & Price...
                  </>
                ) : (
                  <>
                    <Sparkles size={16} /> Analyze Cause with AI
                  </>
                )}
              </button>
            </div>
          </div>
        </form>

        {/* Presets and Quick Tickers Bar */}
        <div
          style={{
            marginTop: '1.25rem',
            paddingTop: '1rem',
            borderTop: '1px solid var(--border-color)',
            display: 'flex',
            flexWrap: 'wrap',
            gap: '1.5rem',
            justify: 'space-between',
            alignItems: 'center',
          }}
        >
          {/* Quick Date Presets */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>Quick Presets:</span>
            {[
              { label: '7 Days', days: 7 },
              { label: '14 Days', days: 14 },
              { label: '30 Days', days: 30 },
              { label: '90 Days', days: 90 },
            ].map(p => (
              <button
                key={p.days}
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => applyPreset(p.days)}
                style={{ fontSize: '0.75rem', padding: '0.2rem 0.6rem', borderRadius: '0.5rem' }}
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Quick Stocks */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>Popular:</span>
            {QUICK_STOCKS.map(st => (
              <button
                key={st.symbol}
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => {
                  setSymbolInput(st.symbol)
                  setActiveSymbol(st.symbol)
                  setSearchParams({ symbol: st.symbol, start_date: startDate, end_date: endDate })
                }}
                style={{
                  fontSize: '0.75rem',
                  padding: '0.2rem 0.6rem',
                  borderRadius: '0.5rem',
                  background: activeSymbol === st.symbol ? 'rgba(99,102,241,0.15)' : undefined,
                  color: activeSymbol === st.symbol ? '#818cf8' : undefined,
                }}
              >
                {st.symbol.split('.')[0]}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error View */}
      {isError && (
        <div
          className="card"
          style={{
            padding: '2rem',
            textAlign: 'center',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '1rem',
            color: '#ef4444',
          }}
        >
          <ShieldAlert size={32} style={{ marginBottom: '0.5rem' }} />
          <h3 style={{ margin: '0 0 0.5rem 0' }}>Unable to Analyze Stock Range</h3>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: 0 }}>
            {(error as any)?.response?.data?.detail || 'Failed to fetch price history or news for this date range.'}
          </p>
        </div>
      )}

      {/* Analysis Results Container */}
      {analysis && !isLoading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Stock & Range Overview Card */}
          <div
            className="card"
            style={{
              padding: '1.5rem',
              borderRadius: '1rem',
              background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9))',
              border: '1px solid var(--border-color)',
            }}
          >
            <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                    {analysis.company_name}
                  </h2>
                  <span
                    style={{
                      padding: '0.25rem 0.625rem',
                      borderRadius: '0.5rem',
                      background: 'rgba(99,102,241,0.2)',
                      color: '#818cf8',
                      fontWeight: 600,
                      fontSize: '0.8125rem',
                    }}
                  >
                    {analysis.symbol}
                  </span>
                </div>
                <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Clock size={14} /> Timeframe: {analysis.start_date} to {analysis.end_date}
                </div>
              </div>

              {/* Price Change Pill */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem',
                  padding: '0.75rem 1.25rem',
                  borderRadius: '0.875rem',
                  background: analysis.price_change_pct >= 0 ? 'rgba(34, 197, 94, 0.12)' : 'rgba(239, 68, 68, 0.12)',
                  border: `1px solid ${analysis.price_change_pct >= 0 ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                }}
              >
                {analysis.price_change_pct >= 0 ? (
                  <TrendingUp size={24} color="#22c55e" />
                ) : (
                  <TrendingDown size={24} color="#ef4444" />
                )}
                <div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: analysis.price_change_pct >= 0 ? '#22c55e' : '#ef4444' }}>
                    {analysis.price_change_pct >= 0 ? '+' : ''}{analysis.price_change_pct.toFixed(2)}%
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                    {analysis.currency}{analysis.start_price.toFixed(2)} → {analysis.currency}{analysis.end_price.toFixed(2)}
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Metrics Bar */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                gap: '1rem',
                marginTop: '1.25rem',
                paddingTop: '1rem',
                borderTop: '1px solid rgba(255,255,255,0.08)',
              }}
            >
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Range High</span>
                <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {analysis.currency}{analysis.high_price.toFixed(2)}
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Range Low</span>
                <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {analysis.currency}{analysis.low_price.toFixed(2)}
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Absolute Change</span>
                <div style={{ fontSize: '1rem', fontWeight: 600, color: analysis.price_change >= 0 ? '#22c55e' : '#ef4444' }}>
                  {analysis.price_change >= 0 ? '+' : ''}{analysis.currency}{analysis.price_change.toFixed(2)}
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>News Analyzed</span>
                <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                  <Newspaper size={16} color="#818cf8" /> {analysis.news_count} Article(s)
                </div>
              </div>
            </div>
          </div>

          {/* AI Executive Explanation Card */}
          <div
            className="card"
            style={{
              padding: '1.5rem',
              borderRadius: '1rem',
              border: '1px solid rgba(129, 140, 248, 0.3)',
              background: 'linear-gradient(135deg, rgba(30, 27, 75, 0.5), rgba(15, 23, 42, 0.8))',
              boxShadow: '0 8px 30px rgba(99, 102, 241, 0.1)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#818cf8', fontWeight: 700 }}>
                <Sparkles size={20} />
                <span>AI Cause Attribution Executive Summary</span>
              </div>

              {/* Confidence Badge */}
              <div
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  padding: '0.25rem 0.625rem',
                  borderRadius: '1rem',
                  background: 'rgba(99,102,241,0.2)',
                  color: '#a5b4fc',
                  border: '1px solid rgba(99,102,241,0.3)',
                }}
              >
                {analysis.ai_explanation.confidence}% AI Confidence
              </div>
            </div>

            <p
              style={{
                fontSize: '1rem',
                lineHeight: '1.6',
                color: 'var(--text-primary)',
                margin: '0 0 1.25rem 0',
                fontWeight: 400,
              }}
            >
              {analysis.ai_explanation.summary}
            </p>

            {/* Drivers Progress Bars */}
            {analysis.ai_explanation.drivers && analysis.ai_explanation.drivers.length > 0 && (
              <div style={{ marginTop: '1rem' }}>
                <h4 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                  Identified Primary Drivers & Weights
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
                  {analysis.ai_explanation.drivers.map((drv, idx) => (
                    <div key={idx} style={{ background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '0.625rem', border: '1px solid rgba(255,255,255,0.05)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem', marginBottom: '0.375rem' }}>
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{drv.factor}</span>
                        <span style={{ fontWeight: 700, color: '#818cf8' }}>{Math.round(drv.weight * 100)}% Impact</span>
                      </div>
                      <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden', marginBottom: '0.375rem' }}>
                        <div
                          style={{
                            height: '100%',
                            width: `${Math.round(drv.weight * 100)}%`,
                            background: 'linear-gradient(90deg, #6366f1, #a855f7)',
                            borderRadius: '3px',
                          }}
                        />
                      </div>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: 0 }}>
                        {drv.description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* AI Caveat Footer */}
            <div
              style={{
                marginTop: '1.25rem',
                paddingTop: '0.75rem',
                borderTop: '1px solid rgba(255,255,255,0.08)',
                fontSize: '0.75rem',
                color: 'var(--text-muted)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.375rem',
              }}
            >
              <Info size={14} /> {analysis.ai_explanation.caveat}
            </div>
          </div>

          {/* Grid Layout: Key Events & News Articles */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem' }}>
            {/* Key News Events Timeline */}
            <div
              className="card"
              style={{
                padding: '1.5rem',
                borderRadius: '1rem',
                background: 'var(--bg-card)',
                border: '1px solid var(--border-color)',
              }}
            >
              <h3 style={{ fontSize: '1.125rem', fontWeight: 700, margin: '0 0 1rem 0', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Clock size={18} color="#818cf8" /> Key Events Timeline ({analysis.start_date} – {analysis.end_date})
              </h3>

              {analysis.key_events.length === 0 ? (
                <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>No discrete high-impact events isolated during this range.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
                  {analysis.key_events.map((ev, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        gap: '0.875rem',
                        padding: '0.75rem',
                        borderRadius: '0.625rem',
                        background: 'var(--bg-elevated, rgba(255,255,255,0.02))',
                        borderLeft: `4px solid ${
                          ev.impact === 'POSITIVE' ? '#22c55e' : ev.impact === 'NEGATIVE' ? '#ef4444' : '#94a3b8'
                        }`,
                      }}
                    >
                      <div>
                        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>{ev.date}</div>
                        <div style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-primary)', marginTop: '0.125rem' }}>
                          {ev.event}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* News Articles Covered */}
            <div
              className="card"
              style={{
                padding: '1.5rem',
                borderRadius: '1rem',
                background: 'var(--bg-card)',
                border: '1px solid var(--border-color)',
              }}
            >
              <h3 style={{ fontSize: '1.125rem', fontWeight: 700, margin: '0 0 1rem 0', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Newspaper size={18} color="#818cf8" /> News Coverage ({analysis.news_articles.length})
              </h3>

              {analysis.news_articles.length === 0 ? (
                <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                  No published news items recorded in local database for this timeframe. AI used market/price trend dynamics.
                </p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '360px', overflowY: 'auto' }}>
                  {analysis.news_articles.map((art, idx) => (
                    <a
                      key={art.id || idx}
                      href={art.url || '#'}
                      target="_blank"
                      rel="noreferrer"
                      style={{
                        padding: '0.75rem',
                        borderRadius: '0.625rem',
                        background: 'var(--bg-elevated, rgba(255,255,255,0.02))',
                        border: '1px solid var(--border-color)',
                        textDecoration: 'none',
                        display: 'block',
                        transition: 'border-color 0.2s',
                      }}
                    >
                      <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                        {art.title}
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        <span>{art.source}</span>
                        <span>{art.published_at ? art.published_at.split('T')[0] : ''}</span>
                      </div>
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
