import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useActivityStore } from '@/stores/activityStore'

describe('activityStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    globalThis.fetch = vi.fn()
  })

  it('fetches first page', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        message: { events: [{ id: 'a', type: 'note', timestamp: '2026-04-28' }], next_cursor: null },
      }),
    })
    const store = useActivityStore()
    await store.loadFeed('CRM-LEAD-1', 'all')
    expect(store.events('CRM-LEAD-1', 'all')).toHaveLength(1)
  })

  it('appends page on loadMore', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        message: { events: [{ id: 'a', type: 'note', timestamp: '2026-04-28' }], next_cursor: '2026-04-28' },
      }),
    })
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        message: { events: [{ id: 'b', type: 'note', timestamp: '2026-04-27' }], next_cursor: null },
      }),
    })
    const store = useActivityStore()
    await store.loadFeed('CRM-LEAD-1', 'all')
    await store.loadMore('CRM-LEAD-1', 'all')
    expect(store.events('CRM-LEAD-1', 'all')).toHaveLength(2)
  })

  it('separate cache per filter', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ message: { events: [{ id: 'a', type: 'note' }], next_cursor: null } }),
    })
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ message: { events: [{ id: 'b', type: 'whatsapp' }], next_cursor: null } }),
    })
    const store = useActivityStore()
    await store.loadFeed('CRM-LEAD-1', 'notes')
    await store.loadFeed('CRM-LEAD-1', 'messages')
    expect(store.events('CRM-LEAD-1', 'notes')[0].id).toBe('a')
    expect(store.events('CRM-LEAD-1', 'messages')[0].id).toBe('b')
  })
})
