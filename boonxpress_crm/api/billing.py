"""Razorpay subscription billing integration + 5-user cap enforcement.

The Razorpay webhook lifecycle drives tenant site activation/suspension:
- subscription.activated     → activate site (clear suspended flag)
- subscription.charged       → log payment, extend grace period
- payment.failed             → mark dunning, n8n sends WA reminder
- subscription.cancelled     → suspend site (read-only mode)
- subscription.completed     → suspend site

The 5-user cap is enforced via a Frappe permission hook that blocks new
User records once the tenant's active count hits 5 (per PRD §3.3, §5.2).

Configuration (Site Config / Boon Tenant Config):
- razorpay_key_id, razorpay_key_secret    — for API calls
- razorpay_webhook_secret                 — for HMAC verification
- max_users (default 5)                   — per-tenant cap
"""

import hashlib
import hmac
import json

import frappe
from frappe import _


# Razorpay event types we handle. Other event types are acknowledged
# (200 OK) so Razorpay doesn't keep retrying, but otherwise ignored.
HANDLED_EVENTS = {
    "subscription.activated",
    "subscription.charged",
    "subscription.cancelled",
    "subscription.completed",
    "subscription.halted",
    "payment.failed",
    "payment.captured",
    # v0.3.0: one-time WhatsApp credit top-up payments
    "order.paid",
}


@frappe.whitelist(allow_guest=True)
def razorpay_webhook():
    """Razorpay webhook endpoint.

    Razorpay POSTs JSON with `X-Razorpay-Signature` header. We verify the
    HMAC SHA256 signature against the webhook secret stored in site
    config, then dispatch to the per-event handler.
    """
    raw_body = frappe.request.get_data() or b""
    signature = frappe.get_request_header("X-Razorpay-Signature") or ""

    if not _verify_razorpay_signature(raw_body, signature):
        frappe.local.response["http_status_code"] = 400
        return {"status": "invalid_signature"}

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        frappe.local.response["http_status_code"] = 400
        return {"status": "bad_json"}

    event = payload.get("event") or ""
    if event not in HANDLED_EVENTS:
        return {"status": "ignored", "event": event}

    handler = {
        "subscription.activated": _on_subscription_activated,
        "subscription.charged": _on_subscription_charged,
        "subscription.cancelled": _on_subscription_cancelled,
        "subscription.completed": _on_subscription_cancelled,
        "subscription.halted": _on_subscription_cancelled,
        "payment.failed": _on_payment_failed,
        "payment.captured": _on_subscription_charged,
        "order.paid": _on_order_paid,
    }[event]

    result = handler(payload)
    frappe.db.commit()
    return {"status": "ok", "event": event, "result": result}


def _verify_razorpay_signature(raw_body, signature):
    """HMAC-SHA256 verification per Razorpay webhook spec."""
    secret = frappe.conf.get("razorpay_webhook_secret") or ""
    if not secret:
        return False
    expected = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _on_subscription_activated(payload):
    """First successful charge → provision tenant site if not already, activate."""
    sub = (payload.get("payload") or {}).get("subscription", {}).get("entity") or {}
    sub_id = sub.get("id")
    if not sub_id:
        return {"error": "no_subscription_id"}

    tenant = _find_tenant_by_subscription(sub_id)
    if not tenant:
        # No matching tenant — likely a fresh signup. Trigger Press provisioning.
        notes = sub.get("notes") or {}
        return _provision_from_subscription(sub_id, notes)

    tenant.status = "Active"
    tenant.suspended = 0
    tenant.last_payment_at = frappe.utils.now()
    tenant.save(ignore_permissions=True)
    return {"tenant": tenant.name, "action": "activated"}


def _on_subscription_charged(payload):
    """Recurring charge succeeded → extend grace period."""
    sub_id = (payload.get("payload") or {}).get("subscription", {}).get("entity", {}).get("id")
    tenant = _find_tenant_by_subscription(sub_id) if sub_id else None
    if not tenant:
        return {"warning": "no_tenant_for_subscription", "subscription_id": sub_id}
    tenant.last_payment_at = frappe.utils.now()
    tenant.save(ignore_permissions=True)
    return {"tenant": tenant.name, "action": "charged"}


