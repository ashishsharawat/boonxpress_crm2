<template>
  <div class="h-full overflow-y-auto">
    <div v-if="loading" class="flex items-center justify-center h-full">
      <div class="w-6 h-6 border-2 border-boon-primary border-t-transparent rounded-full animate-spin" />
    </div>
    <div v-else-if="contact" class="pb-6">
      <!-- Back button -->
      <div class="px-4 py-3">
        <button class="flex items-center gap-1 text-sm text-boon-text-secondary cursor-pointer" @click="$router.back()">
          <ChevronLeft :size="18" />
          <span>Back</span>
        </button>
      </div>

      <!-- Profile card -->
      <div class="px-4 mb-4">
        <div class="bg-boon-surface rounded-2xl p-4 text-center">
          <Avatar :name="contact.full_name" size="lg" class="mx-auto mb-2" />
          <h2 class="text-lg font-semibold text-boon-text-primary font-heading">
            {{ contact.full_name || `${contact.first_name || ''} ${contact.last_name || ''}`.trim() }}
          </h2>
          <p v-if="contact.mobile_no" class="text-sm text-boon-text-secondary mt-0.5">
            {{ formatPhone(contact.mobile_no) }}
          </p>
          <p v-if="contact.email_id" class="text-xs text-boon-text-secondary">
            {{ contact.email_id }}
          </p>

          <!-- Quick actions -->
          <div class="flex items-center justify-center gap-3 mt-4">
            <WhatsAppButton :phone="contact.mobile_no" size="md" />
            <a
              v-if="contact.mobile_no"
              :href="`tel:${contact.mobile_no}`"
              class="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center cursor-pointer"
            >
              <Phone :size="18" class="text-blue-600" />
            </a>
          </div>
        </div>
      </div>

      <!-- Vertical-specific fields -->
      <div v-if="extraFields.length" class="px-4 mb-4">
        <div class="bg-boon-surface rounded-2xl p-4">
          <h3 class="text-xs font-semibold text-boon-text-secondary uppercase tracking-wider mb-3">Details</h3>
          <div v-for="field in extraFields" :key="field.fieldname" class="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
            <span class="text-xs text-boon-text-secondary">{{ field.label }}</span>
            <span class="text-sm text-boon-text-primary font-medium">{{ contact[field.fieldname] || '—' }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ChevronLeft, Phone } from 'lucide-vue-next'
import Avatar from '@/components/common/Avatar.vue'
import WhatsAppButton from '@/components/whatsapp/WhatsAppButton.vue'
import { useVertical } from '@/composables/useVertical'
import { getDoc } from '@/utils/api'
import { formatPhone } from '@/utils/formatters'

const props = defineProps({ id: { type: String, required: true } })
const { contactFields } = useVertical()

const contact = ref(null)
const loading = ref(true)

const extraFields = computed(() => contactFields.value || [])

onMounted(async () => {
  try {
    contact.value = await getDoc('Contact', props.id)
  } catch (err) {
    console.error('Failed to load contact:', err)
  } finally {
    loading.value = false
  }
})
</script>
