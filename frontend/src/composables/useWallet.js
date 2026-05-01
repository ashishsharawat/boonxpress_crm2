import { ref } from 'vue'
import { call } from '@/utils/api'

/**
 * Reactive WhatsApp credit wallet client.
 *
 *   const { balance, tiers, loading, refresh, buyCredits } = useWallet()
 *   await refresh()
 *   await buyCredits('Growth ₹2000')
 *
 * The buy flow returns a Razorpay order_id + key_id; the caller opens
 * Razorpay Checkout, which on success triggers the order.paid webhook
 * server-side, which credits the wallet. After Checkout, call refresh().
 */
export function useWallet() {
  const balance = ref({
    balance_inr: 0,
    bonus_credits_inr: 0,
    free_utility_remaining: 0,
    free_utility_quota: 100,
    last_topup_at: '',
    tiers: [],
  })
  const loading = ref(false)

  async function refresh() {
    loading.value = true
    try {
      balance.value = await call('boonxpress_crm.api.wallet.get_balance')
    } finally {
      loading.value = false
    }
  }

  async function buyCredits(tierName) {
    return call('boonxpress_crm.api.wallet.create_purchase_order', { tier_name: tierName })
  }

  return { balance, loading, refresh, buyCredits }
}
