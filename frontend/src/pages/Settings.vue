<template>
  <div class="h-full overflow-y-auto px-4 py-4 space-y-4">
    <!-- Business Info -->
    <div class="bg-boon-surface rounded-2xl p-4">
      <h3 class="text-xs font-semibold text-boon-text-secondary uppercase tracking-wider mb-3">Business</h3>
      <div class="space-y-2">
        <div class="flex justify-between">
          <span class="text-sm text-boon-text-secondary">Name</span>
          <span class="text-sm text-boon-text-primary font-medium">{{ businessName }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-sm text-boon-text-secondary">Type</span>
          <span class="text-sm text-boon-text-primary font-medium">{{ displayName }}</span>
        </div>
      </div>
    </div>

    <!-- Account -->
    <div class="bg-boon-surface rounded-2xl p-4">
      <h3 class="text-xs font-semibold text-boon-text-secondary uppercase tracking-wider mb-3">Account</h3>
      <div class="space-y-2">
        <div class="flex justify-between">
          <span class="text-sm text-boon-text-secondary">User</span>
          <span class="text-sm text-boon-text-primary font-medium">{{ userEmail }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-sm text-boon-text-secondary">Plan</span>
          <span class="text-sm text-boon-text-primary font-medium">₹999/mo</span>
        </div>
      </div>
    </div>

    <!-- WhatsApp Connection (Embedded Signup, v0.4.0) -->
    <div>
      <h3 class="text-xs font-semibold text-boon-text-secondary uppercase tracking-wider mb-2 px-1">WhatsApp</h3>
      <ConnectWhatsAppButton />
    </div>

    <!-- WhatsApp Credit Wallet (v0.3.0) -->
    <div class="bg-boon-surface rounded-2xl p-4">
      <h3 class="text-xs font-semibold text-boon-text-secondary uppercase tracking-wider mb-3">Message Credits</h3>
      <div v-if="walletLoading" class="text-sm text-boon-text-secondary">Loading…</div>
      <div v-else>
        <div class="flex justify-between mb-2">
          <span class="text-sm text-boon-text-secondary">Balance</span>
          <span class="text-sm text-boon-text-primary font-semibold">
            ₹{{ formatNum(wallet.balance.balance_inr + wallet.balance.bonus_credits_inr) }}
            <span v-if="wallet.balance.bonus_credits_inr > 0" class="text-[10px] text-emerald-600 ml-1">
              (incl. ₹{{ formatNum(wallet.balance.bonus_credits_inr) }} bonus)
            </span>
          </span>
        </div>
        <div class="flex justify-between mb-3">
          <span class="text-sm text-boon-text-secondary">Free utility this month</span>
          <span class="text-sm text-boon-text-primary font-medium">
            {{ wallet.balance.free_utility_remaining }} / {{ wallet.balance.free_utility_quota }}
          </span>
        </div>
        <div class="grid grid-cols-2 gap-2">
          <button
            v-for="tier in wallet.balance.tiers"
            :key="tier.key"
            @click="onBuyCredits(tier.key)"
            :disabled="purchasing"
            class="py-2 rounded-lg bg-boon-primary-bg text-boon-primary text-xs font-semibold disabled:opacity-50"
          >
            ₹{{ formatNum(tier.amount_inr) }}<span v-if="tier.bonus_pct"> +{{ tier.bonus_pct }}%</span>
          </button>
        </div>
        <p v-if="purchaseHint" class="text-xs text-boon-text-secondary mt-2">{{ purchaseHint }}</p>
      </div>
    </div>

    <!-- App Version -->
    <div class="text-center py-2">
      <p class="text-[10px] text-gray-400">BoonCRM v0.4.0</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useVertical } from '@/composables/useVertical'
import { useSessionStore } from '@/stores/session'
import { useWallet } from '@/composables/useWallet'
import ConnectWhatsAppButton from '@/components/whatsapp/ConnectWhatsAppButton.vue'

const { businessName, displayName } = useVertical()
const session = useSessionStore()
const userEmail = session.userEmail

const wallet = useWallet()
const walletLoading = ref(true)
const purchasing = ref(false)
const purchaseHint = ref('')

async function loadWallet() {
  walletLoading.value = true
  try {
    await wallet.refresh()
  } finally {
    walletLoading.value = false
  }
}

async function onBuyCredits(tierKey) {
  if (purchasing.value) return
  purchasing.value = true
  purchaseHint.value = ''
  try {
    const result = await wallet.buyCredits(tierKey)
    if (result?.razorpay_order_id?.startsWith('order_mock_')) {
      purchaseHint.value = 'Razorpay creds not configured yet — order created in mock mode. Operator must complete platform setup.'
    } else if (result?.razorpay_order_id) {
      purchaseHint.value = `Razorpay order ${result.razorpay_order_id} created. Razorpay Checkout integration ships with Settings UI v2 — for now, complete the payment via Razorpay Dashboard.`
      // Future: open Razorpay Checkout here
      // const rzp = new window.Razorpay({ key: result.razorpay_key_id, order_id: result.razorpay_order_id, ... })
      // rzp.open()
    }
    await loadWallet()
  } catch (e) {
    purchaseHint.value = e.message || 'Failed to start top-up.'
  } finally {
    purchasing.value = false
  }
}

function formatNum(n) {
  return new Intl.NumberFormat('en-IN').format(Math.round(Number(n) || 0))
}

onMounted(loadWallet)
</script>
