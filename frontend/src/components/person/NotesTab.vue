<template>
  <div class="p-4">
    <div v-if="loading" class="space-y-2">
      <SkeletonCard v-for="i in 3" :key="i" />
    </div>
    <EmptyState
      v-else-if="!notes.length"
      title="No notes yet"
      message="Tap the + button to add the first note."
    />
    <ul v-else class="space-y-2">
      <li
        v-for="note in notes"
        :key="note.name"
        class="bg-boon-surface rounded-lg p-3"
      >
        <p class="text-sm text-boon-text-primary whitespace-pre-line">{{ note.content }}</p>
        <p class="text-[10px] text-boon-text-secondary mt-1">{{ formatRelative(note.creation) }} · {{ note.owner }}</p>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { call } from '@/utils/api'
import EmptyState from '@/components/lists/EmptyState.vue'
import SkeletonCard from '@/components/lists/SkeletonCard.vue'
import { formatRelative } from '@/utils/formatters'

const props = defineProps({ person: { type: Object, required: true } })
defineEmits(['refresh'])

const notes = ref([])
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    const result = await call('boonxpress_crm.api.activity.get_feed', {
      person_id: props.person.canonical_id,
      filter_type: 'notes',
      page_size: 100,
    })
    notes.value = (result.events || []).map((e) => ({
      name: e.id,
      content: e.content,
      creation: e.timestamp,
      owner: e.owner,
    }))
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