def _on_subscription_cancelled(payload):
    """Subscription ended → suspend site (read-only mode)."""
    sub_id = (payload.get("payload") or {}).get("subscription", {}).get("entity", {}).get("id")
    tenant = _find_tenant_by_subscription(sub_id) if sub_id else None
    if not tenant:
        return {"warning": "no_tenant_for_subscription"}
    tenant.status = "Suspended"
    tenant.suspended = 1
    tenant.save(ignore_permissions=True)
    return {"tenant": tenant.name, "action": "suspended"}


def _on_order_paid(payload):
    """One-time payment for WhatsApp credit top-up (v0.3.0).

    Razorpay's `order.paid` event fires when an Order (created via
    wallet.create_purchase_order) is fully paid. We hand off to
    wallet.apply_purchase which credits the wallet and marks the
    Purchase Order as Paid.
    """
    payload_obj = payload.get("payload") or {}
    order = (payload_obj.get("order") or {}).get("entity") or {}
    payment = (payload_obj.get("payment") or {}).get("entity") or {}
    order_id = order.get("id") or payment.get("order_id")
    payment_id = payment.get("id")
    if not order_id or not payment_id:
        return {"warning": "missing_order_or_payment_id"}

    from boonxpress_crm.api import wallet as wallet_api
    return wallet_api.apply_purchase(order_id, payment_id)


def _on_payment_failed(payload):
    """Mark tenant in dunning. n8n picks this up and sends WA reminder."""
    sub_id = (payload.get("payload") or {}).get("subscription", {}).get("entity", {}).get("id")
    tenant = _find_tenant_by_subscription(sub_id) if sub_id else None
    if not tenant:
        return {"warning": "no_tenant_for_subscription"}
    tenant.dunning = 1
    tenant.save(ignore_permissions=True)
    # n8n reads dunning=1 tenants on a daily schedule and sends WA reminders.
    # See n8n workflow `boon-dunning-reminder` (deferred to v0.3.0).
    return {"tenant": tenant.name, "action": "dunning_flagged"}


def _find_tenant_by_subscription(subscription_id):
    """Locate the Boon Tenant doc tied to a Razorpay subscription id."""
    if not frappe.db.exists("DocType", "Boon Tenant"):
        return None
    name = frappe.db.get_value(
        "Boon Tenant",
        {"razorpay_subscription_id": subscription_id},
        "name",
    )
    return frappe.get_doc("Boon Tenant", name) if name else None


def _provision_from_subscription(subscription_id, notes):
    """Fresh signup path: enqueue Press provisioning from Razorpay notes.

    `notes` should contain at minimum: business_name, vertical_type, owner_email.
    The signup landing page (admin.enabble.com / booncrm.in) attaches these
    as Razorpay subscription notes when creating the subscription.
    """
    business_name = notes.get("business_name") or notes.get("name") or "BoonCRM Tenant"
    vertical_type = notes.get("vertical_type") or "general"
    owner_email = notes.get("owner_email") or notes.get("email") or ""
    if not owner_email:
        return {"error": "missing_owner_email", "notes": notes}

    # Lazy import to keep this module importable without provisioning deps.
    from boonxpress_crm.api import provisioning

    slug = provisioning.slugify(business_name)
    tenant = frappe.get_doc({
        "doctype": "Boon Tenant",
        "slug": slug,
        "business_name": business_name,
        "vertical_type": vertical_type,
        "owner_email": owner_email,
        "razorpay_subscription_id": subscription_id,
        "status": "Provisioning",
    })
    tenant.insert(ignore_permissions=True)
    return {"tenant": tenant.name, "action": "provisioning_queued"}


# ─────────────────────────────────────────────────────────────────────
# 5-user cap enforcement (PRD §3.3 — "User Management — 5-user cap")
# ─────────────────────────────────────────────────────────────────────


def enforce_user_cap(doc, method=None):
    """`User` `before_insert` hook — block when active user count >= cap.

    Wired from hooks.py:
        doc_events = {"User": {"before_insert": "boonxpress_crm.api.billing.enforce_user_cap"}}
    """
    if doc.user_type != "System User":
        return  # Website users / API users don't count toward the cap.
    if doc.name in ("Administrator", "Guest"):
        return

    cap = int(frappe.conf.get("max_users") or 5)
    active_count = frappe.db.count(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
    )
    # The new user is being inserted, so the cap hits when active==cap (not >cap).
    if active_count >= cap:
        frappe.throw(
            _("User limit reached: this plan includes up to {0} users. Upgrade or disable an existing user first.").format(cap),
            frappe.ValidationError,
        )
