/**
 * Tiny event bus that lets vertical home screens (e.g. SalonHome) react to
 * FAB clicks without restructuring MobileShell.
 *
 *   import { onFabAction, emitFabAction } from '@/composables/useFabBus'
 *
 *   // FAB.vue: emit on click
 *   emitFabAction('create_appointment')
 *
 *   // SalonHome.vue: subscribe within onMounted
 *   onFabAction(action => { if (action === 'create_appointment') ... })
 */

import { onMounted, onBeforeUnmount } from 'vue'

const EVENT_NAME = 'booncrm:fab-action'

export function emitFabAction(action) {
  window.dispatchEvent(new CustomEvent(EVENT_NAME, { detail: action }))
}

export function onFabAction(handler) {
  const wrapper = (e) => handler(e.detail)
  onMounted(() => window.addEventListener(EVENT_NAME, wrapper))
  onBeforeUnmount(() => window.removeEventListener(EVENT_NAME, wrapper))
}
