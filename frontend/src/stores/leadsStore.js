import { defineStore } from 'pinia'
import { getList, call } from '@/utils/api'
import { PAGE_SIZE } from '@/utils/constants'

const FIELDS_LEAD = ['name', 'first_name', 'last_name', 'mobile_no', 'email', 'source', 'status', 'modified']
const FIELDS_DEAL = ['name', 'organization', 'deal_value', 'currency', 'status', 'expected_closure_date', 'modified']

export const useLeadsStore = defineStore('leads', {
  state: () => ({
    segments: {},
    counts: {},
  }),
  actions: {
    async loadSegment(segmentKey, filter, { reset = true, search = '' } = {}) {
      const seg = this.segments[segmentKey] || { items: [], page: 0, hasMore: true, loading: false }
      if (reset) {
        seg.items = []
        seg.page = 0
        seg.hasMore = true
      }
      seg.loading = true
      this.segments[segmentKey] = seg

      const items = await this._fetchByFilter(filter, seg.page, search)
      seg.items = reset ? items : [...seg.items, ...items]
      seg.hasMore = items.length === PAGE_SIZE
      seg.page = seg.page + 1
      seg.loading = false
    },

    async _fetchByFilter(filter, page, search) {
      // Closed segment uses the union endpoint
      if (filter.doctype === '*') {
        const result = await call('boonxpress_crm.api.leads.get_closed', {
          page,
          page_size: PAGE_SIZE,
        })
        return (result.items || []).map(this._tagItem)
      }

      const filters = []
      if (filter.status_in) filters.push(['status', 'in', filter.status_in])
      if (filter.status_not_in) filters.push(['status', 'not in', filter.status_not_in])
      if (search) {
        if (filter.doctype === 'CRM Lead') filters.push(['first_name', 'like', `%${search}%`])
        else if (filter.doctype === 'CRM Deal') filters.push(['organization', 'like', `%${search}%`])
      }

      const fields = filter.doctype === 'CRM Lead' ? FIELDS_LEAD : FIELDS_DEAL
      const data = await getList(filter.doctype, {
        fields,
        filters,
        orderBy: 'modified desc',
        pageLength: PAGE_SIZE,
        start: page * PAGE_SIZE,
      })
      return data.map((row) => this._tagItem({ ...row, doctype: filter.doctype }))
    },

    _tagItem(item) {
      item._badge = item.doctype === 'CRM Deal' ? 'DEAL' : 'LEAD'
      return item
    },

    items(segmentKey) {
      return (this.segments[segmentKey] || {}).items || []
    },

    invalidateAll() {
      this.segments = {}
      this.counts = {}
    },
  },
})
