<template>
  <div class="bg-boon-surface px-4 py-3 border-b border-gray-100 sticky top-0 z-20">
    <div class="flex items-center justify-between gap-2">
      <div class="flex items-center gap-3 min-w-0 flex-1">
        <button @click="goBack" class="text-boon-text-secondary -ml-1" aria-label="Back">
          <ChevronLeft :size="22" />
        </button>
        <div class="min-w-0">
          <div class="flex items-center gap-2">
            <h1 class="text-base font-semibold text-boon-text-primary truncate">{{ name }}</h1>
            <span
              v-if="status"
              :class="['text-[10px] font-bold px-1.5 py-0.5 rounded', statusClass]"
            >{{ status }}</span>
          </div>
          <p class="text-[11px] text-boon-text-secondary mt-0.5 truncate">{{ summaryLine }}</p>
        </div>
      </div>
      <KebabMenu :items="menuItems" @select="$emit('action', $event)" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronLeft } from 'lucide-vue-next'
import KebabMenu from '@/components/common/KebabMenu.vue'
import { formatRelative } from '@/utils/formatters'

const props = defineProps({ person: { type: Object, required: true } })
defineEmits(['action'])

const router = useRouter()

const name = computed(() => {
  const p = props.person
  if (p.contact) {
    return (
      `${p.contact.first_name || ''} ${p.contact.last_name || ''}`.trim() ||
      p.contact.name
    )
  }
  if (p.lead) {
    return (
      p.lead.lead_name ||
      `${p.lead.first_name || ''} ${p.lead.last_name || ''}`.trim()
    )
  }
  return p.canonical_id || ''
})

const status = computed(() => {
  const p = props.person
  if (p.deals?.some((d) => d.status === 'Won')) return 'CUSTOMER'
  if (p.deals?.some((d) => !['Won', 'Lost'].includes(d.status))) return 'IN PIPELINE'
  if (p.lead?.status === 'Lost' || p.lead?.status === 'Junk') return 'LOST'
  return 'NEW LEAD'
})

const statusClass = computed(() => {
  const s = status.value
  if (s === 'CUSTOMER') return 'bg-emerald-100 text-emerald-800'
  if (s === 'IN PIPELINE') return 'bg-amber-100 text-amber-800'
  if (s === 'LOST') return 'bg-gray-100 text-gray-600'
  return 'bg-pink-100 text-pink-800'
})

const summaryLine = computed(() => {
  const s = props.person.summary || {}
  const parts = []
  if (s.visit_count) parts.push(`${s.visit_count} ${s.visit_count === 1 ? 'visit' : 'visits'}`)
  if (s.lifetime_value) {
    parts.push(`₹${new Intl.NumberFormat('en-IN').format(Math.round(s.lifetime_value))} lifetime`)
  }
  if (s.last_contact) parts.push(`last ${formatRelative(s.last_contact)}`)
  return parts.join(' · ') || 'No history yet'
})

const menuItems = computed(() => [
  { key: 'edit', label: 'Edit details' },
  { key: 'merge', label: 'Merge with…' },
  { key: 'share', label: 'Share via WhatsApp' },
  { key: 'delete', label: 'Delete', destructive: true },
])

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/')
}
</script>
