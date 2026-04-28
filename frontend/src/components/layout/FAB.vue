<template>
  <div class="fixed right-4 z-30" style="bottom: 72px;">
    <!-- Expanded actions backdrop -->
    <Transition name="fade">
      <div v-if="expanded" class="fixed inset-0 bg-black/20 z-20" @click="expanded = false" />
    </Transition>

    <!-- Action items (shown when expanded) -->
    <Transition name="slide-up">
      <div v-if="expanded" class="absolute bottom-14 right-0 flex flex-col items-end gap-2 z-30">
        <button
          v-for="action in fabActions"
          :key="action.action"
          class="flex items-center gap-2 bg-boon-surface rounded-full pl-3 pr-4 py-2 shadow-lg cursor-pointer transition-transform duration-200 hover:scale-105"
          @click="handleAction(action)"
        >
          <component :is="getIcon(action.icon)" :size="18" class="text-boon-primary" />
          <span class="text-sm font-medium text-boon-text-primary whitespace-nowrap">{{ action.label }}</span>
        </button>
      </div>
    </Transition>

    <!-- Main FAB button -->
    <button
      class="w-12 h-12 rounded-full bg-boon-primary shadow-lg flex items-center justify-center cursor-pointer transition-all duration-200 hover:shadow-xl active:scale-95 z-30 relative"
      @click="handleFabClick"
    >
      <Plus
        :size="24"
        class="text-white transition-transform duration-200"
        :class="{ 'rotate-45': expanded }"
      />
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useVertical } from '@/composables/useVertical'
import { emitFabAction } from '@/composables/useFabBus'
import {
  Plus, CalendarPlus, UserPlus, TrendingUp, Package, Footprints
} from 'lucide-vue-next'

const { fabActions } = useVertical()
const expanded = ref(false)

const emit = defineEmits(['action'])

const iconMap = {
  CalendarPlus, UserPlus, TrendingUp, Package,
  FootprintsIcon: Footprints,
}

function getIcon(name) {
  return iconMap[name] || Plus
}

function handleFabClick() {
  if (fabActions.value.length === 1) {
    handleAction(fabActions.value[0])
  } else {
    expanded.value = !expanded.value
  }
}

function handleAction(action) {
  expanded.value = false
  // Local emit for direct parent listeners + global bus for vertical homes
  // mounted under <Home>/<router-view> that don't have a direct prop chain.
  emit('action', action.action)
  emitFabAction(action.action)
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.slide-up-enter-active, .slide-up-leave-active { transition: all 0.2s ease-out; }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translateY(8px); }
</style>
