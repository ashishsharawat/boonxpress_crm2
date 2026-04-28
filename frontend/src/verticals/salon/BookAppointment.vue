<template>
  <BottomSheet v-model="isOpen" :title="sheetTitle">
    <div class="space-y-4">
      <!-- Client search (or pre-selected if editing / from PersonDetail) -->
      <div v-if="!lockedClient">
        <label class="text-xs font-medium text-boon-text-secondary mb-1 block">Client</label>
        <SearchBar v-model="clientSearch" placeholder="Search client..." />
        <div v-if="clientResults.length" class="mt-1 bg-white border border-gray-200 rounded-xl max-h-32 overflow-y-auto">
          <button
            v-for="c in clientResults"
            :key="c.name"
            class="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 cursor-pointer"
            @click="selectClient(c)"
          >
            {{ c.full_name || c.first_name }}
          </button>
        </div>
        <p v-if="selectedClient" class="text-xs text-boon-primary mt-1">
          Selected: {{ selectedClient.full_name || selectedClient.first_name }}
        </p>
      </div>
      <div v-else class="bg-boon-surface-alt rounded-xl px-3 py-2">
        <div class="text-xs text-boon-text-secondary">Client</div>
        <div class="text-sm font-semibold">{{ selectedClient?.full_name || selectedClient?.first_name }}</div>
      </div>

      <div>
        <label class="text-xs font-medium text-boon-text-secondary mb-1 block">Service</label>
        <select
          v-model="serviceType"
          class="w-full h-10 px-3 text-sm bg-boon-surface border border-gray-200 rounded-xl text-boon-text-primary focus:outline-none focus:ring-2 focus:ring-boon-primary/30"
        >
          <option value="">Select service...</option>
          <option v-for="s in services" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>

      <div>
        <label class="text-xs font-medium text-boon-text-secondary mb-1 block">Date</label>
        <input
          v-model="date"
          type="date"
          class="w-full h-10 px-3 text-sm bg-boon-surface border border-gray-200 rounded-xl text-boon-text-primary focus:outline-none focus:ring-2 focus:ring-boon-primary/30"
        />
      </div>

      <div>
        <label class="text-xs font-medium text-boon-text-secondary mb-1 block">Time</label>
        <select
          v-model="timeSlot"
          class="w-full h-10 px-3 text-sm bg-boon-surface border border-gray-200 rounded-xl text-boon-text-primary focus:outline-none focus:ring-2 focus:ring-boon-primary/30"
        >
          <option value="">Select time...</option>
          <option v-for="t in timeOptions" :key="t" :value="t">{{ formatTimeOption(t) }}</option>
        </select>
      </div>

      <div v-if="isEditMode">
        <label class="text-xs font-medium text-boon-text-secondary mb-1 block">Status</label>
        <select
          v-model="status"
          class="w-full h-10 px-3 text-sm bg-boon-surface border border-gray-200 rounded-xl text-boon-text-primary focus:outline-none focus:ring-2 focus:ring-boon-primary/30"
        >
          <option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>

      <p v-if="error" class="text-xs text-red-600">{{ error }}</p>

      <TouchButton
        variant="primary"
        class="w-full"
        :loading="saving"
        :disabled="!canSubmit"
        @click="submit"
      >
        {{ submitLabel }}
      </TouchButton>
    </div>
  </BottomSheet>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import BottomSheet from '@/components/common/BottomSheet.vue'
import SearchBar from '@/components/common/SearchBar.vue'
import TouchButton from '@/components/common/TouchButton.vue'
import { useVertical } from '@/composables/useVertical'
import { getList, createDoc, call, setValue } from '@/utils/api'

