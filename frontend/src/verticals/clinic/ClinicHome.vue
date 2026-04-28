<template>
  <div class="h-full overflow-y-auto pb-24">
    <div class="px-4 pt-3 pb-2">
      <h1 class="text-base font-bold text-boon-text-primary leading-tight">
        {{ greeting }}<span v-if="firstName">, {{ firstName }}</span>
      </h1>
      <p class="text-xs text-boon-text-secondary mt-0.5">
        {{ businessName }} · {{ todayLabel }}
      </p>
    </div>

    <QuickStatsBar :stats="statsData" />

    <div class="px-4 py-2">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-sm font-semibold text-boon-text-primary font-heading">Today's Consultations</h2>
        <button
          v-if="!loading && appointments.length"
          class="text-xs font-medium text-boon-primary"
          @click="openCreateAppointment"
        >+ New</button>
      </div>

      <div v-if="loading" class="space-y-2">
        <SkeletonCard v-for="i in 4" :key="i" />
      </div>

      <div v-else-if="appointments.length" class="space-y-2">
        <AppointmentCard
          v-for="apt in appointments"
          :key="apt.name"
          :appointment="apt"
          @tap="openEditAppointment"
        />
      </div>

      <EmptyState
        v-else
        title="No consultations today"
        message="Tap + to book a consultation or use the FAB."
      />
    </div>

    <div v-if="recentActivity.length" class="px-4 py-2">
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-sm font-semibold text-boon-text-primary font-heading">Recent activity</h2>
      </div>
      <div class="bg-boon-surface rounded-xl">
        <div
          v-for="ev in recentActivity"
          :key="ev.id"
          class="px-3 py-2 border-b border-gray-100 last:border-b-0 flex justify-between gap-2"
        >
          <span class="text-xs text-boon-text-primary truncate">{{ ev.summary }}</span>
          <span class="text-[10px] text-boon-text-secondary shrink-0">{{ formatRelative(ev.timestamp) }}</span>
        </div>
      </div>
    </div>

    <BookAppointment
      v-model="showAppointmentSheet"
      :appointment="editingAppointment"
      @saved="onAppointmentSaved"
    />
    <NewEnquirySheet
      v-model="showEnquirySheet"
      @saved="onEnquirySaved"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import QuickStatsBar from '@/components/stats/QuickStatsBar.vue'
import AppointmentCard from '@/components/cards/AppointmentCard.vue'
import SkeletonCard from '@/components/lists/SkeletonCard.vue'
import EmptyState from '@/components/lists/EmptyState.vue'
import BookAppointment from '@/verticals/salon/BookAppointment.vue'
import NewEnquirySheet from '@/verticals/salon/NewEnquirySheet.vue'
import { useVertical } from '@/composables/useVertical'
import { useSessionStore } from '@/stores/session'
import { onFabAction } from '@/composables/useFabBus'
import { call } from '@/utils/api'
import { formatRelative } from '@/utils/formatters'

const router = useRouter()
const { config } = useVertical()
const session = useSessionStore()

const loading = ref(true)
const appointments = ref([])
const stats = ref({})
const recentActivity = ref([])
const showAppointmentSheet = ref(false)
const showEnquirySheet = ref(false)
const editingAppointment = ref(null)

const businessName = computed(() => config.value?.business_name || config.value?.display_name || 'Clinic')
const firstName = computed(() => (session.fullName || '').split(' ')[0] || '')
const todayLabel = computed(() => new Date().toLocaleDateString('en-IN', { weekday: 'long', month: 'short', day: 'numeric' }))

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
})

const statsData = computed(() => {
  const cfg = config.value?.stats_config || []
  return cfg.map((s) => ({
    key: s.key,
    label: s.label,
    icon: s.icon,
    value: stats.value?.[s.key] ?? 0,
  }))
})

onFabAction((action) => {
  if (action === 'create_appointment') openCreateAppointment()
  else if (action === 'create_lead') showEnquirySheet.value = true
})

async function loadData() {
  loading.value = true
  try {
    const [aptsData, statsData, activityData] = await Promise.all([
      call('boonxpress_crm.api.appointments.get_today').catch(() => []),
      call('boonxpress_crm.api.stats.get_quick_stats').catch(() => ({})),
      call('boonxpress_crm.api.stats.get_recent_activity', { limit: 3 }).catch(() => []),
    ])
    appointments.value = aptsData || []
    stats.value = statsData || {}
    recentActivity.value = activityData || []
  } finally {
    loading.value = false
  }
}

function openCreateAppointment() {
  editingAppointment.value = null
  showAppointmentSheet.value = true
}

function openEditAppointment(apt) {
  editingAppointment.value = apt
  showAppointmentSheet.value = true
}

function onAppointmentSaved() {
  editingAppointment.value = null
  loadData()
}

function onEnquirySaved(lead) {
  if (lead?.name) {
    router.push(`/person/${encodeURIComponent(lead.name)}`)
  } else {
    loadData()
  }
}

onMounted(loadData)
</script>
