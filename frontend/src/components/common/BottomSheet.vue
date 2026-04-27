<template>
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="modelValue" class="fixed inset-0 z-50">
        <div class="absolute inset-0 bg-black/40" @click="close" />
        <div class="absolute bottom-0 left-0 right-0 bg-boon-surface rounded-t-2xl max-h-[85vh] flex flex-col">
          <!-- Handle -->
          <div class="flex justify-center py-2 shrink-0">
            <div class="w-10 h-1 bg-gray-300 rounded-full" />
          </div>
          <!-- Header -->
          <div v-if="title" class="flex items-center justify-between px-4 pb-3 border-b border-gray-100 shrink-0">
            <h2 class="text-base font-semibold text-boon-text-primary font-heading">{{ title }}</h2>
            <button class="touch-target flex items-center justify-center cursor-pointer" @click="close">
              <X :size="20" class="text-boon-text-secondary" />
            </button>
          </div>
          <!-- Content -->
          <div class="flex-1 overflow-y-auto px-4 py-4">
            <slot />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { X } from 'lucide-vue-next'

defineProps({
  modelValue: { type: Boolean, required: true },
  title: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

function close() {
  emit('update:modelValue', false)
}
</script>

<style scoped>
.sheet-enter-active, .sheet-leave-active {
  transition: all 0.3s ease-out;
}
.sheet-enter-active > div:last-child, .sheet-leave-active > div:last-child {
  transition: transform 0.3s ease-out;
}
.sheet-enter-from > div:first-child, .sheet-leave-to > div:first-child {
  opacity: 0;
}
.sheet-enter-from > div:last-child, .sheet-leave-to > div:last-child {
  transform: translateY(100%);
}
</style>
