<template>
  <div
    @click="$emit('tap', event)"
    class="bg-boon-surface px-4 py-3 border-b border-gray-100 flex gap-3 active:bg-gray-50 cursor-pointer"
  >
    <div :class="['w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0', iconBg]">
      <component :is="icon" :size="14" :class="iconColor" />
    </div>
    <div class="flex-1 min-w-0">
      <p class="text-sm font-semibold text-boon-text-primary">{{ title }}</p>
      <p class="text-xs text-boon-text-secondary mt-0.5 line-clamp-2">{{ event.content }}</p>
    </div>
    <span class="text-[10px] text-boon-text-secondary flex-shrink-0">{{ time }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { MessageCircle, Phone, RefreshCw, FileText, Calendar, CheckSquare, Paperclip } from 'lucide-vue-next'
import { formatRelative } from '@/utils/formatters'

const props = defineProps({ event: { type: Object, required: true } })
defineEmits(['tap'])

const ICONS = {
  whatsapp: { i: MessageCircle, bg: 'bg-emerald-100', color: 'text-emerald-700' },
  email: { i: MessageCircle, bg: 'bg-blue-100', color: 'text-blue-700' },
  call: { i: Phone, bg: 'bg-blue-100', color: 'text-blue-700' },
  stage: { i: RefreshCw, bg: 'bg-amber-100', color: 'text-amber-700' },
  note: { i: FileText, bg: 'bg-slate-100', color: 'text-slate-700' },
  appointment: { i: Calendar, bg: 'bg-pink-100', color: 'text-pink-700' },
  task: { i: CheckSquare, bg: 'bg-purple-100', color: 'text-purple-700' },
  file: { i: Paperclip, bg: 'bg-gray-100', color: 'text-gray-700' },
}

const meta = computed(() => ICONS[props.event.type] || ICONS.note)
const icon = computed(() => meta.value.i)
const iconBg = computed(() => meta.value.bg)
const iconColor = computed(() => meta.value.color)

const title = computed(() => {
  switch (props.event.type) {
    case 'whatsapp': return `WhatsApp ${props.event.direction === 'sent' ? 'sent' : 'received'}`
    case 'call': return `Call ${props.event.direction || ''}`
    case 'stage': return 'Stage change'
    case 'note': return 'Note'
    case 'appointment': return 'Appointment'
    case 'task': return 'Task'
    default: return props.event.type
  }
})

const time = computed(() => formatRelative(props.event.timestamp))
</script>
