"""First-login onboarding — sample data loader + checklist API.

When a tenant site is first provisioned, we load vertical-specific
fixture data (a few leads, contacts, appointments) so the dashboard
isn't empty on first login. We also expose a checklist API that the
frontend uses to drive the "set up your CRM" first-login experience.

Sample data lives at:
    boonxpress_crm/fixtures/sample_data/<vertical_type>.json

Checklist state is stored in `Boon Tenant Config`:
    onboarding_checklist_completed   (JSON-encoded list of step keys)
    sample_data_loaded               (boolean)

PRD: §3.3 (Automated Notifications, sample pipeline stages, WA template
library), §5.2 (boon_onboarding), §7 P1 ("first-login checklist").
"""

import json
import os

import frappe


CHECKLIST_STEPS = [
    {"key": "connect_whatsapp", "label": "Connect WhatsApp Business", "icon": "MessageCircle"},
    {"key": "invite_team", "label": "Invite your team", "icon": "Users"},
    {"key": "import_contacts", "label": "Import existing customers", "icon": "Upload"},
    {"key": "first_lead", "label": "Add your first lead", "icon": "UserPlus"},
    {"key": "set_business_hours", "label": "Set business hours", "icon": "Clock"},
]


def _fixtures_dir():
    api_dir = os.path.dirname(os.path.abspath(__file__))
    pkg_dir = os.path.dirname(api_dir)
    return os.path.join(pkg_dir, "fixtures", "sample_data")


def load_sample_data(vertical_type=None):
    """Load per-vertical sample fixtures into the current site.

    Idempotent: checks `Boon Tenant Config.sample_data_loaded` first.
    Returns a summary dict for logging.
    """
    if not frappe.db.exists("DocType", "Boon Tenant Config"):
        return {"status": "skipped", "reason": "boon_tenant_config_missing"}

    cfg = frappe.get_single("Boon Tenant Config")
    if getattr(cfg, "sample_data_loaded", 0):
        return {"status": "skipped", "reason": "already_loaded"}

    if not vertical_type:
        vertical_type = cfg.vertical_type or "general"

    path = os.path.join(_fixtures_dir(), f"{vertical_type}.json")
    if not os.path.exists(path):
        # Fall back to general
        path = os.path.join(_fixtures_dir(), "general.json")
    if not os.path.exists(path):
        return {"status": "no_fixtures", "vertical_type": vertical_type}

    with open(path) as f:
        fixtures = json.load(f)

    counts = {}
    for record in fixtures.get("records", []) or []:
        doctype = record.pop("doctype", None)
        if not doctype:
            continue
        if not frappe.db.exists("DocType", doctype):
            continue
        try:
            doc = frappe.get_doc({"doctype": doctype, **record})
            doc.insert(ignore_permissions=True)
            counts[doctype] = counts.get(doctype, 0) + 1
        except Exception as e:
            frappe.log_error(f"Sample data insert failed ({doctype}): {e}", "boonxpress_crm.onboarding")

    cfg.sample_data_loaded = 1
    cfg.save(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "loaded", "vertical_type": vertical_type, "counts": counts}


@frappe.whitelist()
def get_checklist():
    """Return the onboarding checklist with completed-state per step."""
    completed = []
    if frappe.db.exists("DocType", "Boon Tenant Config"):
        cfg = frappe.get_single("Boon Tenant Config")
        raw = getattr(cfg, "onboarding_checklist_completed", None)
        if raw:
            try:
                completed = json.loads(raw) if isinstance(raw, str) else list(raw)
            except (ValueError, TypeError):
                completed = []

    completed_set = set(completed)
    return [
        {**step, "completed": step["key"] in completed_set}
        for step in CHECKLIST_STEPS
    ]


@frappe.whitelist()
def mark_step_complete(step_key):
    """Mark a checklist step as complete."""
    if step_key not in {s["key"] for s in CHECKLIST_STEPS}:
        frappe.throw(f"Unknown checklist step: {step_key}")
    if not frappe.db.exists("DocType", "Boon Tenant Config"):
        return {"status": "no_config_doctype"}

    cfg = frappe.get_single("Boon Tenant Config")
    raw = getattr(cfg, "onboarding_checklist_completed", None) or "[]"
    try:
        completed = json.loads(raw) if isinstance(raw, str) else list(raw)
    except (ValueError, TypeError):
        completed = []

    if step_key not in completed:
        completed.append(step_key)
        cfg.onboarding_checklist_completed = json.dumps(completed)
        cfg.save(ignore_permissions=True)
        frappe.db.commit()

    return {"status": "ok", "completed": completed}


def after_install():
    """Frappe `after_install` hook — load sample data on fresh tenant install."""
    try:
        result = load_sample_data()
        frappe.logger("boonxpress_crm").info(f"after_install sample data: {result}")
    except Exception as e:
        frappe.log_error(f"after_install sample data failed: {e}", "boonxpress_crm.onboarding")
