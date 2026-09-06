import { api } from './client'

export interface ChangeSignal { type: string; value: number; label: string }
export interface DetectedChange {
  id: number; symbol: string; company_name: string;
  severity: 'MAJOR' | 'IMPORTANT' | 'WATCH' | 'NORMAL';
  attention_score: number; price: number; change_pct?: number; volume_ratio?: number;
  signals: ChangeSignal[]; summary: string; detected_at: string;
}
export interface ChangeSummary { major: number; important: number; watch: number; normal: number; total: number }
export interface DashboardStock {
  symbol: string; company_name: string; price: number; change_pct?: number;
  attention_score: number; severity: string; volume_ratio?: number; data_status: string;
}
export interface DashboardResponse {
  last_checked_at?: string; summary: ChangeSummary;
  top_attention: DetectedChange[]; watchlist: DashboardStock[];
  watchlist_id?: number; watchlist_name?: string;
}
export interface Attribution {
  company_specific: number; sector_effect: number; market_effect: number;
  company_specific_pct: number; sector_effect_pct: number; market_pct: number;
}
export interface AnalysisResponse {
  symbol: string; company_name: string; attention_score: number; severity: string;
  price_z_score: number; volume_ratio: number; attribution: Attribution;
  signals: ChangeSignal[]; confidence: number;
}
export interface AIExplanation {
  summary: string; drivers: { factor: string; weight: number; description: string }[];
  confidence: number; caveat: string;
}
export interface TimelineEvent {
  timestamp: string; event_type: string; description: string; severity?: string;
}
export interface NewsItem {
  id: number; title: string; summary?: string; source?: string; url?: string;
  published_at: string; sentiment?: string; impact_score: number; event_type?: string;
}

export const changesApi = {
  getDashboard: (syncLive = false) =>
    api.get<DashboardResponse>('/api/dashboard', { params: { sync_live: syncLive } }).then(r => r.data),


  getChanges: (watchlistId: number) =>
    api.get<DetectedChange[]>(`/api/watchlists/${watchlistId}/changes`).then(r => r.data),

  saveCheckpoint: (watchlistId: number) =>
    api.post(`/api/watchlists/${watchlistId}/checkpoint`).then(r => r.data),

  getCheckpointInfo: (watchlistId: number) =>
    api.get(`/api/watchlists/${watchlistId}/checkpoint`).then(r => r.data),

  getAnalysis: (symbol: string) =>
    api.get<AnalysisResponse>(`/api/stocks/${symbol}/analysis`).then(r => r.data),

  getExplanation: (symbol: string) =>
    api.get<AIExplanation>(`/api/stocks/${symbol}/explanation`).then(r => r.data),

  getTimeline: (symbol: string) =>
    api.get<TimelineEvent[]>(`/api/stocks/${symbol}/timeline`).then(r => r.data),

  getNews: (symbol: string) =>
    api.get<NewsItem[]>(`/api/stocks/${symbol}/news`).then(r => r.data),
}
