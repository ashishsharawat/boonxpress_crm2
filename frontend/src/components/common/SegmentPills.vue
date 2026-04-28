<template>
  <div class="flex gap-2 overflow-x-auto px-3 py-2 sticky top-0 bg-boon-surface z-10 border-b border-gray-100">
    <button
      v-for="seg in segments"
      :key="seg.key"
      @click="$emit('update:modelValue', seg.key)"
      :class="[
        'flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-semibold transition-colors',
        modelValue === seg.key
          ? 'bg-boon-primary text-white'
          : 'bg-boon-surface-alt text-boon-text-secondary',
      ]"
    >
      {{ seg.label }}<span v-if="seg.count !== undefined && seg.count !== null" class="ml-1 opacity-80">{{ seg.count }}</span>
    </button>
  </div>
</template>

<script setup>
defineProps({
  segments: { type: Array, required: true },
  modelValue: { type: String, required: true },
})
defineEmits(['update:modelValue'])
</script>
