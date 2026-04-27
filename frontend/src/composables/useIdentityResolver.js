import { call } from '@/utils/api'
import { usePersonStore } from '@/stores/personStore'

const TTL_MS = 60_000

export function useIdentityResolver() {
  const store = usePersonStore()

  async function resolve(id) {
    const cached = store.get(id)
    if (cached && Date.now() - cached._fetchedAt < TTL_MS) {
      return cached.person
    }
    const person = await call('boonxpress_crm.api.identity.resolve', { id })
    store.set(id, person)
    return person
  }

  return { resolve }
}
