<template>
  <div ref="container" class="h-full overflow-y-auto overscroll-contain" @scroll="onScroll">
    <!-- Pull to refresh indicator -->
    <div v-if="refreshing" class="flex justify-center py-3">
      <div class="w-5 h-5 border-2 border-boon-primary border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Content -->
    <div class="px-4 py-3 space-y-2">
      <!-- Loading skeleton -->
      <template v-if="loading && items.length === 0">
        <SkeletonCard v-for="i in 5" :key="i" />
      </template>

      <!-- Items -->
      <template v-else-if="items.length > 0">
        <slot v-for="item in items" :key="item.name" :item="item" />
      </template>

      <!-- Empty state -->
      <EmptyState
        v-else
        :title="emptyTitle"
        :message="emptyMessage"
      />
    </div>

    <!-- Load more indicator -->
    <div v-if="loading && items.length > 0" class="flex justify-center py-3">
      <div class="w-5 h-5 border-2 border-boon-primary border-t-transparent rounded-full animate-spin" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import SkeletonCard from './SkeletonCard.vue'
import EmptyState from './EmptyState.vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  hasMore: { type: Boolean, default: false },
  refreshing: { type: Boolean, default: false },
  emptyTitle: { type: String, default: 'Nothing here yet' },
  emptyMessage: { type: String, default: 'Items will appear here once added.' },
})

const emit = defineEmits(['load-more', 'refresh'])
const container = ref(null)

function onScroll() {
  if (!props.hasMore || props.loading) return
  const el = container.value
  if (!el) return
  const threshold = 100
  if (el.scrollHeight - el.scrollTop - el.clientHeight < threshold) {
    emit('load-more')
  }
}
</script>
