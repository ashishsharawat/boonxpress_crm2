<template>
  <span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium" :class="badgeClass">
    {{ status }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, required: true },
})

const badgeClass = computed(() => {
  const map = {
    Open: 'bg-blue-50 text-blue-700',
    Replied: 'bg-green-50 text-green-700',
    Converted: 'bg-emerald-50 text-emerald-700',
    Closed: 'bg-gray-100 text-gray-600',
    Lost: 'bg-red-50 text-red-700',
    Confirmed: 'bg-green-50 text-green-700',
    Pending: 'bg-yellow-50 text-yellow-700',
    Done: 'bg-gray-100 text-gray-600',
    Cancelled: 'bg-red-50 text-red-700',
    Hot: 'bg-red-50 text-red-700',
    Warm: 'bg-orange-50 text-orange-700',
    Cold: 'bg-blue-50 text-blue-700',
    Active: 'bg-green-50 text-green-700',
    Trial: 'bg-indigo-50 text-indigo-700',
  }
  return map[props.status] || 'bg-gray-100 text-gray-600'
})
</script>
