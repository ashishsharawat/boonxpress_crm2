"""WhatsApp Credit Wallet — pre-send gating + top-up flow.

Pricing model (locked decisions):
- Marketing conversations: 40% markup over Meta cost
- Utility / Authentication: 25% markup
- Service-window replies (within 24h of customer message): truly free
- Free tier included with the ₹999/month subscription: 100 utility
  conversations per calendar month, resets on the 1st
- Top-up tiers with bonus credits:
    Starter ₹500   → 0% bonus  (₹500 wallet credit)
    Growth  ₹2000  → 5% bonus  (₹2100 wallet credit)
    Pro     ₹5000  → 10% bonus (₹5500 wallet credit)
    Scale   ₹10000 → 15% bonus (₹11500 wallet credit)

Send-time flow:
1. `check_and_reserve(category, customer_phone, waba_phone_id)` — opens or
    finds the active 24h conversation log, computes price, deducts from
    wallet (or free quota), creates a Pending Conversation Log + a
    Charge Transaction. Returns `reservation_id` (= conversation log name).
2. Caller invokes Meta Send (frappe_whatsapp).
3. `commit(reservation_id, meta_message_id)` — marks the conversation
    as charged + records the meta_conversation_id on webhook.
4. On Meta send failure, caller invokes `refund(reservation_id, reason)`
    which credits the wallet back.
"""

import json
from datetime import datetime, timedelta

import frappe
from frappe import _


# ---------------------------------------------------------------------
# Tier table — locked product decision (denomination: INR-based)
# ---------------------------------------------------------------------

TIERS = {
    "Starter ₹500":   {"amount_inr": 500,    "bonus_pct": 0},
    "Growth ₹2000":   {"amount_inr": 2000,   "bonus_pct": 5},
    "Pro ₹5000":      {"amount_inr": 5000,   "bonus_pct": 10},
    "Scale ₹10000":   {"amount_inr": 10000,  "bonus_pct": 15},
}

DEFAULT_FREE_UTILITY_QUOTA = 100  # Conversations per calendar month, ₹999 plan
SERVICE_CATEGORY = "Service"


# ---------------------------------------------------------------------
# Public read-only API (frontend calls these for balance/usage display)
# ---------------------------------------------------------------------

@frappe.whitelist()
def get_balance():
    """Return the tenant's current wallet snapshot for display in Settings."""
    wallet = _get_or_create_wallet()
    return {
        "balance_inr": float(wallet.balance_inr or 0),
        "bonus_credits_inr": float(wallet.bonus_credits_inr or 0),
        "free_utility_remaining": int(wallet.free_utility_conversations_remaining or 0),
        "free_utility_quota": int(wallet.free_utility_quota or DEFAULT_FREE_UTILITY_QUOTA),
        "last_topup_at": str(wallet.last_topup_at or ""),
        "tiers": [
            {
                "key": key,
                "amount_inr": tier["amount_inr"],
                "bonus_pct": tier["bonus_pct"],
                "total_credits_inr": tier["amount_inr"] * (1 + tier["bonus_pct"] / 100.0),
            }
            for key, tier in TIERS.items()
        ],
    }


@frappe.whitelist()
def get_pricing(country_code="IN"):
    """Return the current customer-facing prices per category for a country."""
    rows = frappe.get_all(
        "WhatsApp Conversation Pricing",
        filters={"country_code": country_code, "active": 1},
        fields=["category", "meta_cost_inr", "markup_pct", "customer_price_inr"],
    )
    return {r["category"]: r for r in rows}


# ---------------------------------------------------------------------
# Send-time gating — called by whatsapp_send.py before invoking Meta
# ---------------------------------------------------------------------

