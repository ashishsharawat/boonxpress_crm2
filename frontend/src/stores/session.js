import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useSessionStore = defineStore('session', () => {
  const user = ref(null)
  const initialized = ref(false)

  const isLoggedIn = computed(() => !!user.value && user.value !== 'Guest')
  const fullName = computed(() => user.value?.full_name || '')
  const userEmail = computed(() => user.value?.email || '')

  async function init() {
    try {
      const response = await fetch('/api/method/frappe.auth.get_logged_user', {
        headers: {
          'X-Frappe-CSRF-Token': window.csrf_token || '',
        },
      })
      const data = await response.json()
      if (data.message && data.message !== 'Guest') {
        // Fetch full user info
        const userResponse = await fetch(`/api/resource/User/${data.message}?fields=["full_name","email","user_image"]`, {
          headers: {
            'X-Frappe-CSRF-Token': window.csrf_token || '',
          },
        })
        const userData = await userResponse.json()
        user.value = userData.data
      }
    } catch (err) {
      console.error('Session init failed:', err)
    } finally {
      initialized.value = true
    }
  }

  return { user, initialized, isLoggedIn, fullName, userEmail, init }
})
