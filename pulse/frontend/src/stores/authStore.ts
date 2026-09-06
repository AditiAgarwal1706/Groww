import { create } from 'zustand'
import { authApi } from '../api/auth'

interface User { id: number; email: string; name?: string }

interface AuthStore {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name?: string) => Promise<void>
  logout: () => void
  loadUser: () => Promise<void>
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  user: null,
  token: localStorage.getItem('pulse_token'),
  isLoading: false,
  isAuthenticated: !!localStorage.getItem('pulse_token'),

  login: async (email, password) => {
    set({ isLoading: true })
    try {
      const { access_token } = await authApi.login({ email, password })
      localStorage.setItem('pulse_token', access_token)
      const user = await authApi.me()
      set({ token: access_token, user, isAuthenticated: true, isLoading: false })
    } catch (err) {
      set({ isLoading: false })
      throw err
    }
  },

  register: async (email, password, name) => {
    set({ isLoading: true })
    try {
      const { access_token } = await authApi.register({ email, password, name })
      localStorage.setItem('pulse_token', access_token)
      const user = await authApi.me()
      set({ token: access_token, user, isAuthenticated: true, isLoading: false })
    } catch (err) {
      set({ isLoading: false })
      throw err
    }
  },

  logout: () => {
    localStorage.removeItem('pulse_token')
    set({ user: null, token: null, isAuthenticated: false })
  },

  loadUser: async () => {
    if (!get().token) return
    try {
      const user = await authApi.me()
      set({ user, isAuthenticated: true })
    } catch {
      get().logout()
    }
  },
}))
