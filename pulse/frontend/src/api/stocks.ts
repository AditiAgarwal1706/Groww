import { api } from './client'

export interface Stock { id: number; symbol: string; company_name: string; sector?: string; exchange?: string }
export interface Quote {
  symbol: string; company_name: string; price: number; open?: number; high?: number; low?: number;
  previous_close?: number; volume?: number; change_pct?: number; market_cap?: number;
  timestamp: string; data_status: string; sector?: string;
}
export interface HistoryPoint { date: string; open: number; high: number; low: number; close: number; volume: number }

export const stocksApi = {
  search: (q: string) =>
    api.get<Stock[]>(`/api/stocks/search`, { params: { q } }).then(r => r.data),

  getQuote: (symbol: string) =>
    api.get<Quote>(`/api/stocks/${symbol}/quote`).then(r => r.data),

  getHistory: (symbol: string, days = 30) =>
    api.get<{ symbol: string; history: HistoryPoint[] }>(`/api/stocks/${symbol}/history`, { params: { days } }).then(r => r.data),
}
