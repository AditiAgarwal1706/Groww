import { api } from './client'

export interface Watchlist {
  id: number; name: string; created_at: string; updated_at: string; stock_count: number
}

export const watchlistApi = {
  list: () =>
    api.get<Watchlist[]>('/api/watchlists').then(r => r.data),

  create: (name: string) =>
    api.post<Watchlist>('/api/watchlists', { name }).then(r => r.data),

  get: (id: number) =>
    api.get(`/api/watchlists/${id}`).then(r => r.data),

  update: (id: number, name: string) =>
    api.patch<Watchlist>(`/api/watchlists/${id}`, { name }).then(r => r.data),

  delete: (id: number) =>
    api.delete(`/api/watchlists/${id}`),

  addStock: (id: number, symbol: string) =>
    api.post(`/api/watchlists/${id}/stocks`, { symbol }).then(r => r.data),

  removeStock: (id: number, symbol: string) =>
    api.delete(`/api/watchlists/${id}/stocks/${symbol}`),
}
