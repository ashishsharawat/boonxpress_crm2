import { defineStore } from 'pinia'

export const usePersonStore = defineStore('person', {
  state: () => ({
    cache: {},
  }),
  actions: {
    set(id, person) {
      const entry = { person, _fetchedAt: Date.now() }
      this.cache[id] = entry
      if (person?.canonical_id && person.canonical_id !== id) {
        this.cache[person.canonical_id] = entry
      }
    },
    get(id) {
      return this.cache[id] || null
    },
    invalidate(id) {
      const entry = this.cache[id]
      if (entry?.person?.canonical_id) delete this.cache[entry.person.canonical_id]
      delete this.cache[id]
    },
    invalidateAll() {
      this.cache = {}
    },
  },
})
