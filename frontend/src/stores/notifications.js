import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useNotificationStore = defineStore('notifications', () => {
  const waPending = ref(0)
  const newLeads = ref(0)
  const totalUnread = ref(0)

  async function refresh() {
    try {
      const response = await fetch('/api/method/boonxpress_crm.api.stats.get_notification_counts', {
        headers: {
          'Content-Type': 'application/json',
          'X-Frappe-CSRF-Token': window.csrf_token || '',
        },
      })
      if (response.ok) {
        const data = await response.json()
        const counts = data.message || {}
        waPending.value = counts.wa_pending || 0
        newLeads.value = counts.new_leads || 0
        totalUnread.value = (counts.wa_pending || 0) + (counts.new_leads || 0)
      }
    } catch (err) {
      console.error('Failed to refresh notifications:', err)
    }
  }

  return { waPending, newLeads, totalUnread, refresh }
})
