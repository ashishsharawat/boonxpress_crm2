<template>
  <div class="h-full flex flex-col bg-boon-bg">
    <PersonHeader v-if="person" :person="person" @action="onAction" />
    <PersonTabs v-if="person" v-model="activeTab" :tabs="tabs" />

    <div v-if="loading" class="p-4 space-y-2">
      <SkeletonCard v-for="i in 3" :key="i" />
    </div>

    <EmptyState
      v-else-if="error"
      :title="errorTitle"
      :message="errorMessage"
    />

    <div v-else-if="person" class="flex-1 overflow-y-auto">
      <component :is="tabComponent" :person="person" @refresh="reload" />
    </div>

    <DeleteConfirmModal v-model="showDelete" @confirmed="doDelete" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useIdentityResolver } from '@/composables/useIdentityResolver'
import { usePersonStore } from '@/stores/personStore'
import { softDelete } from '@/utils/api'
import PersonHeader from '@/components/person/PersonHeader.vue'
import PersonTabs from '@/components/person/PersonTabs.vue'
import OverviewTab from '@/components/person/OverviewTab.vue'
import ActivityTab from '@/components/person/ActivityTab.vue'
import DealsTab from '@/components/person/DealsTab.vue'
import NotesTab from '@/components/person/NotesTab.vue'
import ProfileTab from '@/components/person/ProfileTab.vue'
import SkeletonCard from '@/components/lists/SkeletonCard.vue'
import EmptyState from '@/components/lists/EmptyState.vue'
import DeleteConfirmModal from '@/components/common/DeleteConfirmModal.vue'

const props = defineProps({ id: { type: String, required: true } })

const router = useRouter()
const personStore = usePersonStore()
const { resolve } = useIdentityResolver()

const person = ref(null)
const loading = ref(true)
const error = ref(null)
const activeTab = ref('overview')
const showDelete = ref(false)

const errorTitle = computed(() => (error.value === '404' ? 'Not found' : 'Something went wrong'))
const errorMessage = computed(() => (error.value === '404'
  ? "Couldn't find this person — it may have been deleted."
  : 'Try refreshing the page.'))

const tabs = computed(() => [
  { key: 'overview', label: 'Overview', count: null },
  { key: 'activity', label: 'Activity', count: null },
  { key: 'deals', label: 'Deals', count: person.value?.deals?.length || null },
  { key: 'notes', label: 'Notes', count: null },
  { key: 'profile', label: 'Profile', count: null },
])

const tabComponent = computed(() => {
  switch (activeTab.value) {
    case 'overview': return OverviewTab
    case 'activity': return ActivityTab
    case 'deals': return DealsTab
    case 'notes': return NotesTab
    case 'profile': return ProfileTab
    default: return OverviewTab
  }
})

async function load() {
  loading.value = true
  error.value = null
  try {
    person.value = await resolve(props.id)
  } catch (e) {
    error.value = e.message?.includes('404') || e.message?.includes('DoesNotExist') ? '404' : 'error'
  } finally {
    loading.value = false
  }
}

async function reload() {
  personStore.invalidate(props.id)
  await load()
}

async function onAction(actionKey) {
  if (actionKey === 'delete') {
    showDelete.value = true
  }
  // 'edit', 'merge', 'share' wired in subsequent polish passes
}

async function doDelete() {
  if (!person.value) return
  let target, doctype
  if (person.value.lead) {
    target = person.value.lead
    doctype = 'CRM Lead'
  } else if (person.value.deals?.length) {
    target = person.value.deals[0]
    doctype = 'CRM Deal'
  } else if (person.value.contact) {
    target = person.value.contact
    doctype = 'Contact'
  }
  if (!target) return
  await softDelete(doctype, target.name)
  router.back()
}

onMounted(load)
watch(() => props.id, load)
</script>
