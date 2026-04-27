<template>
  <nav class="flex items-center justify-around bg-boon-surface border-t border-gray-200 pb-safe shrink-0"
       style="height: 56px; min-height: 56px;">
    <router-link
      v-for="item in navItems"
      :key="item.key"
      :to="item.route"
      class="flex flex-col items-center justify-center gap-0.5 flex-1 h-full touch-target transition-colors duration-200 cursor-pointer"
      :class="isActive(item.route) ? 'text-boon-primary' : 'text-boon-text-secondary'"
    >
      <component :is="getIcon(item.icon)" :size="20" :stroke-width="isActive(item.route) ? 2.5 : 1.5" />
      <span class="text-[10px] font-medium leading-none">{{ item.label }}</span>
    </router-link>
  </nav>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { useVertical } from '@/composables/useVertical'
import {
  Home, Users, Target, MessageCircle, Settings,
  Calendar, TrendingUp, Package
} from 'lucide-vue-next'

const route = useRoute()
const { navItems } = useVertical()

const iconMap = {
  Home, Users, Target, MessageCircle, Settings,
  Calendar, TrendingUp, Package,
}

function getIcon(name) {
  return iconMap[name] || Home
}

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>
