<template>
  <div class="h-full overflow-y-auto">
    <!-- Quick Stats -->
    <QuickStatsBar :stats="statsData" />

    <!-- Today's Appointments -->
    <div class="px-4 py-2">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-sm font-semibold text-boon-text-primary font-heading">Today's Appointments</h2>
        <span class="text-xs text-boon-text-secondary">{{ todayLabel }}</span>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="space-y-2">
        <div v-for="i in 4" :key="i" class="bg-boon-surface rounded-xl px-3 py-3 flex items-center gap-3">
          <div class="w-12 h-8 skeleton rounded" />
          <div class="flex-1 space-y-2">
            <div class="h-3.5 w-3/4 skeleton rounded" />
            <div class="h-3 w-1/2 skeleton rounded" />
          </div>
        </div>
      </div>

      <!-- Appointment list -->
      <div v-else-if="appointments.length" class="space-y-2">
        <AppointmentCard
          v-for="apt in appointments"
          :key="apt.name"
          :appointment="apt"
          @tap="openAppointment"
        />
      </div>

      <!-- Empty state -->
      <div v-else class="text-center py-8">
        <Calendar :size="40" class="text-boon-primary-light mx-auto mb-2" />
        <p class="text-sm font-medium text-boon-text-primary">No appointments today</p>
        <p class="text-xs text-boon-text-secondary mt-1">Tap + to book a new appointment</p>
      </div>
    </div>

    <!-- Book Appointment Sheet -->
    <BookAppointment v-model="showBooking" @created="onAppointmentCreated" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Calendar } from 'lucide-vue-next'
import QuickStatsBar from '@/components/stats/QuickStatsBar.vue'
import AppointmentCard from '@/components/cards/AppointmentCard.vue'
import BookAppointment from './BookAppointment.vue'
import { call } from '@/utils/api'

const loading = ref(true)
const appointments = ref([])
const statsData = ref([])
const showBooking = ref(false)

const todayLabel = computed(() => {
  return new Date().toLocaleDateString('en-IN', { weekday: 'long', month: 'short', day: 'numeric' })
})

async function loadData() {
  loading.value = true
  try {
    const [aptsData, stats] = await Promise.all([
      call('boonxpress_crm.api.appointments.get_today'),
      call('boonxpress_crm.api.stats.get_quick_stats'),
    ])
    appointments.value = aptsData || []
    statsData.value = [
      { key: 'appointments_today', label: 'Today', icon: 'Calendar', value: stats?.appointments_today ?? 0 },
      { key: 'new_leads', label: 'New Leads', icon: 'Target', value: stats?.new_leads ?? 0 },
      { key: 'wa_pending', label: 'WA Pending', icon: 'MessageCircle', value: stats?.wa_pending ?? 0 },
    ]
  } catch (err) {
    console.error('Failed to load salon home data:', err)
    // Show zeroes on error
    statsData.value = [
      { key: 'appointments_today', label: 'Today', icon: 'Calendar', value: 0 },
      { key: 'new_leads', label: 'New Leads', icon: 'Target', value: 0 },
      { key: 'wa_pending', label: 'WA Pending', icon: 'MessageCircle', value: 0 },
    ]
  } finally {
    loading.value = false
  }
}

function openAppointment(apt) {
  // Future: open appointment detail bottom sheet
}

function onAppointmentCreated() {
  showBooking.value = false
  loadData()
}

onMounted(loadData)
</script>
