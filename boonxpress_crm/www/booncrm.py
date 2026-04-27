import frappe
import json
import os

no_cache = 1


def get_context(context):
    """Build context for the BoonCRM SPA."""
    csrf_token = frappe.sessions.get_csrf_token()

    # Get vertical config
    vertical_type = frappe.conf.get("vertical_type", "general")
    business_name = frappe.conf.get("business_name", "BoonCRM")

    # Try to load from Boon Tenant Config if available
    config = None
    try:
        if frappe.db.exists("DocType", "Boon Tenant Config"):
            config_doc = frappe.get_single("Boon Tenant Config")
            if config_doc.config_json:
                config = json.loads(config_doc.config_json)
                business_name = config_doc.business_name or business_name
                vertical_type = config_doc.vertical_type or vertical_type
    except Exception:
        pass

    if not config:
        config_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "vertical_configs",
            f"{vertical_type}.json"
        )
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)

    context.csrf_token = csrf_token
    context.vertical_type = vertical_type
    context.business_name = business_name
    context.booncrm_config = json.dumps(config) if config else "{}"