def check_and_reserve(
    category,
    customer_phone,
    waba_phone_id,
    country_code="IN",
):
    """Reserve a conversation slot. Returns dict with reservation_id or
    `{"ok": False, "reason": "..."}`.

    Caller MUST invoke `commit()` on success or `refund()` on failure.
    """
    if not customer_phone:
        return {"ok": False, "reason": "missing_customer_phone"}
    if not waba_phone_id:
        return {"ok": False, "reason": "missing_waba_phone_id"}

    # 1. Look for an existing active conversation in the 24h window.
    existing = _find_active_conversation(waba_phone_id, customer_phone, category)
    if existing:
        # Inside the window → free for the caller (Meta doesn't double-bill).
        return {
            "ok": True,
            "reservation_id": existing["name"],
            "reused_window": True,
            "charge_inr": 0,
            "is_free_quota_use": False,
        }

    # 2. Service-category messages are truly free per Meta + per our policy.
    if category == SERVICE_CATEGORY:
        log = _open_conversation(waba_phone_id, customer_phone, category, country_code)
        log.charged = 1
        log.charge_amount_inr = 0
        log.save(ignore_permissions=True)
        frappe.db.commit()
        return {
            "ok": True,
            "reservation_id": log.name,
            "reused_window": False,
            "charge_inr": 0,
            "is_free_quota_use": False,
            "service_window": True,
        }

    # 3. Compute charge.
    price = _customer_price(category, country_code)
    if price is None:
        return {"ok": False, "reason": "no_pricing_configured", "category": category, "country": country_code}

    wallet = _get_or_create_wallet()
    _maybe_reset_free_quota(wallet)

    # 4. Try free utility quota first (only Utility category).
    use_free = (
        category == "Utility"
        and (wallet.free_utility_conversations_remaining or 0) > 0
    )
    if use_free:
        log = _open_conversation(waba_phone_id, customer_phone, category, country_code)
        log.is_free_quota_use = 1
        log.charge_amount_inr = 0
        log.charged = 1
        log.save(ignore_permissions=True)

        wallet.free_utility_conversations_remaining = max(
            0, (wallet.free_utility_conversations_remaining or 0) - 1
        )
        wallet.save(ignore_permissions=True)

        _record_transaction(
            wallet=wallet,
            transaction_type="Free Quota Use",
            amount_inr=0,
            related_conversation_log=log.name,
            notes=f"Used 1 of free utility quota; {wallet.free_utility_conversations_remaining} remaining",
            is_free_quota_use=1,
        )
        frappe.db.commit()
        return {
            "ok": True,
            "reservation_id": log.name,
            "reused_window": False,
            "charge_inr": 0,
            "is_free_quota_use": True,
        }

    # 5. Paid path — must have sufficient balance (cash + bonus pooled).
    pooled_balance = float(wallet.balance_inr or 0) + float(wallet.bonus_credits_inr or 0)
    if pooled_balance < price:
        return {
            "ok": False,
            "reason": "insufficient_balance",
            "balance_inr": pooled_balance,
            "required_inr": price,
            "shortfall_inr": price - pooled_balance,
        }

    log = _open_conversation(waba_phone_id, customer_phone, category, country_code)
    log.charge_amount_inr = price

    # Spend bonus first, then cash. Cleaner accounting.
    bonus_used = min(float(wallet.bonus_credits_inr or 0), price)
    cash_used = price - bonus_used
    wallet.bonus_credits_inr = float(wallet.bonus_credits_inr or 0) - bonus_used
    wallet.balance_inr = float(wallet.balance_inr or 0) - cash_used
    wallet.save(ignore_permissions=True)

    log.save(ignore_permissions=True)

    txn = _record_transaction(
        wallet=wallet,
        transaction_type="Conversation Charge",
        amount_inr=-price,
        related_conversation_log=log.name,
        notes=f"{category} conversation, {country_code}, bonus={bonus_used} cash={cash_used}",
    )
    log.charged = 1
    log.charge_transaction = txn.name
    log.save(ignore_permissions=True)

    frappe.db.commit()
    return {
        "ok": True,
        "reservation_id": log.name,
        "reused_window": False,
        "charge_inr": price,
        "is_free_quota_use": False,
        "transaction": txn.name,
    }


