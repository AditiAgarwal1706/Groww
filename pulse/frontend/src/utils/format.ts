/**
 * Currency and price formatting utility for PULSE.
 * Automatically formats Indian stocks (NSE/BSE, .NS, .BO, INR) with ₹
 * and US/global stocks with $.
 */

export function isIndianStock(symbol: string, currency?: string | null): boolean {
  if (!symbol) return false
  const sym = symbol.toUpperCase()
  return (
    sym.endsWith('.NS') ||
    sym.endsWith('.BO') ||
    currency === 'INR'
  )
}

export function getCurrencySymbol(symbol: string, currency?: string | null): string {
  return isIndianStock(symbol, currency) ? '₹' : '$'
}

export function formatPrice(price?: number | null, symbol: string = '', currency?: string | null, decimals = 2): string {
  if (price === undefined || price === null || isNaN(price)) return '—'
  const sign = getCurrencySymbol(symbol, currency)
  const formatted = price.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
  return `${sign}${formatted}`
}

export function formatChangePct(pct?: number | null): string {
  if (pct === undefined || pct === null || isNaN(pct)) return '—'
  return `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%`
}
