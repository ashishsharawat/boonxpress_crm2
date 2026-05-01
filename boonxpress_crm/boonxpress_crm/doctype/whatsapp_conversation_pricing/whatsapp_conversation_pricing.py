"""WhatsApp Conversation Pricing — per (country, category) cost+markup table.

`customer_price_inr` is auto-computed from `meta_cost_inr` × markup on save.
"""

import frappe
from frappe.model.document import Document


class WhatsAppConversationPricing(Document):
    def validate(self):
        meta_cost = float(self.meta_cost_inr or 0)
        markup = float(self.markup_pct or 0)
        self.customer_price_inr = round(meta_cost * (1 + markup / 100.0), 4)
