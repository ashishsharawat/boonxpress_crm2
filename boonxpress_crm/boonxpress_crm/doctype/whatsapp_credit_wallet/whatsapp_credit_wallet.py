"""WhatsApp Credit Wallet — Single doctype, one per tenant site.

Holds the tenant's INR-denominated message-credit balance plus the free
utility-conversation quota (100/month included with the ₹999 plan).
Mutations happen exclusively through `boonxpress_crm.api.wallet`.
"""

from frappe.model.document import Document


class WhatsAppCreditWallet(Document):
    pass
