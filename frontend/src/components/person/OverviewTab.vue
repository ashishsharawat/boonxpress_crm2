<template>
  <div class="p-4 space-y-4">
    <div class="bg-boon-surface rounded-xl p-4 grid grid-cols-2 gap-3">
      <div>
        <div class="text-[10px] uppercase font-semibold text-boon-text-secondary">Last contact</div>
        <div class="text-sm font-semibold mt-0.5">{{ lastContact }}</div>
      </div>
      <div>
        <div class="text-[10px] uppercase font-semibold text-boon-text-secondary">Lifetime value</div>
        <div class="text-sm font-semibold mt-0.5">₹{{ formatNum(person.summary?.lifetime_value) }}</div>
      </div>
      <div>
        <div class="text-[10px] uppercase font-semibold text-boon-text-secondary">Pipeline</div>
        <div class="text-sm font-semibold mt-0.5">₹{{ formatNum(person.summary?.pipeline_value) }}</div>
      </div>
      <div>
        <div class="text-[10px] uppercase font-semibold text-boon-text-secondary">Visits</div>
        <div class="text-sm font-semibold mt-0.5">{{ person.summary?.visit_count || 0 }}</div>
      </div>
    </div>

    <button
      v-if="primaryAction"
      class="w-full py-3 rounded-xl bg-boon-primary text-white text-sm font-semibold shadow-sm"
    >{{ primaryAction.label }}</button>

    <div class="grid grid-cols-3 gap-2">
      <button class="py-2.5 rounded-lg bg-boon-surface text-xs font-semibold flex flex-col items-center gap-1">
        <Phone :size="16" /> Call
      </button>
      <button class="py-2.5 rounded-lg bg-emerald-50 text-emerald-700 text-xs font-semibold flex flex-col items-center gap-1">
        <MessageCircle :size="16" /> WhatsApp
      </button>
      <button class="py-2.5 rounded-lg bg-boon-surface text-xs font-semibold flex flex-col items-center gap-1">
        <Calendar :size="16" /> Schedule
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Phone, MessageCircle, Calendar } from 'lucide-vue-next'
import { useVertical } from '@/composables/useVertical'
import { formatRelative } from '@/utils/formatters'

const props = defineProps({ person: { type: Object, required: true } })
defineEmits(['refresh'])

const { config } = useVertical()
const primaryAction = computed(() => config.value?.person_primary_action)

const lastContact = computed(() => {
  const lc = props.person.summary?.last_contact
  return lc ? formatRelative(lc) : 'Never'
})

function formatNum(n) {
  return new Intl.NumberFormat('en-IN').format(Math.round(Number(n) || 0))
}
</script>
