<template>
  <div class="flex gap-2 overflow-x-auto px-4 py-2 no-scrollbar">
    <div
      v-for="stat in stats"
      :key="stat.key"
      class="flex items-center gap-2 bg-boon-surface rounded-xl px-3 py-2.5 shrink-0 min-w-[90px]"
    >
      <component :is="getIcon(stat.icon)" :size="16" class="text-boon-primary shrink-0" />
      <div>
        <p class="text-lg font-bold text-boon-text-primary leading-none">{{ stat.value ?? '-' }}</p>
        <p class="text-[10px] text-boon-text-secondary mt-0.5">{{ stat.label }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Calendar, Target, MessageCircle, Flame, Car, Package, TrendingUp } from 'lucide-vue-next'

defineProps({
  stats: { type: Array, default: () => [] },
})

const iconMap = { Calendar, Target, MessageCircle, Flame, Car, Package, TrendingUp }

function getIcon(name) {
  return iconMap[name] || Target
}
</script>

<style scoped>
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
.no-scrollbar::-webkit-scrollbar { display: none; }
</style>
