<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      class="fixed inset-0 z-40 bg-black/50 flex items-end sm:items-center justify-center"
      @click.self="$emit('update:modelValue', false)"
    >
      <div class="bg-white w-full sm:max-w-sm rounded-t-2xl sm:rounded-2xl p-5 shadow-xl">
        <h3 class="text-lg font-semibold text-boon-text-primary">{{ title }}</h3>
        <p class="text-sm text-boon-text-secondary mt-2">{{ message }}</p>
        <div class="flex gap-2 mt-5">
          <button
            @click="$emit('update:modelValue', false)"
            class="flex-1 py-2.5 rounded-lg bg-gray-100 text-boon-text-primary text-sm font-semibold"
          >Cancel</button>
          <button
            @click="confirm"
            class="flex-1 py-2.5 rounded-lg bg-red-600 text-white text-sm font-semibold"
          >Delete</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  modelValue: Boolean,
  title: { type: String, default: 'Delete this record?' },
  message: { type: String, default: 'It will be archived (soft delete). You can restore from Frappe Desk.' },
})
const emit = defineEmits(['update:modelValue', 'confirmed'])

function confirm() {
  emit('confirmed')
  emit('update:modelValue', false)
}
</script>
