import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock WebSocket for React tests
class MockWebSocket {
  url: string
  readyState = 1 // OPEN
  onopen: (() => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null
  onerror: (() => void) | null = null
  onclose: (() => void) | null = null

  constructor(url: string) {
    this.url = url
    setTimeout(() => {
      if (this.onopen) this.onopen()
    }, 10)
  }

  send(data: string) {
    // Echo back ping
    try {
      const parsed = JSON.parse(data)
      if (parsed.action === 'ping' && this.onmessage) {
        this.onmessage({ data: JSON.stringify({ type: 'pong' }) })
      }
    } catch {}
  }

  close() {
    if (this.onclose) this.onclose()
  }
}

global.WebSocket = MockWebSocket as any

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
} as any

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})
