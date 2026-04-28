<template>
  <BottomSheet v-model="isOpen" :title="sheetTitle">
    <div class="space-y-4">
      <!-- Customer search (locked when launched from a Lead's PersonDetail) -->
      <div v-if="!lockedCustomer">
        <label class="text-xs font-medium text-boon-text-secondary mb-1 block">Customer / Lead</label>
        <SearchBar v-model="customerSearch" placeholder="Search customer or lead..." />
        <div v-if="customerResults.length" class="mt-1 bg-white border border-gray-200 rounded-xl max-h-32 overflow-y-auto">
          <button
            v-for="c in customerResults"
            :key="c.name"
            class="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 cursor-pointer"
            @click="selectCustomer(c)"
          >
            {{ c.full_name || c.first_name || c.lead_name }} <span class="text-[10px] text-boon-text-secondary">{{ c._kind }}</span>
          </button>
        </div>
        <p v-if="selectedCustomer" class="text-xs text-boon-primary mt-1">
          Selected: {{ selectedCustomer.full_name || selectedCustomer.first_name }}
        </p>
      </div>
      <div v-else class="bg-boon-surface-alt rounded-xl px-3 py-2">
        <div class="text-xs text-boon-text-secondary">For</div>
        <div class="text-sm font-semibold">{{ selectedCustomer?.full_name || selectedCustomer?.first_name }}</div>
      </div>

      <div>
        <label class="text-xs font-medium text-boon-text-secondary mb-1 block">Vehicle / Description</label>
        <input
          v-model="organization"
          type="text"
          placeholder="e.g. 2020 Honda City VX, white"
          class="w-full h-10 px-3 text-sm bg-boon-surface border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-boon-primary/30"
        />
      </div>

      <div class="grid grid-cols-3 gap-2">
        <div class="col-span-2">
          <label class="text-xs font-medium text-boon-text-secondary mb-1 block">Quote amount</label>
          <input
            v-model.number="dealValue"
            type="number"
            min="0"
            class="w-full h-10 px-3 text-sm bg-boon-surface border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-boon-primary/30"
          />
        </div>
        <div>
          <label class="text-xs font-medium text-boon-text-secondary mb-1 block">Currency</label>
          <select
            v-model="currency"
            class="w-full h-10 px-3 text-sm bg-boon-surface border border-gray-200 rounded-xl"
          >
            <option>INR</option>
            <option>USD</option>
            <option>EUR</option>
          </select>
        </div>
      </div>

      <div>
        <label class="text-xs font-medium text-boon-text-secondary mb-1 block">Stage</label>
        <select
          v-model="status"
          class="w-full h-10 px-3 text-sm bg-boon-surface border border-gray-200 rounded-xl"
        >
          <option v-for="stage in stages" :key="stage" :value="stage">{{ stage }}</option>
        </select>
      </div>

      <div>
        <label class="text-xs font-medium text-boon-text-secondary mb-1 block">Expected close (optional)</label>
        <input
          v-model="expectedClosure"
          type="date"
          class="w-full h-10 px-3 text-sm bg-boon-surface border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-boon-primary/30"
        />
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
import { getList, createDoc, call } from '@/utils/api'

const props = defineProps({
  modelValue: Boolean,
  // When launched from a Lead's PersonDetail, pass the Lead doc here so we
  // run convert_to_deal (which creates Contact + Deal in one call) instead
  // of creating a standalone Deal.
  lead: { type: Object, default: null },
  // Pre-fill an existing Contact (locks the customer field).
  presetContact: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'saved'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const lockedCustomer = computed(() => !!props.lead || !!props.presetContact)

const { config } = useVertical()
const stages = computed(() => config.value?.deal_stages || ['Qualification', 'Quote Sent', 'Negotiation'])

const sheetTitle = computed(() => (props.lead ? 'Send Quote (convert lead)' : 'Send Quote'))
const submitLabel = computed(() => (saving.value ? 'Saving…' : 'Send Quote'))

const customerSearch = ref('')
const customerResults = ref([])
const selectedCustomer = ref(null)
const organization = ref('')
const dealValue = ref(0)
const currency = ref('INR')
const status = ref('')
const expectedClosure = ref('')
const saving = ref(false)
const error = ref('')

const canSubmit = computed(() => {
  if (!status.value) return false
  if (props.lead) return true
  return selectedCustomer.value && organization.value.trim()
})

watch(() => props.modelValue, (open) => {
  if (!open) return
  status.value = stages.value[0] || 'Qualification'
  if (props.lead) {
    selectedCustomer.value = {
      name: props.lead.name,
      first_name: props.lead.first_name,
      last_name: props.lead.last_name,
      full_name: `${props.lead.first_name || ''} ${props.lead.last_name || ''}`.trim(),
      _kind: 'Lead',
    }
    organization.value = props.lead.organization || ''
  } else if (props.presetContact) {
    selectedCustomer.value = props.presetContact
  } else {
    selectedCustomer.value = null
    organization.value = ''
    customerSearch.value = ''
  }
  dealValue.value = 0
  currency.value = 'INR'
  expectedClosure.value = ''
  error.value = ''
})

watch(customerSearch, async (val) => {
  if (lockedCustomer.value) return
  if (!val || val.length < 2) { customerResults.value = []; return }
  if (selectedCustomer.value && (val === selectedCustomer.value.full_name)) return
  selectedCustomer.value = null
  try {
    const [contacts, leads] = await Promise.all([
      getList('Contact', {
        fields: ['name', 'first_name', 'last_name', 'full_name', 'mobile_no'],
        filters: [['full_name', 'like', `%${val}%`]],
        pageLength: 5,
      }).catch(() => []),
      getList('CRM Lead', {
        fields: ['name', 'first_name', 'last_name'],
        filters: [['first_name', 'like', `%${val}%`]],
        pageLength: 5,
      }).catch(() => []),
    ])
    customerResults.value = [
      ...contacts.map((c) => ({ ...c, _kind: 'Contact' })),
      ...leads.map((l) => ({ ...l, full_name: `${l.first_name || ''} ${l.last_name || ''}`.trim(), _kind: 'Lead' })),
    ]
  } catch {
    customerResults.value = []
  }
})

function selectCustomer(c) {
  selectedCustomer.value = c
  customerSearch.value = c.full_name || c.first_name || ''
  customerResults.value = []
}

async function submit() {
  if (!canSubmit.value || saving.value) return
  saving.value = true
  error.value = ''
  try {
    let dealName
    const dealPayload = {
      organization: organization.value || (selectedCustomer.value?.full_name || 'Customer'),
      deal_value: dealValue.value || 0,
      currency: currency.value,
      status: status.value,
    }
    if (expectedClosure.value) dealPayload.expected_closure_date = expectedClosure.value

    if (props.lead || (selectedCustomer.value && selectedCustomer.value._kind === 'Lead')) {
      const leadName = props.lead?.name || selectedCustomer.value.name
      const result = await call('crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal', {
        lead: leadName,
        deal: dealPayload,
      })
      dealName = result
    } else {
      const newDeal = await createDoc('CRM Deal', {
        ...dealPayload,
        contact: selectedCustomer.value?.name,
      })
      dealName = newDeal.name
    }

    emit('saved', { dealName })
    isOpen.value = false
  } catch (err) {
    error.value = err?.message || 'Failed to save quote.'
    console.error('Failed to save quote:', err)
  } finally {
    saving.value = false
  }
}
</script>
