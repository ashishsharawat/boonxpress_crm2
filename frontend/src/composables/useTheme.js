import { watch } from 'vue'
import { useVerticalStore } from '@/stores/vertical'

export function useTheme() {
  const verticalStore = useVerticalStore()

  function applyTheme(scheme) {
    if (!scheme) return
    const root = document.documentElement
    const props = {
      '--boon-primary': scheme.primary,
      '--boon-primary-light': scheme.primary_light,
      '--boon-primary-bg': scheme.primary_bg,
      '--boon-primary-dark': scheme.primary_dark,
      '--boon-accent': scheme.accent,
      '--boon-text-primary': scheme.text_primary,
      '--boon-text-secondary': scheme.text_secondary,
      '--boon-surface': scheme.surface,
      '--boon-surface-alt': scheme.surface_alt,
    }
    for (const [key, value] of Object.entries(props)) {
      if (value) root.style.setProperty(key, value)
    }

    // Update theme-color meta tag for mobile browser chrome
    const meta = document.querySelector('meta[name="theme-color"]')
    if (meta) {
      meta.setAttribute('content', scheme.primary)
    } else {
      const newMeta = document.createElement('meta')
      newMeta.name = 'theme-color'
      newMeta.content = scheme.primary
      document.head.appendChild(newMeta)
    }
  }

  // Watch for config changes and re-apply theme
  watch(() => verticalStore.colorScheme, (newScheme) => {
    if (newScheme) applyTheme(newScheme)
  })

  return { applyTheme }
}
