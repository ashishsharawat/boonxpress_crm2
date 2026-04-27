<template>
  <BottomSheet :model-value="modelValue" :title="`Edit ${field.label}`" @update:model-value="$emit('update:modelValue', $event)">
    <div>
      <textarea
        v-if="field.type === 'textarea'"
        v-model="localValue"
        rows="4"
        class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
      ></textarea>
      <input
        v-else
        :type="inputType"
        v-model="localValue"
        class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
      />
      <div class="flex gap-2 mt-6">
        <button
          @click="$emit('update:modelValue', false)"
          class="flex-1 py-2.5 rounded-lg bg-gray-100 text-boon-text-primary text-sm font-semibold"
        >Cancel</button>
        <button
          :disabled="saving"
          @click="save"
          class="flex-1 py-2.5 rounded-lg bg-boon-primary text-white text-sm font-semibold disabled:opacity-50"
        >{{ saving ? 'Saving…' : 'Save' }}</button>
      </div>
      <p v-if="error" class="text-xs text-red-600 mt-3">{{ error }}</p>
    </div>
  </BottomSheet>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import BottomSheet from '@/components/common/BottomSheet.vue'

const props = defineProps({
  modelValue: Boolean,
  field: { type: Object, required: true },
  saver: { type: Function, required: true },
})
const emit = defineEmits(['update:modelValue', 'saved'])

const localValue = ref(props.field.value ?? '')
const saving = ref(false)
const error = ref('')

watch(() => props.field, (f) => { localValue.value = f.value ?? '' }, { deep: true })

const inputType = computed(() => {
  if (props.field.type === 'date') return 'date'
  if (props.field.type === 'url') return 'url'
  return 'text'
})

async function save() {
  saving.value = true
  error.value = ''
  try {
    await props.saver(localValue.value)
    emit('saved', localValue.value)
    emit('update:modelValue', false)
  } catch (err) {
    error.value = err.message || 'Failed to save'
  } finally {
    saving.value = false
  }
}
</script>
