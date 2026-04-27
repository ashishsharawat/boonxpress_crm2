<template>
  <div class="flex flex-col h-full bg-boon-surface-alt overflow-hidden">
    <AppHeader />
    <main class="flex-1 overflow-y-auto overscroll-contain">
      <slot />
    </main>
    <FAB />
    <BottomTabBar />
  </div>
</template>

<script setup>
import AppHeader from './AppHeader.vue'
import BottomTabBar from './BottomTabBar.vue'
import FAB from './FAB.vue'
</script>
