<template>
  <header class="flex items-center justify-between px-4 bg-boon-surface border-b border-gray-100 shrink-0"
          style="height: 48px; min-height: 48px;">
    <div class="flex items-center gap-2 min-w-0">
      <div class="w-7 h-7 rounded-lg bg-boon-primary flex items-center justify-center shrink-0">
        <span class="text-white text-xs font-bold">{{ initials }}</span>
      </div>
      <h1 class="text-sm font-semibold text-boon-text-primary truncate font-heading">
        {{ businessName }}
      </h1>
    </div>
    <button
      class="relative flex items-center justify-center touch-target cursor-pointer"
      @click="$router.push('/notifications')"
    >
      <Bell :size="20" class="text-boon-text-secondary" />
      <span
        v-if="totalUnread > 0"
        class="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center"
      >
        {{ totalUnread > 9 ? '9+' : totalUnread }}
      </span>
    </button>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { Bell } from 'lucide-vue-next'
import { useVertical } from '@/composables/useVertical'
import { useNotificationStore } from '@/stores/notifications'
import { getInitials } from '@/utils/formatters'

const { businessName } = useVertical()
const notificationStore = useNotificationStore()
const totalUnread = computed(() => notificationStore.totalUnread)
const initials = computed(() => getInitials(businessName.value))
</script>
