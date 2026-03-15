import { config } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

config.global.stubs = {
  localStorage: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
  },
}

export function setupPinia() {
  const pinia = createPinia()
  setActivePinia(pinia)
}

beforeEach(() => {
  setupPinia()
})
