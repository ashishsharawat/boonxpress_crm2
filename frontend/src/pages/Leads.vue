<template>
  <div class="h-full flex flex-col">
    <div class="px-4 pt-3 pb-2">
      <SearchBar v-model="search" :placeholder="`Search ${term('lead', 'leads')}...`" />
    </div>
    <SegmentPills v-model="activeSegment" :segments="pills" />
    <InfiniteList
      :items="currentItems"
      :loading="currentLoading"
      :has-more="currentHasMore"
      :empty-title="`No ${currentLabel.toLowerCase()} yet`"
      :empty-message="emptyMessage"
      @load-more="loadMore"
    >
      <template #default="{ item }">
        <ProspectCard :item="item" @tap="open" />
      </template>
    </InfiniteList>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import SearchBar from '@/components/common/SearchBar.vue'
import SegmentPills from '@/components/common/SegmentPills.vue'
import InfiniteList from '@/components/lists/InfiniteList.vue'
import ProspectCard from '@/components/cards/ProspectCard.vue'
import { useLeadsStore } from '@/stores/leadsStore'
import { useVertical } from '@/composables/useVertical'

const router = useRouter()
const leadsStore = useLeadsStore()
const { config, term } = useVertical()

const search = ref('')
const activeSegment = ref('new')

const segmentDefs = computed(() => config.value?.leads_segments || [
  { key: 'new', label: 'New', filter: { doctype: 'CRM Lead', status_in: ['Open', 'Replied'] } },
  { key: 'pipeline', label: 'Pipeline', filter: { doctype: 'CRM Deal', status_not_in: ['Won', 'Lost'] } },
  { key: 'closed', label: 'Closed', filter: { doctype: '*', status_in: ['Lost'] } },
])

const pills = computed(() =>
  segmentDefs.value.map((s) => ({
    key: s.key,
    label: s.label,
    count: (leadsStore.segments[s.key]?.items || []).length || null,
  })),
)

const activeFilter = computed(() => segmentDefs.value.find((s) => s.key === activeSegment.value)?.filter)

const currentItems = computed(() => leadsStore.items(activeSegment.value))
const currentLoading = computed(() => (leadsStore.segments[activeSegment.value] || {}).loading)
const currentHasMore = computed(() => (leadsStore.segments[activeSegment.value] || {}).hasMore !== false)
const currentLabel = computed(() => pills.value.find((p) => p.key === activeSegment.value)?.label || 'leads')

const emptyMessage = computed(() => {
  if (activeSegment.value === 'new') return 'New enquiries will appear here.'
  if (activeSegment.value === 'pipeline') return 'Active deals will appear here once leads convert.'
  return 'Lost or cancelled deals will appear here.'
})

async function load() {
  if (!activeFilter.value) return
  await leadsStore.loadSegment(activeSegment.value, activeFilter.value, { reset: true, search: search.value })
}

async function loadMore() {
  if (!activeFilter.value) return
  await leadsStore.loadSegment(activeSegment.value, activeFilter.value, { reset: false, search: search.value })
}

function open(item) {
  router.push(`/person/${encodeURIComponent(item.name)}`)
}

let searchTimer
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(load, 300)
})

watch(activeSegment, load)
onMounted(load)
</script>
