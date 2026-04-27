import frappe
import json
import os


@frappe.whitelist()
def get_config():
    """Get the vertical configuration for the current site.

    Reads from Boon Tenant Config (Single DocType) if it exists,
    otherwise falls back to the default config based on site_config vertical_type.
    """
    try:
        # Try reading from Boon Tenant Config Single DocType
        if frappe.db.exists("DocType", "Boon Tenant Config"):
            config_doc = frappe.get_single("Boon Tenant Config")
            if config_doc.config_json:
                config = json.loads(config_doc.config_json)
                config["business_name"] = config_doc.business_name or config.get("display_name", "BoonCRM")
                return config
    except Exception:
        pass

    # Fallback: read vertical_type from site_config
    vertical_type = frappe.conf.get("vertical_type", "general")

    # Load default config from JSON file
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "vertical_configs",
        f"{vertical_type}.json"
    )

    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
    else:
        # Ultimate fallback: general config
        general_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "vertical_configs",
            "general.json"
        )
        with open(general_path, "r") as f:
            config = json.load(f)

    # Add business name from site config
    config["business_name"] = frappe.conf.get("business_name", config.get("display_name", "BoonCRM"))

    return config


@frappe.whitelist()
def set_config(config_json=None, vertical_type=None, business_name=None):
    """Update the vertical configuration on this tenant site.

    Called by the control site's sync module when admin changes vertical_type.
    """
    if not frappe.db.exists("DocType", "Boon Tenant Config"):
        frappe.throw("Boon Tenant Config DocType not found on this site")

    config_doc = frappe.get_single("Boon Tenant Config")

    if config_json:
        config_doc.config_json = config_json if isinstance(config_json, str) else json.dumps(config_json)

    if vertical_type:
        config_doc.vertical_type = vertical_type

    if business_name:
        config_doc.business_name = business_name

    config_doc.last_synced = frappe.utils.now()
    config_doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {"status": "ok", "vertical_type": config_doc.vertical_type}
