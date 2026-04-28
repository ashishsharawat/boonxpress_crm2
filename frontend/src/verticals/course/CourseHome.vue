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

    <!-- Enquiries (active counselling) -->
    <div class="px-4 py-2">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-sm font-semibold text-boon-text-primary font-heading">New Enquiries</h2>
        <button
          v-if="!loadingLeads && newEnquiries.length"
          class="text-xs font-medium text-boon-primary"
          @click="goToLeads"
        >View all</button>
      </div>

      <div v-if="loadingLeads" class="space-y-2">
        <SkeletonCard v-for="i in 3" :key="i" />
      </div>

      <div v-else-if="newEnquiries.length" class="space-y-2">
        <ProspectCard
          v-for="item in newEnquiries"
          :key="item.name"
          :item="item"
          @tap="open"
        />
      </div>

      <EmptyState
        v-else
        title="No new enquiries"
        message="Tap + to log a new enquiry or enrollment."
      />
    </div>

    <!-- Active enrollments (deals in pipeline) -->
    <div v-if="activeEnrollments.length || loadingDeals" class="px-4 py-2">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-sm font-semibold text-boon-text-primary font-heading">Active Enrollments</h2>
      </div>

      <div v-if="loadingDeals" class="space-y-2">
        <SkeletonCard v-for="i in 2" :key="i" />
      </div>

      <div v-else class="space-y-2">
        <ProspectCard
          v-for="item in activeEnrollments"
          :key="item.name"
          :item="item"
          @tap="open"
        />
      </div>
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

    <NewEnquirySheet v-model="showEnquirySheet" @saved="onEnquirySaved" />
    <SendQuoteSheet v-model="showEnrollSheet" @saved="onEnrollSaved" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import QuickStatsBar from '@/components/stats/QuickStatsBar.vue'
import ProspectCard from '@/components/cards/ProspectCard.vue'
import SkeletonCard from '@/components/lists/SkeletonCard.vue'
import EmptyState from '@/components/lists/EmptyState.vue'
import NewEnquirySheet from '@/verticals/salon/NewEnquirySheet.vue'
// Course's "New Enrollment" reuses the same Deal-creation sheet as Used Car —
// the underlying flow is identical (create CRM Deal with stage from config).
// Vertical-specific naming is supplied by vertical_config.deal_stages.
import SendQuoteSheet from '@/verticals/usedcar/SendQuoteSheet.vue'
import { useVertical } from '@/composables/useVertical'
import { useSessionStore } from '@/stores/session'
import { onFabAction } from '@/composables/useFabBus'
import { call, getList } from '@/utils/api'
import { formatRelative } from '@/utils/formatters'

const router = useRouter()
const { config } = useVertical()
const session = useSessionStore()

const loadingLeads = ref(true)
const loadingDeals = ref(true)
const newEnquiries = ref([])
const activeEnrollments = ref([])
const stats = ref({})
const recentActivity = ref([])
const showEnquirySheet = ref(false)
const showEnrollSheet = ref(false)

const businessName = computed(() => config.value?.business_name || config.value?.display_name || 'Course')
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
  if (action === 'create_lead') showEnquirySheet.value = true
  else if (action === 'create_deal') showEnrollSheet.value = true
})

async function loadData() {
  loadingLeads.value = true
  loadingDeals.value = true
  try {
    const [leadsData, dealsData, statsData, activityData] = await Promise.all([
      getList('CRM Lead', {
        fields: ['name', 'first_name', 'last_name', 'mobile_no', 'source', 'status', 'modified'],
        filters: [['status', 'in', ['New', 'Contacted', 'Nurture']]],
        orderBy: 'modified desc',
        pageLength: 5,
      }).catch(() => []),
      getList('CRM Deal', {
        fields: ['name', 'organization', 'deal_value', 'currency', 'status', 'modified'],
        filters: [['status', 'not in', ['Won', 'Lost']]],
        orderBy: 'modified desc',
        pageLength: 5,
      }).catch(() => []),
      call('boonxpress_crm.api.stats.get_quick_stats').catch(() => ({})),
      call('boonxpress_crm.api.stats.get_recent_activity', { limit: 3 }).catch(() => []),
    ])
    newEnquiries.value = leadsData.map((d) => ({ ...d, doctype: 'CRM Lead', _badge: 'ENQUIRY' }))
    activeEnrollments.value = dealsData.map((d) => ({ ...d, doctype: 'CRM Deal', _badge: 'ENROLL' }))
    stats.value = statsData || {}
    recentActivity.value = activityData || []
  } finally {
    loadingLeads.value = false
    loadingDeals.value = false
  }
}

function open(item) {
  router.push(`/person/${encodeURIComponent(item.name)}`)
}

function goToLeads() {
  router.push('/leads')
}

function onEnquirySaved(lead) {
  if (lead?.name) router.push(`/person/${encodeURIComponent(lead.name)}`)
  else loadData()
}

function onEnrollSaved() {
  loadData()
}

onMounted(loadData)
</script>
