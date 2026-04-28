<template>
  <div
    class="flex items-center gap-3 bg-boon-surface rounded-xl px-3 py-3 cursor-pointer transition-colors active:bg-gray-50 mb-2"
    @click="$emit('tap', client)"
  >
    <Avatar :name="displayName" />
    <div class="flex-1 min-w-0">
      <div class="flex items-center gap-2 justify-between">
        <p class="text-sm font-semibold text-boon-text-primary truncate">{{ displayName }}</p>
        <span
          v-if="client._tag"
          class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700"
        >{{ client._tag }}</span>
      </div>
      <div class="flex items-center gap-1.5 mt-1 text-[11px] text-boon-text-secondary">
        <span v-if="client._summary">{{ client._summary }}</span>
        <span v-else-if="client.email_id">{{ client.email_id }}</span>
      </div>
    </div>
    <WhatsAppButton
      v-if="phoneNumber"
      :phone="phoneNumber"
      @click.stop
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Avatar from '@/components/common/Avatar.vue'
import WhatsAppButton from '@/components/whatsapp/WhatsAppButton.vue'

const props = defineProps({ client: { type: Object, required: true } })
defineEmits(['tap'])

const displayName = computed(() => {
  const c = props.client
  return `${c.first_name || ''} ${c.last_name || ''}`.trim() || c.name
})

const phoneNumber = computed(() => {
  const c = props.client
  if (c.mobile_no) return c.mobile_no
  if (c.phone_nos && c.phone_nos[0]) return c.phone_nos[0].phone
  return null
})
</script>