const props = defineProps({
  modelValue: Boolean,
  // Edit mode: pass an existing appointment doc to edit; create mode: omit
  appointment: { type: Object, default: null },
  // Pre-fill the client (used when launched from PersonDetail) — locks the field
  presetClient: { type: Object, default: null },
  // If launched from a Lead's PersonDetail, the auto-conversion id to flag for
  // post-save: this routes the booking through convert_to_deal in the backend
  // so the lead → contact → deal lifecycle ticks forward in one shot.
  convertLeadId: { type: String, default: null },
})
const emit = defineEmits(['update:modelValue', 'saved'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const isEditMode = computed(() => !!props.appointment)
const lockedClient = computed(() => !!props.presetClient || !!props.appointment)

const sheetTitle = computed(() => (isEditMode.value ? 'Edit Appointment' : 'New Appointment'))
const submitLabel = computed(() => (isEditMode.value ? 'Save changes' : 'Book Appointment'))

const clientSearch = ref('')
const clientResults = ref([])
const selectedClient = ref(null)
const serviceType = ref('')
const date = ref(new Date().toISOString().split('T')[0])
const timeSlot = ref('')
const status = ref('Pending')
const saving = ref(false)
const error = ref('')

const { config } = useVertical()

// Services come from vertical_config.appointment_services. Salon defaults preserved
// as fallback for backward compat with sites whose config_json hasn't been refreshed.
const SALON_FALLBACK = ['Haircut', 'Coloring', 'Facial', 'Manicure', 'Pedicure', 'Waxing', 'Threading', 'Bridal']
const services = computed(() => config.value?.appointment_services || SALON_FALLBACK)
const statusOptions = ['Pending', 'Confirmed', 'Done', 'Cancelled']

const timeOptions = Array.from({ length: 24 }, (_, i) => {
  const hour = Math.floor(i / 2) + 9
  const min = i % 2 === 0 ? '00' : '30'
  if (hour > 20) return null
  return `${String(hour).padStart(2, '0')}:${min}`
}).filter(Boolean)

const canSubmit = computed(() => selectedClient.value && serviceType.value && date.value && timeSlot.value)

function formatTimeOption(t) {
  const [h, m] = t.split(':').map(Number)
  const ampm = h >= 12 ? 'PM' : 'AM'
  const dh = h % 12 || 12
  return `${dh}:${String(m).padStart(2, '0')} ${ampm}`
}

function selectClient(c) {
  selectedClient.value = c
  clientSearch.value = c.full_name || c.first_name
  clientResults.value = []
}

function resetForm() {
  selectedClient.value = props.presetClient || null
  clientSearch.value = ''
  serviceType.value = ''
  date.value = new Date().toISOString().split('T')[0]
  timeSlot.value = ''
  status.value = 'Pending'
  error.value = ''
}

watch(() => props.modelValue, (open) => {
  if (!open) return
  if (props.appointment) {
    // Edit mode — hydrate from existing doc
    selectedClient.value = {
      name: props.appointment.client,
      full_name: props.appointment.client_name,
      mobile_no: props.appointment.client_phone,
    }
    serviceType.value = props.appointment.service_type || ''
    date.value = props.appointment.date || new Date().toISOString().split('T')[0]
    timeSlot.value = props.appointment.time_slot || ''
    status.value = props.appointment.status || 'Pending'
  } else if (props.presetClient) {
    selectedClient.value = props.presetClient
    serviceType.value = ''
    timeSlot.value = ''
    status.value = 'Pending'
  } else {
    resetForm()
  }
})

watch(clientSearch, async (val) => {
  if (lockedClient.value) return
  if (!val || val.length < 2) { clientResults.value = []; return }
  if (selectedClient.value && (val === selectedClient.value.full_name || val === selectedClient.value.first_name)) return
  selectedClient.value = null
  try {
    clientResults.value = await getList('Contact', {
      fields: ['name', 'first_name', 'last_name', 'full_name', 'mobile_no'],
      filters: [['full_name', 'like', `%${val}%`]],
      pageLength: 5,
    })
  } catch { clientResults.value = [] }
})

async function submit() {
  if (!canSubmit.value || saving.value) return
  saving.value = true
  error.value = ''
  try {
    if (isEditMode.value) {
      // Update existing appointment field-by-field via set_value
      const fields = {
        service_type: serviceType.value,
        date: date.value,
        time_slot: timeSlot.value,
        status: status.value,
      }
      for (const [key, val] of Object.entries(fields)) {
        await setValue('Boon Appointment', props.appointment.name, key, val)
      }
      emit('saved', { ...props.appointment, ...fields })
    } else {
      const newDoc = await createDoc('Boon Appointment', {
        client: selectedClient.value.name,
        client_name: selectedClient.value.full_name || selectedClient.value.first_name,
        client_phone: selectedClient.value.mobile_no || '',
        service_type: serviceType.value,
        date: date.value,
        time_slot: timeSlot.value,
        status: 'Pending',
      })
      // Auto-convert the lead if launched from a Lead's PersonDetail (auto-mode verticals).
      if (props.convertLeadId) {
        try {
          await call('crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal', {
            lead: props.convertLeadId,
            existing_contact: selectedClient.value.name,
          })
        } catch (e) {
          // Conversion failure is non-fatal — appointment booked, log for follow-up.
          console.warn('Auto-convert failed:', e)
        }
      }
      emit('saved', newDoc)
      resetForm()
    }
    isOpen.value = false
  } catch (err) {
    error.value = err?.message || 'Failed to save appointment.'
    console.error('Failed to save appointment:', err)
  } finally {
    saving.value = false
  }
}
</script>
