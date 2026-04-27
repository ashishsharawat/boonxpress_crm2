<template>
  <div class="h-full flex flex-col">
    <div class="px-4 pt-3 pb-2">
      <SearchBar v-model="search" :placeholder="`Search ${term('contact', 'Contacts')}...`" />
    </div>
    <InfiniteList
      :items="contacts"
      :loading="loading"
      :has-more="hasMore"
      :empty-title="`No ${term('contact', 'contacts')} yet`"
      :empty-message="`Add your first ${term('contact', 'contact')} to get started.`"
      @load-more="loadMore"
    >
      <template #default="{ item }">
        <ContactCard :contact="item" @tap="openContact" />
      </template>
    </InfiniteList>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import SearchBar from '@/components/common/SearchBar.vue'
import InfiniteList from '@/components/lists/InfiniteList.vue'
import ContactCard from '@/components/cards/ContactCard.vue'
import { useVertical } from '@/composables/useVertical'
import { getList } from '@/utils/api'
import { PAGE_SIZE } from '@/utils/constants'

const router = useRouter()
const { term } = useVertical()

const contacts = ref([])
const loading = ref(false)
const hasMore = ref(true)
const search = ref('')
let start = 0

async function fetchContacts(reset = false) {
  if (loading.value) return
  loading.value = true
  if (reset) {
    start = 0
    contacts.value = []
    hasMore.value = true
  }
  try {
    const filters = search.value
      ? [['full_name', 'like', `%${search.value}%`]]
      : []
    const data = await getList('Contact', {
      fields: ['name', 'first_name', 'last_name', 'full_name', 'mobile_no', 'email_id', 'modified'],
      filters,
      orderBy: 'modified desc',
      pageLength: PAGE_SIZE,
      start,
    })
    contacts.value = reset ? data : [...contacts.value, ...data]
    hasMore.value = data.length === PAGE_SIZE
    start += data.length
  } catch (err) {
    console.error('Failed to load contacts:', err)
  } finally {
    loading.value = false
  }
}

function loadMore() {
  fetchContacts(false)
}

function openContact(contact) {
  router.push({ name: 'ClientDetail', params: { id: contact.name } })
}

watch(search, () => fetchContacts(true))
onMounted(() => fetchContacts(true))
</script>
