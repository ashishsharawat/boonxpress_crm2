<template>
  <div class="p-4 space-y-2">
    <div
      v-for="field in fields"
      :key="field.key"
      @click="editField(field)"
      class="bg-boon-surface rounded-lg p-3 flex justify-between items-center cursor-pointer active:bg-gray-50"
    >
      <div class="min-w-0 flex-1">
        <div class="text-[10px] uppercase font-semibold text-boon-text-secondary">{{ field.label }}</div>
        <div class="text-sm text-boon-text-primary truncate mt-0.5">{{ field.value || '—' }}</div>
      </div>
      <Pencil :size="14" class="text-gray-400" />
    </div>

    <EditFieldSheet
      v-if="editing"
      v-model="sheetOpen"
      :field="editing"
      :saver="saveField"
      @saved="onSaved"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Pencil } from 'lucide-vue-next'
import { useVertical } from '@/composables/useVertical'
import { setValue } from '@/utils/api'
import EditFieldSheet from '@/components/common/EditFieldSheet.vue'

const props = defineProps({ person: { type: Object, required: true } })
const emit = defineEmits(['refresh'])

const { config } = useVertical()
const editing = ref(null)
const sheetOpen = ref(false)

const target = computed(() => {
  if (props.person.contact) return { doctype: 'Contact', doc: props.person.contact }
  if (props.person.lead) return { doctype: 'CRM Lead', doc: props.person.lead }
  return null
})

const fields = computed(() => {
  if (!target.value) return []
  const isContact = target.value.doctype === 'Contact'
  const baseFields = [
    { key: 'first_name', label: 'First name', type: 'text' },
    { key: 'last_name', label: 'Last name', type: 'text' },
    { key: isContact ? 'mobile_no' : 'mobile_no', label: 'Phone', type: 'text' },
    { key: isContact ? 'email_id' : 'email', label: 'Email', type: 'text' },
  ]
  const verticalFields = (config.value?.profile_fields || []).map((f) => ({
    key: f.key,
    label: f.label,
    type: f.type,
  }))
  return [...baseFields, ...verticalFields].map((f) => ({
    ...f,
    value: target.value.doc?.[f.key],
  }))
})

function editField(field) {
  editing.value = field
  sheetOpen.value = true
}

async function saveField(newValue) {
  if (!target.value) return
  await setValue(target.value.doctype, target.value.doc.name, editing.value.key, newValue)
}

function onSaved() {
  emit('refresh')
}
</script>
