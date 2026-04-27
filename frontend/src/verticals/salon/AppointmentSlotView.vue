<template>
  <div class="px-4 py-2">
    <h3 class="text-sm font-semibold text-boon-text-primary font-heading mb-3">Schedule View</h3>
    <div class="space-y-1">
      <div
        v-for="slot in timeSlots"
        :key="slot.time"
        class="flex items-stretch gap-2 min-h-[44px]"
      >
        <!-- Time label -->
        <div class="w-14 text-right pr-2 py-2 shrink-0">
          <span class="text-xs text-boon-text-secondary">{{ slot.label }}</span>
        </div>
        <!-- Slot content -->
        <div class="flex-1 border-t border-gray-100 py-1">
          <div
            v-if="slot.appointment"
            class="rounded-lg px-2 py-1.5 text-xs"
            :class="statusBg(slot.appointment.status)"
          >
            <p class="font-medium text-boon-text-primary truncate">{{ slot.appointment.client_name }}</p>
            <p class="text-boon-text-secondary truncate">{{ slot.appointment.service_type }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  appointments: { type: Array, default: () => [] },
})

const hours = Array.from({ length: 12 }, (_, i) => i + 9) // 9AM to 8PM

const timeSlots = computed(() => {
  return hours.map(hour => {
    const timeStr = `${String(hour).padStart(2, '0')}:00`
    const label = hour < 12 ? `${hour} AM` : hour === 12 ? '12 PM' : `${hour - 12} PM`
    const appointment = props.appointments.find(a => {
      if (!a.time_slot) return false
      const aptHour = parseInt(a.time_slot.split(':')[0])
      return aptHour === hour
    })
    return { time: timeStr, label, appointment }
  })
})

function statusBg(status) {
  const map = {
    Confirmed: 'bg-green-50 border-l-2 border-green-400',
    Pending: 'bg-yellow-50 border-l-2 border-yellow-400',
    Done: 'bg-gray-50 border-l-2 border-gray-400',
    Cancelled: 'bg-red-50 border-l-2 border-red-300',
  }
  return map[status] || 'bg-gray-50'
}
</script>
