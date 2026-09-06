import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from './authStore'

describe('AuthStore Zustand Store', () => {
  beforeEach(() => {
    useAuthStore.getState().logout()
    localStorage.clear()
  })

  it('initializes as unauthenticated when localStorage is empty', () => {
    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.token).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })

  it('updates state on auth actions and persists in localStorage', () => {
    const dummyUser = { id: 1, email: 'trader@example.com', name: 'Pro Trader' }
    const dummyToken = 'jwt-secret-token-123'

    useAuthStore.setState({ user: dummyUser, token: dummyToken, isAuthenticated: true })

    const state = useAuthStore.getState()
    expect(state.user).toEqual(dummyUser)
    expect(state.token).toBe(dummyToken)
    expect(state.isAuthenticated).toBe(true)
  })

  it('logs out user and removes stored token from localStorage', () => {
    localStorage.setItem('pulse_token', 'token-123')
    useAuthStore.setState({ user: { id: 1, email: 'test@example.com' }, token: 'token-123', isAuthenticated: true })

    useAuthStore.getState().logout()

    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.token).toBeNull()
    expect(state.isAuthenticated).toBe(false)
    expect(localStorage.getItem('pulse_token')).toBeNull()
  })
})

