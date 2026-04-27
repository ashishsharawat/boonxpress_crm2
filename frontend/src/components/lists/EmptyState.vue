<template>
  <div class="flex flex-col items-center justify-center py-12 px-6 text-center">
    <div class="w-16 h-16 rounded-full bg-boon-primary-bg flex items-center justify-center mb-4">
      <Inbox :size="28" class="text-boon-primary" />
    </div>
    <p class="text-sm font-semibold text-boon-text-primary">{{ title }}</p>
    <p class="text-xs text-boon-text-secondary mt-1 max-w-[240px]">{{ message }}</p>
  </div>
</template>

<script setup>
import { Inbox } from 'lucide-vue-next'

defineProps({
  title: { type: String, default: 'Nothing here yet' },
  message: { type: String, default: '' },
})
</script>
