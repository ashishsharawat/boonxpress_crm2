<template>
  <BottomSheet v-model="isOpen" title="New Appointment">
    <div class="space-y-4">
      <!-- Client search -->
      <div>
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

      <!-- Service type -->
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

      <!-- Date -->
      <div>
        <label class="text-xs font-medium text-boon-text-secondary mb-1 block">Date</label>
        <input
          v-model="date"
          type="date"
          class="w-full h-10 px-3 text-sm bg-boon-surface border border-gray-200 rounded-xl text-boon-text-primary focus:outline-none focus:ring-2 focus:ring-boon-primary/30"
        />
      </div>

      <!-- Time slot -->
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

      <!-- Submit -->
      <TouchButton
        variant="primary"
        class="w-full"
        :loading="saving"
        :disabled="!canSubmit"
        @click="createAppointment"
      >
        Book Appointment
      </TouchButton>
    </div>
  </BottomSheet>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import BottomSheet from '@/components/common/BottomSheet.vue'
import SearchBar from '@/components/common/SearchBar.vue'
import TouchButton from '@/components/common/TouchButton.vue'
import { getList, createDoc } from '@/utils/api'

const props = defineProps({ modelValue: Boolean })
const emit = defineEmits(['update:modelValue', 'created'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const clientSearch = ref('')
const clientResults = ref([])
const selectedClient = ref(null)
const serviceType = ref('')
const date = ref(new Date().toISOString().split('T')[0])
const timeSlot = ref('')
const saving = ref(false)

const services = ['Haircut', 'Coloring', 'Facial', 'Manicure', 'Pedicure', 'Waxing', 'Threading', 'Bridal']

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

watch(clientSearch, async (val) => {
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

async function createAppointment() {
  if (!canSubmit.value || saving.value) return
  saving.value = true
  try {
    await createDoc('Boon Appointment', {
      client: selectedClient.value.name,
      client_name: selectedClient.value.full_name || selectedClient.value.first_name,
      client_phone: selectedClient.value.mobile_no || '',
      service_type: serviceType.value,
      date: date.value,
      time_slot: timeSlot.value,
      status: 'Pending',
    })
    emit('created')
    // Reset form
    selectedClient.value = null
    clientSearch.value = ''
    serviceType.value = ''
    timeSlot.value = ''
  } catch (err) {
    console.error('Failed to create appointment:', err)
  } finally {
    saving.value = false
  }
}
</script>
