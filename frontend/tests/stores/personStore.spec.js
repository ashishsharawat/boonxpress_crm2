import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { usePersonStore } from '@/stores/personStore'

describe('personStore', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('stores and retrieves by id', () => {
    const store = usePersonStore()
    store.set('CRM-LEAD-1', { canonical_id: 'CONT-1', deals: [] })
    expect(store.get('CRM-LEAD-1').person.canonical_id).toBe('CONT-1')
  })

  it('cross-keys by canonical id', () => {
    const store = usePersonStore()
    store.set('CRM-LEAD-1', { canonical_id: 'CONT-1', deals: [] })
    expect(store.get('CONT-1').person.canonical_id).toBe('CONT-1')
  })

  it('invalidate removes entry by both keys', () => {
    const store = usePersonStore()
    store.set('CRM-LEAD-1', { canonical_id: 'CONT-1', deals: [] })
    store.invalidate('CRM-LEAD-1')
    expect(store.get('CRM-LEAD-1')).toBeNull()
    expect(store.get('CONT-1')).toBeNull()
  })

  it('invalidateAll clears the cache', () => {
    const store = usePersonStore()
    store.set('A', { canonical_id: 'A' })
    store.set('B', { canonical_id: 'B' })
    store.invalidateAll()
    expect(store.get('A')).toBeNull()
    expect(store.get('B')).toBeNull()
  })
})