def commit(reservation_id, meta_message_id=None, meta_conversation_id=None):
    """Mark the reservation as fully sent. Records Meta's IDs for reconciliation."""
    if not frappe.db.exists("WhatsApp Conversation Log", reservation_id):
        return {"ok": False, "reason": "unknown_reservation"}
    log = frappe.get_doc("WhatsApp Conversation Log", reservation_id)
    if meta_conversation_id:
        log.meta_conversation_id = meta_conversation_id
    log.save(ignore_permissions=True)

    if meta_message_id and log.charge_transaction:
        # Stamp the message id on the transaction for reconciliation.
        frappe.db.set_value(
            "WhatsApp Credit Transaction",
            log.charge_transaction,
            "related_message",
            meta_message_id,
        )
    frappe.db.commit()
    return {"ok": True, "reservation_id": reservation_id}


def refund(reservation_id, reason="Send failed"):
    """Reverse a paid reservation. Adds amount back to wallet, marks conversation cancelled."""
    if not frappe.db.exists("WhatsApp Conversation Log", reservation_id):
        return {"ok": False, "reason": "unknown_reservation"}
    log = frappe.get_doc("WhatsApp Conversation Log", reservation_id)

    # Service-window or free-quota: nothing to refund.
    if not log.charge_transaction or float(log.charge_amount_inr or 0) == 0:
        log.charged = 0
        log.save(ignore_permissions=True)
        frappe.db.commit()
        return {"ok": True, "refunded_inr": 0}

    txn = frappe.get_doc("WhatsApp Credit Transaction", log.charge_transaction)
    refund_amount = abs(float(txn.amount_inr))

    wallet = _get_or_create_wallet()
    wallet.balance_inr = float(wallet.balance_inr or 0) + refund_amount
    wallet.save(ignore_permissions=True)

    _record_transaction(
        wallet=wallet,
        transaction_type="Refund",
        amount_inr=refund_amount,
        related_conversation_log=log.name,
        notes=f"Refund: {reason}",
    )
    log.charged = 0
    log.save(ignore_permissions=True)
    frappe.db.commit()
    return {"ok": True, "refunded_inr": refund_amount}


# ---------------------------------------------------------------------
# Top-up flow — Razorpay one-time payment
# ---------------------------------------------------------------------

@frappe.whitelist()
def create_purchase_order(tier_name):
    """Creates a Pending Purchase Order. Frontend uses the returned
    razorpay_order_id to open Razorpay Checkout. On payment success the
    Razorpay webhook (boonxpress_crm.api.billing) calls apply_purchase().
    """
    if tier_name not in TIERS:
        frappe.throw(_("Unknown tier: {0}").format(tier_name))
    tier = TIERS[tier_name]
    amount = tier["amount_inr"]
    bonus = round(amount * tier["bonus_pct"] / 100.0, 2)

    rzp_order = _create_razorpay_order(amount)

    po = frappe.get_doc({
        "doctype": "WhatsApp Credit Purchase Order",
        "tier_name": tier_name,
        "amount_inr": amount,
        "bonus_credits_inr": bonus,
        "status": "Pending",
        "razorpay_order_id": rzp_order.get("id") if rzp_order else None,
        "buyer_email": frappe.session.user if frappe.session.user != "Guest" else None,
    })
    po.insert(ignore_permissions=True)
    frappe.db.commit()
    return {
        "purchase_order": po.name,
        "razorpay_order_id": po.razorpay_order_id,
        "razorpay_key_id": frappe.conf.get("razorpay_key_id"),
        "amount_inr": amount,
        "bonus_credits_inr": bonus,
        "tier_name": tier_name,
    }


