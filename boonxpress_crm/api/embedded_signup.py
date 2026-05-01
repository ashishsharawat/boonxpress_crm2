"""WhatsApp Embedded Signup — Meta Tech Provider self-service flow.

Customer-facing flow:
1. User clicks "Connect WhatsApp" in Settings → frontend opens Meta's
   Embedded Signup popup (FB.login with config_id, response_type='code').
2. User authenticates with Meta + creates/selects WABA + phone number.
3. Frontend captures `code` (from FB.login callback) plus `phone_number_id`
   and `waba_id` (from postMessage `WA_EMBEDDED_SIGNUP` event).
4. Frontend POSTs all three to `boonxpress_crm.api.embedded_signup.complete`.
5. We exchange `code` → access_token via Graph API, register the webhook
   with the WABA, and create or update a `WhatsApp Account` doc on this
   tenant site (frappe_whatsapp's account doctype).

Configuration (Site Config):
- meta_app_id                              — our Facebook App ID
- meta_app_secret                          — our Facebook App secret
- meta_embedded_signup_config_id           — WhatsApp Configuration ID
                                             (Meta App > WhatsApp > Configurations)
- meta_redirect_uri (optional)             — must match Meta App settings
- meta_webhook_verify_token (per tenant)   — auto-generated if absent

PRD: §3.1 ("WhatsApp is Primary"), §5.2 (boon_whatsapp_ui).
"""

import json
import secrets

import frappe
from frappe import _


GRAPH_API_VERSION = "v20.0"


@frappe.whitelist()
def get_signup_config():
    """Return the public config the frontend needs to launch Embedded Signup.

    The frontend uses these to initialise the Facebook JS SDK + render the
    Continue with Facebook button. None of these values are secret.
    """
    return {
        "meta_app_id": frappe.conf.get("meta_app_id") or "",
        "config_id": frappe.conf.get("meta_embedded_signup_config_id") or "",
        "graph_api_version": GRAPH_API_VERSION,
        "ready": bool(
            frappe.conf.get("meta_app_id")
            and frappe.conf.get("meta_embedded_signup_config_id")
        ),
    }


@frappe.whitelist()
def complete(code, phone_number_id, waba_id, account_name=None):
    """Finalise an Embedded Signup. Exchanges the auth code for a long-lived
    access token, registers the webhook on the WABA, and creates the
    `WhatsApp Account` doc that frappe_whatsapp uses for sending.

    Args:
        code: Short-lived auth code from FB.login response_type='code'.
        phone_number_id: From the WA_EMBEDDED_SIGNUP postMessage event.
        waba_id: WhatsApp Business Account ID, also from the postMessage.
        account_name: Optional display name; defaults to "Default WhatsApp".

    Returns:
        { "ok": True, "whatsapp_account": "<docname>", "phone_number_id": "..." }
        or { "ok": False, "reason": "..." }.
    """
    if not code:
        return {"ok": False, "reason": "missing_code"}
    if not phone_number_id or not waba_id:
        return {"ok": False, "reason": "missing_phone_or_waba_id"}

    app_id = frappe.conf.get("meta_app_id")
    app_secret = frappe.conf.get("meta_app_secret")
    if not app_id or not app_secret:
        return {"ok": False, "reason": "platform_not_configured"}

    # Step 1: short-lived auth code → access_token (≈1h validity).
    short = _exchange_code_for_token(code, app_id, app_secret)
    if not short or not short.get("access_token"):
        return {"ok": False, "reason": "code_exchange_failed", "detail": short}

    # Step 2: short-lived → long-lived (60-day) token. Best-effort; some
    # Tech Provider configs return a non-expiring token from step 1, in
    # which case this no-ops gracefully.
    long = _exchange_for_long_lived(short["access_token"], app_id, app_secret) or short
    access_token = long.get("access_token") or short.get("access_token")

    # Step 3: register webhook on the WABA so incoming messages flow to us.
    verify_token = frappe.conf.get("meta_webhook_verify_token") or _generate_verify_token()
    sub_result = _subscribe_app_to_waba(waba_id, access_token)

    # Step 4: create or update WhatsApp Account doc (frappe_whatsapp).
    if not frappe.db.exists("DocType", "WhatsApp Account"):
        return {
            "ok": False,
            "reason": "frappe_whatsapp_not_installed",
            "hint": "Run `bench install-app frappe_whatsapp` on this site.",
        }

    existing_name = frappe.db.get_value(
        "WhatsApp Account",
        {"phone_id": phone_number_id},
        "name",
    )
    if existing_name:
        account = frappe.get_doc("WhatsApp Account", existing_name)
    else:
        account = frappe.new_doc("WhatsApp Account")
    account.account_name = account_name or "Default WhatsApp"
    account.url = "https://graph.facebook.com"
    account.version = GRAPH_API_VERSION
    account.token = access_token  # Frappe Password fieldtype encrypts on save
    account.phone_id = phone_number_id
    account.business_id = waba_id
    account.app_id = app_id
    account.webhook_verify_token = verify_token
    account.is_default_outgoing = 1
    account.is_default_incoming = 1
    account.status = "Active" if hasattr(account, "status") else None
    account.save(ignore_permissions=True)
    frappe.db.commit()

    # Mark the tenant config so the frontend "Connect" button can show
    # connected state without re-querying frappe_whatsapp.
    try:
        if frappe.db.exists("DocType", "Boon Tenant Config"):
            cfg = frappe.get_single("Boon Tenant Config")
            cfg.whatsapp_connected = 1
            cfg.whatsapp_phone_id = phone_number_id
            cfg.whatsapp_waba_id = waba_id
            cfg.save(ignore_permissions=True)
            frappe.db.commit()
    except Exception:
        # Boon Tenant Config may not have these fields yet; that's fine —
        # the WhatsApp Account doc is the source of truth.
        pass

    return {
        "ok": True,
        "whatsapp_account": account.name,
        "phone_number_id": phone_number_id,
        "waba_id": waba_id,
        "subscription": sub_result,
    }


