import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useLeadsStore } from '@/stores/leadsStore'

describe('leadsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    globalThis.fetch = vi.fn()
  })

  it('loads New segment from CRM Lead and tags badge', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ data: [{ name: 'CRM-LEAD-1', first_name: 'A', status: 'Open' }] }),
    })
    const store = useLeadsStore()
    await store.loadSegment('new', { doctype: 'CRM Lead', status_in: ['Open', 'Replied'] })
    const items = store.items('new')
    expect(items[0].name).toBe('CRM-LEAD-1')
    expect(items[0]._badge).toBe('LEAD')
  })

  it('loads Pipeline segment from CRM Deal and tags badge', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        data: [{ name: 'CRM-DEAL-1', organization: 'X', deal_value: 1000, currency: 'INR', status: 'Negotiation' }],
      }),
    })
    const store = useLeadsStore()
    await store.loadSegment('pipeline', { doctype: 'CRM Deal', status_not_in: ['Won', 'Lost'] })
    expect(store.items('pipeline')[0]._badge).toBe('DEAL')
  })

  it('Closed segment uses union endpoint', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        message: {
          items: [
            { doctype: 'CRM Lead', name: 'L1', status: 'Lost' },
            { doctype: 'CRM Deal', name: 'D1', status: 'Lost' },
          ],
          has_more: false,
        },
      }),
    })
    const store = useLeadsStore()
    await store.loadSegment('closed', { doctype: '*', status_in: ['Lost'] })
    expect(store.items('closed')).toHaveLength(2)
  })
})
