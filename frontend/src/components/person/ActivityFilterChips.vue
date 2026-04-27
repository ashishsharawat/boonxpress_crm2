<template>
  <div class="flex gap-2 px-4 py-2 overflow-x-auto bg-boon-surface sticky top-0 z-10 border-b border-gray-100">
    <button
      v-for="chip in chips"
      :key="chip.key"
      @click="$emit('update:modelValue', chip.key)"
      :class="[
        'flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-semibold transition-colors',
        modelValue === chip.key ? 'bg-boon-primary text-white' : 'bg-boon-surface-alt text-boon-text-secondary',
      ]"
    >{{ chip.label }}</button>
  </div>
</template>

<script setup>
defineProps({
  chips: { type: Array, required: true },
  modelValue: { type: String, required: true },
})
defineEmits(['update:modelValue'])
</script>