@frappe.whitelist()
def disconnect():
    """Remove the connected WhatsApp Account on this tenant site.

    Soft action — disables the account rather than deleting (preserves
    activity-log history). Re-connecting the same number reactivates it.
    """
    if not frappe.db.exists("DocType", "WhatsApp Account"):
        return {"ok": False, "reason": "frappe_whatsapp_not_installed"}

    accounts = frappe.get_all(
        "WhatsApp Account",
        filters={"is_default_outgoing": 1},
        pluck="name",
    )
    for name in accounts:
        doc = frappe.get_doc("WhatsApp Account", name)
        doc.is_default_outgoing = 0
        doc.is_default_incoming = 0
        if hasattr(doc, "status"):
            doc.status = "Inactive"
        doc.save(ignore_permissions=True)

    try:
        cfg = frappe.get_single("Boon Tenant Config")
        cfg.whatsapp_connected = 0
        cfg.save(ignore_permissions=True)
    except Exception:
        pass

    frappe.db.commit()
    return {"ok": True, "disabled": accounts}


@frappe.whitelist()
def status():
    """Frontend uses this to show connected/disconnected state in Settings."""
    if not frappe.db.exists("DocType", "WhatsApp Account"):
        return {"connected": False, "reason": "frappe_whatsapp_not_installed"}
    rows = frappe.get_all(
        "WhatsApp Account",
        filters={"is_default_outgoing": 1},
        fields=["name", "account_name", "phone_id", "business_id"],
    )
    if not rows:
        return {"connected": False}
    row = rows[0]
    return {
        "connected": True,
        "account_name": row.get("account_name"),
        "phone_id": row.get("phone_id"),
        "business_id": row.get("business_id"),
    }


# ---------------------------------------------------------------------
# Helpers — Graph API calls
# ---------------------------------------------------------------------

def _exchange_code_for_token(code, app_id, app_secret):
    import urllib.parse
    import urllib.request

    redirect_uri = frappe.conf.get("meta_redirect_uri") or ""
    qs = urllib.parse.urlencode({
        "client_id": app_id,
        "client_secret": app_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    })
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/oauth/access_token?{qs}"
    return _graph_get(url)


def _exchange_for_long_lived(short_token, app_id, app_secret):
    import urllib.parse

    qs = urllib.parse.urlencode({
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_token,
    })
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/oauth/access_token?{qs}"
    return _graph_get(url)


def _subscribe_app_to_waba(waba_id, access_token):
    """Register our webhook receiver on this WABA. Required for inbound."""
    import urllib.request

    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{waba_id}/subscribed_apps"
    req = urllib.request.Request(
        url,
        method="POST",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        data=b"",
    )
    try:
        import urllib.request
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        frappe.log_error(f"WABA subscribe failed: {e}", "boonxpress_crm.embedded_signup")
        return {"warning": str(e)}


def _graph_get(url):
    import urllib.request

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        frappe.log_error(f"Graph GET failed for {url[:80]}...: {e}", "boonxpress_crm.embedded_signup")
        return None


def _generate_verify_token():
    return secrets.token_urlsafe(24)
