import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useIdentityResolver } from '@/composables/useIdentityResolver'

describe('useIdentityResolver', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    globalThis.fetch = vi.fn()
  })

  it('calls identity.resolve endpoint with given id', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        message: {
          canonical_id: 'CONT-001',
          lead: null,
          deals: [],
          contact: { name: 'CONT-001' },
          organization: null,
          summary: { last_contact: null, lifetime_value: 0, pipeline_value: 0, visit_count: 0, conversion_date: null },
        },
      }),
    })
    const { resolve } = useIdentityResolver()
    const person = await resolve('CRM-LEAD-2026-00001')
    expect(fetch).toHaveBeenCalledWith(
      '/api/method/boonxpress_crm.api.identity.resolve',
      expect.objectContaining({ method: 'POST' })
    )
    expect(person.canonical_id).toBe('CONT-001')
  })

  it('caches subsequent calls for same id within TTL', async () => {
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        message: { canonical_id: 'CONT-X', lead: null, deals: [], contact: null, organization: null, summary: {} },
      }),
    })
    const { resolve } = useIdentityResolver()
    await resolve('CONT-X')
    await resolve('CONT-X')
    expect(fetch).toHaveBeenCalledTimes(1)
  })

  it('throws on resolver error', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ exc: 'DoesNotExistError' }),
    })
    const { resolve } = useIdentityResolver()
    await expect(resolve('BAD-ID')).rejects.toThrow()
  })
})
