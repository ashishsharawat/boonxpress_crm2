<template>
  <div class="relative">
    <Search :size="16" class="absolute left-3 top-1/2 -translate-y-1/2 text-boon-text-secondary pointer-events-none" />
    <input
      type="search"
      :placeholder="placeholder"
      :value="modelValue"
      class="w-full h-10 pl-9 pr-3 text-sm bg-boon-surface border border-gray-200 rounded-xl text-boon-text-primary placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-boon-primary/30 focus:border-boon-primary transition-colors duration-200"
      @input="onInput"
    />
  </div>
</template>

<script setup>
import { Search } from 'lucide-vue-next'
import { DEBOUNCE_MS } from '@/utils/constants'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: 'Search...' },
})

const emit = defineEmits(['update:modelValue'])

let timeout = null
function onInput(e) {
  clearTimeout(timeout)
  timeout = setTimeout(() => {
    emit('update:modelValue', e.target.value)
  }, DEBOUNCE_MS)
}
</script>
