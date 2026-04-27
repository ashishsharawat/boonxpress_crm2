<template>
  <div class="relative">
    <button
      @click="open = !open"
      class="p-2 -mr-2 text-boon-text-secondary"
      aria-label="More actions"
    >
      <MoreVertical :size="20" />
    </button>
    <div v-if="open" @click.self="open = false" class="fixed inset-0 z-30">
      <div class="absolute right-3 top-12 bg-white rounded-lg shadow-xl border border-gray-200 min-w-[180px] py-1">
        <button
          v-for="item in items"
          :key="item.key"
          @click="select(item)"
          :class="[
            'w-full text-left px-4 py-2 text-sm hover:bg-gray-50',
            item.destructive ? 'text-red-600' : 'text-boon-text-primary',
          ]"
        >
          {{ item.label }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { MoreVertical } from 'lucide-vue-next'

defineProps({ items: { type: Array, required: true } })
const emit = defineEmits(['select'])
const open = ref(false)

function select(item) {
  open.value = false
  emit('select', item.key)
}
</script>
