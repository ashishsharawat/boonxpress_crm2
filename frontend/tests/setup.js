import { vi } from 'vitest'

// Mock window.csrf_token used by api.js
globalThis.window = globalThis.window || {}
window.csrf_token = 'test-csrf'

// Mock global fetch by default — individual tests override
globalThis.fetch = vi.fn()
