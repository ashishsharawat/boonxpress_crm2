import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useVerticalStore = defineStore('vertical', () => {
  const config = ref(null)
  const loaded = ref(false)
  const error = ref(null)

  // Computed accessors for common config fields
  const verticalType = computed(() => config.value?.vertical_type || 'general')
  const displayName = computed(() => config.value?.display_name || 'BoonCRM')
  const colorScheme = computed(() => config.value?.color_scheme || {})
  const navItems = computed(() => config.value?.nav_items || [])
  const homeComponent = computed(() => config.value?.home_component || 'GeneralHome')
  const visibleModules = computed(() => config.value?.visible_modules || [])
  const hiddenModules = computed(() => config.value?.hidden_modules || [])
  const contactFields = computed(() => config.value?.contact_fields || [])
  const leadFields = computed(() => config.value?.lead_fields || [])
  const statsConfig = computed(() => config.value?.stats_config || [])
  const terminology = computed(() => config.value?.terminology || {})
  const fabActions = computed(() => config.value?.fab_actions || [])
  const businessName = computed(() => config.value?.business_name || displayName.value)

  // Resolve terminology — returns the vertical-specific label or fallback
  function term(key, fallback) {
    const t = terminology.value?.[key]
    return t === null ? null : (t || fallback || key)
  }

  // Check if a module is visible
  function isModuleVisible(moduleName) {
    if (hiddenModules.value.includes(moduleName)) return false
    if (visibleModules.value.length === 0) return true
    return visibleModules.value.includes(moduleName)
  }

  // Load config from Frappe API
  async function loadConfig() {
    try {
      error.value = null
      const response = await fetch('/api/method/boonxpress_crm.api.vertical.get_config', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Frappe-CSRF-Token': window.csrf_token || '',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to load config: ${response.status}`)
      }

      const data = await response.json()
      config.value = data.message || data
      loaded.value = true
    } catch (err) {
      error.value = err.message
      console.error('Failed to load vertical config:', err)

      // Fallback: try loading from window.__booncrm_config__ (set by booncrm.py)
      if (window.__booncrm_config__) {
        config.value = window.__booncrm_config__
        loaded.value = true
        error.value = null
      }
    }
  }

  return {
    config,
    loaded,
    error,
    verticalType,
    displayName,
    colorScheme,
    navItems,
    homeComponent,
    visibleModules,
    hiddenModules,
    contactFields,
    leadFields,
    statsConfig,
    terminology,
    fabActions,
    businessName,
    term,
    isModuleVisible,
    loadConfig,
  }
})
