"""WhatsApp Credit Purchase Order — one row per Razorpay top-up flow.

Lifecycle: Pending (Razorpay order created) → Paid (webhook hits) → wallet
gets credited via boonxpress_crm.api.wallet.apply_purchase().
"""

from frappe.model.document import Document


class WhatsAppCreditPurchaseOrder(Document):
    def validate(self):
        amount = float(self.amount_inr or 0)
        bonus = float(self.bonus_credits_inr or 0)
        self.total_credits_inr = round(amount + bonus, 2)
