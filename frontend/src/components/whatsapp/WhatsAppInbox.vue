<template>
  <div class="h-full flex flex-col bg-boon-surface-alt">
    <div class="flex-1 flex items-center justify-center p-6">
      <div class="text-center">
        <MessageCircle :size="48" class="text-green-300 mx-auto mb-3" />
        <p class="text-sm font-medium text-boon-text-primary">WhatsApp Inbox</p>
        <p class="text-xs text-boon-text-secondary mt-1">
          Connect your WhatsApp Business account to see messages here.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { MessageCircle } from 'lucide-vue-next'
</script>
