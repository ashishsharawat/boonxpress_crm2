<template>
  <div v-if="loading" class="h-full flex items-center justify-center bg-boon-surface-alt">
    <div class="text-center">
      <div class="w-10 h-10 border-3 border-boon-primary border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
      <p class="text-sm text-boon-text-secondary font-body">Loading...</p>
    </div>
  </div>
  <MobileShell v-else>
    <router-view />
  </MobileShell>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useVerticalStore } from '@/stores/vertical'
import { useTheme } from '@/composables/useTheme'
import MobileShell from '@/components/layout/MobileShell.vue'

const verticalStore = useVerticalStore()
const { applyTheme } = useTheme()
const loading = ref(true)

onMounted(async () => {
  try {
    await verticalStore.loadConfig()
    applyTheme(verticalStore.colorScheme)
  } catch (err) {
    console.error('Failed to load vertical config:', err)
  } finally {
    loading.value = false
  }
})
</script>
