<template>
  <div
    class="flex items-center justify-center rounded-full bg-boon-primary-bg text-boon-primary font-semibold shrink-0"
    :class="sizeClass"
  >
    <span :class="textClass">{{ initials }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getInitials } from '@/utils/formatters'

const props = defineProps({
  name: { type: String, default: '' },
  size: { type: String, default: 'md' },
})

const initials = computed(() => getInitials(props.name))
const sizeClass = computed(() => ({
  sm: 'w-7 h-7',
  md: 'w-9 h-9',
  lg: 'w-12 h-12',
}[props.size] || 'w-9 h-9'))
const textClass = computed(() => ({
  sm: 'text-[10px]',
  md: 'text-xs',
  lg: 'text-sm',
}[props.size] || 'text-xs'))
</script>
