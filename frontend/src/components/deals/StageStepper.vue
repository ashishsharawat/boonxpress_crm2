<template>
  <div class="flex items-center gap-0 px-2 py-3">
    <template v-for="(stage, idx) in stages" :key="stage">
      <button
        :data-stage="stage"
        @click="$emit('change', stage)"
        class="flex flex-col items-center flex-1 group"
      >
        <span
          :class="[
            'w-5 h-5 rounded-full transition-all',
            isPassed(idx) ? 'bg-emerald-500' : '',
            isCurrent(idx) ? 'bg-amber-500 ring-4 ring-amber-100' : (isPassed(idx) ? '' : 'bg-gray-300'),
          ]"
        ></span>
        <span
          :class="[
            'text-[10px] mt-1 font-semibold',
            isCurrent(idx) ? 'text-amber-600' : isPassed(idx) ? 'text-emerald-600' : 'text-gray-400',
          ]"
        >{{ stage.slice(0, 6) }}</span>
      </button>
      <div
        v-if="idx < stages.length - 1"
        :class="['h-[2px] flex-1', isPassed(idx + 1) || isCurrent(idx + 1) ? 'bg-emerald-500' : 'bg-gray-200']"
      ></div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  stages: { type: Array, required: true },
  current: { type: String, required: true },
})
defineEmits(['change'])

const currentIndex = computed(() => props.stages.indexOf(props.current))

function isPassed(idx) {
  return idx < currentIndex.value
}
function isCurrent(idx) {
  return idx === currentIndex.value
}
</script>
