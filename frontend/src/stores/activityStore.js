import { defineStore } from 'pinia'
import { call } from '@/utils/api'

function key(personId, filter) {
  return `${personId}::${filter || 'all'}`
}

export const useActivityStore = defineStore('activity', {
  state: () => ({
    feeds: {},
  }),
  actions: {
    async loadFeed(personId, filter = 'all', { force = false } = {}) {
      const k = key(personId, filter)
      if (!force && this.feeds[k] && Date.now() - this.feeds[k].fetchedAt < 30_000) {
        return this.feeds[k]
      }
      this.feeds[k] = { events: [], nextCursor: null, loading: true, fetchedAt: 0 }
      const result = await call('boonxpress_crm.api.activity.get_feed', {
        person_id: personId,
        filter_type: filter,
      })
      this.feeds[k] = {
        events: result.events || [],
        nextCursor: result.next_cursor,
        loading: false,
        fetchedAt: Date.now(),
      }
      return this.feeds[k]
    },
    async loadMore(personId, filter = 'all') {
      const k = key(personId, filter)
      const feed = this.feeds[k]
      if (!feed || !feed.nextCursor || feed.loading) return feed
      feed.loading = true
      const result = await call('boonxpress_crm.api.activity.get_feed', {
        person_id: personId,
        filter_type: filter,
        page_cursor: feed.nextCursor,
      })
      feed.events = [...feed.events, ...(result.events || [])]
      feed.nextCursor = result.next_cursor
      feed.loading = false
      return feed
    },
    events(personId, filter = 'all') {
      return (this.feeds[key(personId, filter)] || {}).events || []
    },
    invalidate(personId) {
      Object.keys(this.feeds).forEach((k) => {
        if (k.startsWith(`${personId}::`)) delete this.feeds[k]
      })
    },
  },
})
