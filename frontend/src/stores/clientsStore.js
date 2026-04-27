import { defineStore } from 'pinia'
import { getList } from '@/utils/api'
import { PAGE_SIZE } from '@/utils/constants'

const FIELDS = ['name', 'first_name', 'last_name', 'email_id', 'mobile_no', 'image', 'modified']

export const useClientsStore = defineStore('clients', {
  state: () => ({
    segments: {},
  }),
  actions: {
    async loadSegment(segmentKey, segmentFilter, { reset = true, search = '' } = {}) {
      const seg = this.segments[segmentKey] || { items: [], page: 0, hasMore: true, loading: false }
      if (reset) {
        seg.items = []
        seg.page = 0
        seg.hasMore = true
      }
      seg.loading = true
      this.segments[segmentKey] = seg

      const filters = []
      if (search) filters.push(['first_name', 'like', `%${search}%`])
      // Semantic filter translation (visits_gte, days_since_last_visit_gt, etc.) currently
      // pass through as no-op for the v1 list view; richer filtering is delegated to
      // a future server-side endpoint that joins Contact ↔ Deal data.

      const data = await getList('Contact', {
        fields: FIELDS,
        filters,
        orderBy: 'modified desc',
        pageLength: PAGE_SIZE,
        start: seg.page * PAGE_SIZE,
      })

      seg.items = reset ? data : [...seg.items, ...data]
      seg.hasMore = data.length === PAGE_SIZE
      seg.page = seg.page + 1
      seg.loading = false
    },

    items(segmentKey) {
      return (this.segments[segmentKey] || {}).items || []
    },

    invalidateAll() {
      this.segments = {}
    },
  },
})
