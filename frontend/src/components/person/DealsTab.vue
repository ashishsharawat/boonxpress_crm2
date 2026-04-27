<template>
  <div class="p-4">
    <EmptyState
      v-if="!deals.length"
      title="No deals"
      message="Deals will appear here once a quote or pipeline is started."
    />
    <DealCard
      v-for="deal in sortedDeals"
      :key="deal.name"
      :deal="deal"
      :stages="stages"
      @updated="onUpdate"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import DealCard from '@/components/deals/DealCard.vue'
import EmptyState from '@/components/lists/EmptyState.vue'
import { useVertical } from '@/composables/useVertical'

const props = defineProps({ person: { type: Object, required: true } })
const emit = defineEmits(['refresh'])

const { config } = useVertical()
const stages = computed(() => config.value?.deal_stages || ['Qualification', 'Demo', 'Proposal', 'Negotiation'])

const deals = computed(() => props.person.deals || [])
const sortedDeals = computed(() => {
  const order = { Qualification: 1, Demo: 2, Proposal: 3, Negotiation: 4, Won: 5, Lost: 6 }
  return [...deals.value].sort((a, b) => (order[a.status] || 99) - (order[b.status] || 99))
})

function onUpdate() {
  emit('refresh')
}
</script>
