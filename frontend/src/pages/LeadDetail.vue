<template>
  <div class="h-full overflow-y-auto">
    <div v-if="loading" class="flex items-center justify-center h-full">
      <div class="w-6 h-6 border-2 border-boon-primary border-t-transparent rounded-full animate-spin" />
    </div>
    <div v-else-if="lead" class="pb-6">
      <div class="px-4 py-3">
        <button class="flex items-center gap-1 text-sm text-boon-text-secondary cursor-pointer" @click="$router.back()">
          <ChevronLeft :size="18" /><span>Back</span>
        </button>
      </div>
      <div class="px-4 mb-4">
        <div class="bg-boon-surface rounded-2xl p-4 text-center">
          <Avatar :name="lead.lead_name || lead.first_name" size="lg" class="mx-auto mb-2" />
          <h2 class="text-lg font-semibold text-boon-text-primary font-heading">{{ lead.lead_name }}</h2>
          <div class="flex items-center justify-center gap-2 mt-1">
            <StatusBadge v-if="lead.status" :status="lead.status" />
            <span v-if="lead.source" class="text-xs text-boon-text-secondary">via {{ lead.source }}</span>
          </div>
          <p v-if="lead.mobile_no" class="text-sm text-boon-text-secondary mt-2">{{ formatPhone(lead.mobile_no) }}</p>
          <div class="flex items-center justify-center gap-3 mt-4">
            <WhatsAppButton :phone="lead.mobile_no || lead.phone" />
            <a v-if="lead.mobile_no" :href="`tel:${lead.mobile_no}`" class="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center cursor-pointer">
              <Phone :size="18" class="text-blue-600" />
            </a>
          </div>
        </div>
      </div>
      <!-- Lead-specific extra fields from vertical config -->
      <div v-if="extraFields.length" class="px-4 mb-4">
        <div class="bg-boon-surface rounded-2xl p-4">
          <h3 class="text-xs font-semibold text-boon-text-secondary uppercase tracking-wider mb-3">Details</h3>
          <div v-for="field in extraFields" :key="field.fieldname" class="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
            <span class="text-xs text-boon-text-secondary">{{ field.label }}</span>
            <span class="text-sm text-boon-text-primary font-medium">{{ lead[field.fieldname] || '—' }}</span>
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
import StatusBadge from '@/components/common/StatusBadge.vue'
import WhatsAppButton from '@/components/whatsapp/WhatsAppButton.vue'
import { useVertical } from '@/composables/useVertical'
import { getDoc } from '@/utils/api'
import { formatPhone } from '@/utils/formatters'

const props = defineProps({ id: { type: String, required: true } })
const { leadFields } = useVertical()
const lead = ref(null)
const loading = ref(true)
const extraFields = computed(() => leadFields.value || [])

onMounted(async () => {
  try { lead.value = await getDoc('CRM Lead', props.id) }
  catch (err) { console.error('Failed to load lead:', err) }
  finally { loading.value = false }
})
</script>
