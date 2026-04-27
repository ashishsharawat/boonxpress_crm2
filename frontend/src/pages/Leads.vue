<template>
  <div class="h-full flex flex-col">
    <div class="px-4 pt-3 pb-2">
      <SearchBar v-model="search" :placeholder="`Search ${term('lead', 'Leads')}...`" />
    </div>
    <InfiniteList
      :items="leads"
      :loading="loading"
      :has-more="hasMore"
      :empty-title="`No ${term('lead', 'leads')} yet`"
      :empty-message="`New ${term('lead', 'leads')} will appear here automatically.`"
      @load-more="loadMore"
    >
      <template #default="{ item }">
        <LeadCard :lead="item" @tap="openLead" />
      </template>
    </InfiniteList>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import SearchBar from '@/components/common/SearchBar.vue'
import InfiniteList from '@/components/lists/InfiniteList.vue'
import LeadCard from '@/components/cards/LeadCard.vue'
import { useVertical } from '@/composables/useVertical'
import { getList } from '@/utils/api'
import { PAGE_SIZE } from '@/utils/constants'

const router = useRouter()
const { term } = useVertical()

const leads = ref([])
const loading = ref(false)
const hasMore = ref(true)
const search = ref('')
let start = 0

async function fetchLeads(reset = false) {
  if (loading.value) return
  loading.value = true
  if (reset) {
    start = 0
    leads.value = []
    hasMore.value = true
  }
  try {
    const filters = search.value
      ? [['lead_name', 'like', `%${search.value}%`]]
      : []
    const data = await getList('CRM Lead', {
      fields: ['name', 'first_name', 'last_name', 'lead_name', 'mobile_no', 'phone', 'email_id', 'source', 'status', 'modified'],
      filters,
      orderBy: 'modified desc',
      pageLength: PAGE_SIZE,
      start,
    })
    leads.value = reset ? data : [...leads.value, ...data]
    hasMore.value = data.length === PAGE_SIZE
    start += data.length
  } catch (err) {
    console.error('Failed to load leads:', err)
  } finally {
    loading.value = false
  }
}

function loadMore() { fetchLeads(false) }
function openLead(lead) { router.push({ name: 'LeadDetail', params: { id: lead.name } }) }

watch(search, () => fetchLeads(true))
onMounted(() => fetchLeads(true))
</script>
