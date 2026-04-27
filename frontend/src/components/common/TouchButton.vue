<template>
  <button
    class="touch-target inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-all duration-200 cursor-pointer active:scale-95"
    :class="[variantClass, sizeClass]"
    :disabled="disabled || loading"
  >
    <div v-if="loading" class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
    <slot v-else />
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: { type: String, default: 'primary' },
  size: { type: String, default: 'md' },
  disabled: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
})

const variantClass = computed(() => ({
  primary: 'bg-boon-primary text-white hover:opacity-90 disabled:opacity-50',
  secondary: 'bg-boon-surface text-boon-text-primary border border-gray-200 hover:bg-gray-50 disabled:opacity-50',
  ghost: 'text-boon-text-secondary hover:bg-gray-50 disabled:opacity-50',
  accent: 'bg-boon-accent text-white hover:opacity-90 disabled:opacity-50',
}[props.variant] || ''))

const sizeClass = computed(() => ({
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2.5 text-sm',
  lg: 'px-6 py-3 text-base',
}[props.size] || 'px-4 py-2.5 text-sm'))
</script>
