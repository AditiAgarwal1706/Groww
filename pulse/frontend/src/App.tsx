import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useEffect } from 'react'
import { useAuthStore } from './stores/authStore'
import { AppLayout } from './components/layout/AppLayout'
import { Login } from './pages/Login'
import { Register } from './pages/Register'
import { Dashboard } from './pages/Dashboard'
import { WatchlistPage } from './pages/WatchlistPage'
import { StockDetail } from './pages/StockDetail'
import { RangeAnalysisPage } from './pages/RangeAnalysisPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
})

function AuthLoader() {
  const { loadUser, isAuthenticated } = useAuthStore()
  useEffect(() => {
    if (isAuthenticated) loadUser()
  }, [])
  return null
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthLoader />
        <Routes>
          {/* Public */}
          <Route path="/login"    element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected */}
          <Route path="/dashboard" element={<AppLayout><Dashboard /></AppLayout>} />
          <Route path="/watchlist" element={<AppLayout><WatchlistPage /></AppLayout>} />
          <Route path="/range-analysis" element={<AppLayout><RangeAnalysisPage /></AppLayout>} />
          <Route path="/stocks/:symbol" element={<AppLayout><StockDetail /></AppLayout>} />

          {/* Default */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
