<template>
  <div class="flex bg-boon-surface border-b border-gray-100 sticky top-[60px] z-10 overflow-x-auto">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      @click="$emit('update:modelValue', tab.key)"
      :class="[
        'flex-shrink-0 px-3 py-2.5 text-xs font-semibold transition-colors',
        modelValue === tab.key
          ? 'text-boon-primary border-b-2 border-boon-primary'
          : 'text-boon-text-secondary border-b-2 border-transparent',
      ]"
    >
      {{ tab.label }}<span v-if="tab.count !== null && tab.count !== undefined" class="ml-1 opacity-70">({{ tab.count }})</span>
    </button>
  </div>
</template>

<script setup>
defineProps({
  tabs: { type: Array, required: true },
  modelValue: { type: String, required: true },
})
defineEmits(['update:modelValue'])
</script>
