<template>
  <div class="flex items-center gap-3 bg-boon-surface rounded-xl px-3 py-3 cursor-pointer transition-colors duration-200 active:bg-gray-50"
       @click="$emit('tap', contact)">
    <Avatar :name="contact.full_name || contact.first_name" />
    <div class="flex-1 min-w-0">
      <p class="text-sm font-semibold text-boon-text-primary truncate">
        {{ contact.full_name || `${contact.first_name || ''} ${contact.last_name || ''}`.trim() }}
      </p>
      <p class="text-xs text-boon-text-secondary mt-0.5 truncate">
        <span v-if="contact.mobile_no">{{ formatPhone(contact.mobile_no) }}</span>
        <span v-if="contact.modified" class="ml-2">{{ formatRelativeDate(contact.modified) }}</span>
      </p>
      <div v-if="extraInfo" class="mt-1">
        <span class="text-[10px] text-boon-text-secondary bg-boon-surface-alt px-1.5 py-0.5 rounded">
          {{ extraInfo }}
        </span>
      </div>
    </div>
    <WhatsAppButton
      :phone="contact.mobile_no"
      @click.stop
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Avatar from '@/components/common/Avatar.vue'
import WhatsAppButton from '@/components/whatsapp/WhatsAppButton.vue'
import { formatPhone, formatRelativeDate } from '@/utils/formatters'
import { useVertical } from '@/composables/useVertical'

const props = defineProps({
  contact: { type: Object, required: true },
})

defineEmits(['tap'])

const { contactFields } = useVertical()

const extraInfo = computed(() => {
  if (!contactFields.value?.length) return null
  const field = contactFields.value[0]
  return props.contact[field.fieldname] || null
})
</script>