def apply_purchase(razorpay_order_id, razorpay_payment_id):
    """Called by the Razorpay webhook (billing.py) on successful payment.
    Marks the PO Paid and credits the wallet.
    """
    po_name = frappe.db.get_value(
        "WhatsApp Credit Purchase Order",
        {"razorpay_order_id": razorpay_order_id},
        "name",
    )
    if not po_name:
        return {"ok": False, "reason": "no_matching_purchase_order"}
    po = frappe.get_doc("WhatsApp Credit Purchase Order", po_name)
    if po.status == "Paid":
        return {"ok": True, "reason": "already_applied"}

    po.status = "Paid"
    po.razorpay_payment_id = razorpay_payment_id
    po.paid_at = frappe.utils.now()
    po.save(ignore_permissions=True)

    wallet = _get_or_create_wallet()
    wallet.balance_inr = float(wallet.balance_inr or 0) + float(po.amount_inr or 0)
    wallet.bonus_credits_inr = float(wallet.bonus_credits_inr or 0) + float(po.bonus_credits_inr or 0)
    wallet.last_topup_at = frappe.utils.now()
    wallet.save(ignore_permissions=True)

    _record_transaction(
        wallet=wallet,
        transaction_type="Top-up",
        amount_inr=float(po.amount_inr),
        related_purchase_order=po.name,
        notes=f"Razorpay payment {razorpay_payment_id}",
    )
    if float(po.bonus_credits_inr or 0) > 0:
        _record_transaction(
            wallet=wallet,
            transaction_type="Bonus",
            amount_inr=float(po.bonus_credits_inr),
            related_purchase_order=po.name,
            notes=f"{po.tier_name} bonus",
            is_bonus=1,
        )
    frappe.db.commit()
    return {"ok": True, "purchase_order": po.name, "credits_added": float(po.amount_inr) + float(po.bonus_credits_inr)}


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _get_or_create_wallet():
    """The wallet is a Single doctype — there's exactly one per tenant site."""
    if not frappe.db.exists("DocType", "WhatsApp Credit Wallet"):
        frappe.throw(_("WhatsApp Credit Wallet DocType not yet migrated on this site"))
    wallet = frappe.get_single("WhatsApp Credit Wallet")
    if wallet.free_utility_conversations_remaining is None:
        wallet.free_utility_conversations_remaining = wallet.free_utility_quota or DEFAULT_FREE_UTILITY_QUOTA
        wallet.last_reset_at = frappe.utils.now()
        wallet.save(ignore_permissions=True)
    return wallet


def _maybe_reset_free_quota(wallet):
    """Reset the free utility quota at the start of each calendar month."""
    last_reset = wallet.last_reset_at
    now = datetime.now()
    if not last_reset:
        wallet.free_utility_conversations_remaining = wallet.free_utility_quota or DEFAULT_FREE_UTILITY_QUOTA
        wallet.last_reset_at = frappe.utils.now()
        wallet.save(ignore_permissions=True)
        return

    last_reset_dt = (
        last_reset
        if isinstance(last_reset, datetime)
        else datetime.strptime(str(last_reset), "%Y-%m-%d %H:%M:%S.%f")
        if "." in str(last_reset)
        else datetime.strptime(str(last_reset), "%Y-%m-%d %H:%M:%S")
    )
    if last_reset_dt.year != now.year or last_reset_dt.month != now.month:
        wallet.free_utility_conversations_remaining = wallet.free_utility_quota or DEFAULT_FREE_UTILITY_QUOTA
        wallet.last_reset_at = frappe.utils.now()
        wallet.save(ignore_permissions=True)


def _find_active_conversation(waba_phone_id, customer_phone, category):
    """Return the open 24h conversation log for this triple, if any."""
    now = frappe.utils.now()
    rows = frappe.get_all(
        "WhatsApp Conversation Log",
        filters={
            "waba_phone_id": waba_phone_id,
            "customer_phone": customer_phone,
            "category": category,
            "conversation_expires_at": [">", now],
        },
        fields=["name", "conversation_expires_at"],
        order_by="conversation_started_at desc",
        limit_page_length=1,
    )
    return rows[0] if rows else None


