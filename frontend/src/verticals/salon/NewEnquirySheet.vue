<template>
  <BottomSheet v-model="isOpen" title="New Enquiry">
    <div class="space-y-4">
      <div>
        <label class="text-xs font-medium text-boon-text-secondary mb-1 block">First name</label>
        <input
          v-model="firstName"
          type="text"
          autocomplete="given-name"
          class="w-full h-10 px-3 text-sm bg-boon-surface border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-boon-primary/30"
        />
      </div>
      <div>
        <label class="text-xs font-medium text-boon-text-secondary mb-1 block">Last name</label>
        <input
          v-model="lastName"
          type="text"
          autocomplete="family-name"
          class="w-full h-10 px-3 text-sm bg-boon-surface border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-boon-primary/30"
        />
      </div>
      <div>
        <label class="text-xs font-medium text-boon-text-secondary mb-1 block">Phone (with country code)</label>
        <input
          v-model="mobileNo"
          type="tel"
          autocomplete="tel"
          placeholder="+91 98765 43210"
          class="w-full h-10 px-3 text-sm bg-boon-surface border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-boon-primary/30"
        />
      </div>
      <div>
        <label class="text-xs font-medium text-boon-text-secondary mb-1 block">Email (optional)</label>
        <input
          v-model="email"
          type="email"
          autocomplete="email"
          class="w-full h-10 px-3 text-sm bg-boon-surface border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-boon-primary/30"
        />
      </div>
      <div>
        <label class="text-xs font-medium text-boon-text-secondary mb-1 block">Source</label>
        <select
          v-model="source"
          class="w-full h-10 px-3 text-sm bg-boon-surface border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-boon-primary/30"
        >
          <option v-for="s in sourceOptions" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>
      <div>
        <label class="text-xs font-medium text-boon-text-secondary mb-1 block">Note (optional)</label>
        <textarea
          v-model="note"
          rows="2"
          class="w-full px-3 py-2 text-sm bg-boon-surface border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-boon-primary/30"
        ></textarea>
      </div>

      <p v-if="error" class="text-xs text-red-600">{{ error }}</p>

      <TouchButton
        variant="primary"
        class="w-full"
        :loading="saving"
        :disabled="!canSubmit"
        @click="submit"
      >
        Save Enquiry
      </TouchButton>
    </div>
  </BottomSheet>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import BottomSheet from '@/components/common/BottomSheet.vue'
import TouchButton from '@/components/common/TouchButton.vue'
import { createDoc, call } from '@/utils/api'

const props = defineProps({ modelValue: Boolean })
const emit = defineEmits(['update:modelValue', 'saved'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const firstName = ref('')
const lastName = ref('')
const mobileNo = ref('')
const email = ref('')
const source = ref('Walk-in')
const note = ref('')
const saving = ref(false)
const error = ref('')

const sourceOptions = ['Walk-in', 'WhatsApp', 'Phone Call', 'Instagram', 'Referral', 'Website', 'Other']

const canSubmit = computed(() => firstName.value.trim() && (mobileNo.value.trim() || email.value.trim()))

function reset() {
  firstName.value = ''
  lastName.value = ''
  mobileNo.value = ''
  email.value = ''
  source.value = 'Walk-in'
  note.value = ''
  error.value = ''
}

watch(() => props.modelValue, (open) => { if (open) error.value = '' })

async function submit() {
  if (!canSubmit.value || saving.value) return
  saving.value = true
  error.value = ''
  try {
    const lead = await createDoc('CRM Lead', {
      first_name: firstName.value.trim(),
      last_name: lastName.value.trim(),
      mobile_no: mobileNo.value.trim(),
      email: email.value.trim(),
      source: source.value,
      status: 'New',
    })

    if (note.value.trim()) {
      try {
        await createDoc('Comment', {
          comment_type: 'Comment',
          reference_doctype: 'CRM Lead',
          reference_name: lead.name,
          content: note.value.trim(),
        })
      } catch (e) {
        // Note attach failure is non-fatal — lead is saved.
        console.warn('Failed to attach note:', e)
      }
    }

    emit('saved', lead)
    reset()
    isOpen.value = false
  } catch (err) {
    error.value = err?.message || 'Failed to save enquiry. Phone or email may be required.'
    console.error('Failed to save enquiry:', err)
  } finally {
    saving.value = false
  }
}
</script>
