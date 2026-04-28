<template>
  <div>
    <ActivityFilterChips v-model="filter" :chips="chips" />
    <div v-if="loading" class="p-4 space-y-2">
      <SkeletonCard v-for="i in 4" :key="i" />
    </div>
    <EmptyState
      v-else-if="!groups.length"
      title="No activity yet"
      message="Calls, messages, and stage changes will appear here."
    />
    <div v-else>
      <div v-for="group in groups" :key="group.day">
        <div class="px-4 pt-3 pb-1 text-[10px] uppercase font-semibold text-boon-text-secondary">{{ group.day }}</div>
        <ActivityEventCard
          v-for="event in group.events"
          :key="event.id"
          :event="event"
          @tap="onEventTap"
        />
      </div>
      <button
        v-if="hasMore"
        @click="loadMore"
        class="w-full py-3 text-sm font-semibold text-boon-primary"
      >Load older activity</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useActivityStore } from '@/stores/activityStore'
import ActivityFilterChips from '@/components/person/ActivityFilterChips.vue'
import ActivityEventCard from '@/components/person/ActivityEventCard.vue'
import SkeletonCard from '@/components/lists/SkeletonCard.vue'
import EmptyState from '@/components/lists/EmptyState.vue'

const props = defineProps({ person: { type: Object, required: true } })
defineEmits(['refresh'])

const filter = ref('all')
const store = useActivityStore()

const chips = [
  { key: 'all', label: 'All' },
  { key: 'messages', label: 'Messages' },
  { key: 'calls', label: 'Calls' },
  { key: 'stage', label: 'Stage' },
  { key: 'notes', label: 'Notes' },
  { key: 'appointments', label: 'Appointments' },
]

const events = computed(() => store.events(props.person.canonical_id, filter.value))
const feedKey = computed(() => `${props.person.canonical_id}::${filter.value}`)
const loading = computed(() => (store.feeds[feedKey.value] || {}).loading)
const hasMore = computed(() => !!(store.feeds[feedKey.value] || {}).nextCursor)

const groups = computed(() => {
  const out = []
  let curDay = null
  for (const ev of events.value) {
    const day = formatDay(ev.timestamp)
    if (day !== curDay) {
      out.push({ day, events: [] })
      curDay = day
    }
    out[out.length - 1].events.push(ev)
  }
  return out
})

function formatDay(iso) {
  const d = new Date(iso)
  const today = new Date()
  const yest = new Date()
  yest.setDate(yest.getDate() - 1)
  if (sameDay(d, today)) return 'Today'
  if (sameDay(d, yest)) return 'Yesterday'
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}
function sameDay(a, b) {
  return a.toDateString() === b.toDateString()
}

async function load() {
  await store.loadFeed(props.person.canonical_id, filter.value)
}

async function loadMore() {
  await store.loadMore(props.person.canonical_id, filter.value)
}

function onEventTap(event) {
  // Drill-in handlers wired in a later pass; this hook keeps the contract.
}

onMounted(load)
watch(filter, load)
</script>
