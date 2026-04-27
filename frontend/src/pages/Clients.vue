<template>
  <div class="h-full flex flex-col">
    <div class="px-4 pt-3 pb-2">
      <SearchBar v-model="search" :placeholder="`Search ${term('contact', 'clients')}...`" />
    </div>
    <SegmentPills v-model="activeSegment" :segments="pills" />
    <InfiniteList
      :items="currentItems"
      :loading="currentLoading"
      :has-more="currentHasMore"
      :empty-title="`No ${term('contact', 'clients')} yet`"
      empty-message="Customers will appear here as deals close."
      @load-more="loadMore"
    >
      <template #default="{ item }">
        <ClientCard :client="item" @tap="open" />
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
import ClientCard from '@/components/cards/ClientCard.vue'
import { useClientsStore } from '@/stores/clientsStore'
import { useVertical } from '@/composables/useVertical'

const router = useRouter()
const clientsStore = useClientsStore()
const { config, term } = useVertical()

const search = ref('')
const activeSegment = ref('all')

const segmentDefs = computed(() => config.value?.clients_segments || [
  { key: 'all', label: 'All', filter: null },
])

const pills = computed(() =>
  segmentDefs.value.map((s) => ({
    key: s.key,
    label: s.label,
    count: (clientsStore.segments[s.key]?.items || []).length || null,
  })),
)

const activeFilter = computed(() => segmentDefs.value.find((s) => s.key === activeSegment.value)?.filter)

const currentItems = computed(() => clientsStore.items(activeSegment.value))
const currentLoading = computed(() => (clientsStore.segments[activeSegment.value] || {}).loading)
const currentHasMore = computed(() => (clientsStore.segments[activeSegment.value] || {}).hasMore !== false)

async function load() {
  await clientsStore.loadSegment(activeSegment.value, activeFilter.value, { reset: true, search: search.value })
}

async function loadMore() {
  await clientsStore.loadSegment(activeSegment.value, activeFilter.value, { reset: false, search: search.value })
}

function open(client) {
  router.push(`/person/${encodeURIComponent(client.name)}`)
}

let searchTimer
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(load, 300)
})
watch(activeSegment, load)
onMounted(load)
</script>
