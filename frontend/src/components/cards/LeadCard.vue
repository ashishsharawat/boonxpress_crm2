<template>
  <div class="flex items-center gap-3 bg-boon-surface rounded-xl px-3 py-3 cursor-pointer transition-colors duration-200 active:bg-gray-50"
       @click="$emit('tap', lead)">
    <Avatar :name="lead.lead_name || lead.first_name" />
    <div class="flex-1 min-w-0">
      <p class="text-sm font-semibold text-boon-text-primary truncate">
        {{ lead.lead_name || `${lead.first_name || ''} ${lead.last_name || ''}`.trim() }}
      </p>
      <div class="flex items-center gap-1.5 mt-1">
        <StatusBadge v-if="lead.status" :status="lead.status" />
        <span v-if="lead.source" class="text-[10px] text-boon-text-secondary bg-boon-surface-alt px-1.5 py-0.5 rounded">
          {{ lead.source }}
        </span>
      </div>
    </div>
    <WhatsAppButton
      :phone="lead.mobile_no || lead.phone"
      @click.stop
    />
  </div>
</template>

<script setup>
import Avatar from '@/components/common/Avatar.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import WhatsAppButton from '@/components/whatsapp/WhatsAppButton.vue'

defineProps({
  lead: { type: Object, required: true },
})
defineEmits(['tap'])
</script>
