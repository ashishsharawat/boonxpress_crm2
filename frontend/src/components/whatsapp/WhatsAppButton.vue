<template>
  <button
    v-if="phone"
    class="flex items-center justify-center touch-target rounded-full cursor-pointer transition-colors duration-200 hover:bg-green-50 active:bg-green-100"
    :class="sizeClass"
    @click="openChat(phone)"
  >
    <MessageCircle :size="iconSize" class="text-green-600" :fill="'#22c55e'" :stroke="'#16a34a'" />
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { MessageCircle } from 'lucide-vue-next'
import { useWhatsApp } from '@/composables/useWhatsApp'

const props = defineProps({
  phone: { type: String, default: '' },
  size: { type: String, default: 'md' },
})

const { openChat } = useWhatsApp()

const sizeClass = computed(() => props.size === 'sm' ? 'w-8 h-8' : 'w-10 h-10')
const iconSize = computed(() => props.size === 'sm' ? 16 : 20)
</script>