def _open_conversation(waba_phone_id, customer_phone, category, country_code):
    started = datetime.now()
    log = frappe.get_doc({
        "doctype": "WhatsApp Conversation Log",
        "waba_phone_id": waba_phone_id,
        "customer_phone": customer_phone,
        "category": category,
        "country_code": country_code,
        "conversation_started_at": started.strftime("%Y-%m-%d %H:%M:%S"),
        "conversation_expires_at": (started + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S"),
        "charged": 0,
    })
    log.insert(ignore_permissions=True)
    return log


def _customer_price(category, country_code):
    rows = frappe.get_all(
        "WhatsApp Conversation Pricing",
        filters={"category": category, "country_code": country_code, "active": 1},
        fields=["customer_price_inr"],
        order_by="effective_from desc",
        limit_page_length=1,
    )
    if not rows:
        return None
    return float(rows[0]["customer_price_inr"] or 0)


def _record_transaction(
    wallet,
    transaction_type,
    amount_inr,
    related_conversation_log=None,
    related_purchase_order=None,
    notes=None,
    is_bonus=0,
    is_free_quota_use=0,
):
    txn = frappe.get_doc({
        "doctype": "WhatsApp Credit Transaction",
        "transaction_type": transaction_type,
        "amount_inr": amount_inr,
        "balance_after_inr": float(wallet.balance_inr or 0) + float(wallet.bonus_credits_inr or 0),
        "currency": "INR",
        "related_conversation_log": related_conversation_log,
        "related_purchase_order": related_purchase_order,
        "notes": notes,
        "is_bonus": is_bonus,
        "is_free_quota_use": is_free_quota_use,
    })
    txn.insert(ignore_permissions=True)
    return txn


def seed_pricing_table():
    """Idempotent — load India pricing rows from fixtures/whatsapp_pricing.json
    if the table is empty. Called by after_migrate.
    """
    if not frappe.db.exists("DocType", "WhatsApp Conversation Pricing"):
        return {"status": "skipped", "reason": "doctype_missing"}
    if frappe.db.count("WhatsApp Conversation Pricing"):
        return {"status": "already_seeded"}

    import os
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "fixtures",
        "whatsapp_pricing.json",
    )
    if not os.path.exists(path):
        return {"status": "no_fixture", "path": path}

    with open(path) as f:
        rows = json.load(f)

    inserted = 0
    for row in rows:
        try:
            frappe.get_doc(row).insert(ignore_permissions=True)
            inserted += 1
        except Exception as e:
            frappe.log_error(f"Pricing seed failed for {row}: {e}", "boonxpress_crm.wallet")
    frappe.db.commit()
    return {"status": "seeded", "inserted": inserted}


def _create_razorpay_order(amount_inr):
    """Create a Razorpay Order via API. Returns the dict from Razorpay or
    None if creds aren't configured (caller falls back to a mock order id
    so dev/test flows still work).
    """
    key_id = frappe.conf.get("razorpay_key_id")
    key_secret = frappe.conf.get("razorpay_key_secret")
    if not key_id or not key_secret:
        # Dev mode: return a mock order so the flow can be exercised end-to-end
        # before live Razorpay creds are in hand.
        return {"id": f"order_mock_{frappe.generate_hash(length=12)}"}

    import base64
    import urllib.parse
    import urllib.request

    auth = base64.b64encode(f"{key_id}:{key_secret}".encode()).decode()
    body = json.dumps({
        "amount": int(amount_inr * 100),  # Razorpay wants paise
        "currency": "INR",
        "payment_capture": 1,
    }).encode()
    req = urllib.request.Request(
        "https://api.razorpay.com/v1/orders",
        data=body,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        frappe.log_error(f"Razorpay order create failed: {e}", "boonxpress_crm.wallet")
        return None
