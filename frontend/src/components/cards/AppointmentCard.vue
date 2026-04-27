<template>
  <div class="flex items-center gap-3 bg-boon-surface rounded-xl px-3 py-3 cursor-pointer transition-colors duration-200 active:bg-gray-50"
       @click="$emit('tap', appointment)">
    <div class="text-center shrink-0 w-12">
      <p class="text-sm font-bold text-boon-primary">{{ formatTime(appointment.time_slot) }}</p>
    </div>
    <div class="flex-1 min-w-0">
      <p class="text-sm font-semibold text-boon-text-primary truncate">
        {{ appointment.client_name }}
      </p>
      <p class="text-xs text-boon-text-secondary mt-0.5 truncate">
        {{ appointment.service_type }}
      </p>
    </div>
    <div class="flex items-center gap-2 shrink-0">
      <WhatsAppButton
        v-if="appointment.client_phone"
        :phone="appointment.client_phone"
        size="sm"
        @click.stop
      />
      <span
        class="w-2.5 h-2.5 rounded-full shrink-0"
        :class="statusColor"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import WhatsAppButton from '@/components/whatsapp/WhatsAppButton.vue'
import { formatTime } from '@/utils/formatters'
import { APPOINTMENT_STATUS_COLORS } from '@/utils/constants'

const props = defineProps({
  appointment: { type: Object, required: true },
})
defineEmits(['tap'])

const statusColor = computed(() => {
  const status = props.appointment.status || 'Pending'
  const colors = {
    Confirmed: 'bg-green-500',
    Pending: 'bg-yellow-500',
    Done: 'bg-gray-400',
    Cancelled: 'bg-red-500',
  }
  return colors[status] || 'bg-gray-400'
})
</script>
