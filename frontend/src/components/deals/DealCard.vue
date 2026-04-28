<template>
  <div class="bg-boon-surface rounded-xl p-4 mb-3 shadow-sm border border-gray-100">
    <div class="flex justify-between items-start">
      <div>
        <p class="text-sm font-semibold text-boon-text-primary">{{ deal.organization || deal.name }}</p>
        <p class="text-xs text-boon-text-secondary mt-0.5">{{ formattedValue }}</p>
      </div>
      <span
        :class="['text-[10px] font-bold px-2 py-0.5 rounded-full', statusClass]"
      >{{ deal.status?.toUpperCase() }}</span>
    </div>
    <StageStepper
      v-if="!isTerminal"
      :stages="stages"
      :current="deal.status"
      @change="onStageChange"
    />
    <div v-if="!isTerminal" class="flex gap-2 mt-3">
      <button
        @click="onStageChange('Won')"
        class="flex-1 py-2 rounded-lg bg-emerald-600 text-white text-xs font-semibold"
      >Mark Won</button>
      <button
        @click="onStageChange('Lost')"
        class="flex-1 py-2 rounded-lg bg-gray-100 text-boon-text-secondary text-xs font-semibold"
      >Mark Lost</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import StageStepper from '@/components/deals/StageStepper.vue'
import { call } from '@/utils/api'

const props = defineProps({
  deal: { type: Object, required: true },
  stages: { type: Array, required: true },
})
const emit = defineEmits(['updated'])

const isTerminal = computed(() => ['Won', 'Lost'].includes(props.deal.status))

const statusClass = computed(() => {
  if (props.deal.status === 'Won') return 'bg-emerald-100 text-emerald-800'
  if (props.deal.status === 'Lost') return 'bg-gray-100 text-gray-600'
  return 'bg-amber-100 text-amber-800'
})

const formattedValue = computed(() => {
  const v = props.deal.deal_value
  if (!v) return ''
  const sym = props.deal.currency === 'INR' ? '₹' : props.deal.currency === 'USD' ? '$' : ''
  return `${sym}${new Intl.NumberFormat('en-IN').format(Math.round(v))}`
})

async function onStageChange(newStatus) {
  if (newStatus === props.deal.status) return
  await call('boonxpress_crm.api.deals.transition_stage', {
    deal_id: props.deal.name,
    new_status: newStatus,
  })
  emit('updated', { ...props.deal, status: newStatus })
}
</script>
