<template>
  <div
    class="flex items-center gap-3 bg-boon-surface rounded-xl px-3 py-3 cursor-pointer transition-colors duration-200 active:bg-gray-50 mb-2"
    @click="$emit('tap', item)"
  >
    <Avatar :name="displayName" />
    <div class="flex-1 min-w-0">
      <div class="flex items-center justify-between gap-2">
        <p class="text-sm font-semibold text-boon-text-primary truncate">{{ displayName }}</p>
        <span
          :class="[
            'text-[10px] font-bold px-1.5 py-0.5 rounded',
            item._badge === 'DEAL'
              ? 'bg-blue-100 text-blue-800'
              : 'bg-pink-100 text-pink-800',
          ]"
        >
          {{ item._badge }}<span v-if="item._badge === 'DEAL' && item.deal_value">
            · {{ currencySymbol }}{{ formattedValue }}
          </span>
        </span>
      </div>
      <div class="flex items-center gap-1.5 mt-1 text-[11px] text-boon-text-secondary">
        <span v-if="item.status">{{ item.status }}</span>
        <span v-if="relativeTime">· {{ relativeTime }}</span>
      </div>
    </div>
    <WhatsAppButton
      v-if="item.mobile_no || item.phone"
      :phone="item.mobile_no || item.phone"
      @click.stop
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Avatar from '@/components/common/Avatar.vue'
import WhatsAppButton from '@/components/whatsapp/WhatsAppButton.vue'
import { formatRelative } from '@/utils/formatters'

const props = defineProps({
  item: { type: Object, required: true },
})
defineEmits(['tap'])

const displayName = computed(() => {
  const it = props.item
  return (
    it.lead_name ||
    it.organization ||
    `${it.first_name || ''} ${it.last_name || ''}`.trim() ||
    it.name
  )
})

const currencySymbol = computed(() => {
  if (props.item.currency === 'INR') return '₹'
  if (props.item.currency === 'USD') return '$'
  if (props.item.currency === 'EUR') return '€'
  return ''
})

const formattedValue = computed(() => {
  if (!props.item.deal_value) return ''
  return new Intl.NumberFormat('en-IN').format(Math.round(Number(props.item.deal_value)))
})

const relativeTime = computed(() => {
  if (!props.item.modified) return ''
  return formatRelative(props.item.modified)
})
</script>
