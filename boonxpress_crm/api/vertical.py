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


def refresh_config_from_disk():
    """Re-read `vertical_configs/<vertical_type>.json` and overwrite
    Boon Tenant Config.config_json on this site.

    Called by the after_migrate hook so each `bench migrate` picks up
    schema additions (new keys like conversion_mode, leads_segments,
    profile_fields, etc.) without manual UI edits.

    Existing tenants previously frozen on the JSON snapshot from their
    initial provisioning automatically get the latest schema after the
    next deploy + migrate cycle.

    Returns a dict describing what happened, useful when called via
    `bench execute` for debugging.
    """
    log = frappe.logger("boonxpress_crm")

    if not frappe.db.exists("DocType", "Boon Tenant Config"):
        log.info("refresh_config_from_disk: Boon Tenant Config doctype not present; skip")
        return {"status": "skipped", "reason": "doctype_missing"}

    config_doc = frappe.get_single("Boon Tenant Config")

    vertical_type = (
        config_doc.vertical_type
        or frappe.conf.get("vertical_type")
        or "general"
    )

    # Path resolution: __file__ is at apps/boonxpress_crm/boonxpress_crm/api/vertical.py
    # vertical_configs/ lives at apps/boonxpress_crm/vertical_configs/ (one level above
    # the Python package). Walk up two dirs from this file's parent.
    api_dir = os.path.dirname(os.path.abspath(__file__))            # .../boonxpress_crm/api
    pkg_dir = os.path.dirname(api_dir)                              # .../boonxpress_crm
    app_root = os.path.dirname(pkg_dir)                             # apps/boonxpress_crm
    config_path = os.path.join(app_root, "vertical_configs", f"{vertical_type}.json")

    if not os.path.exists(config_path):
        log.warning(f"refresh_config_from_disk: config file not found at {config_path}")
        return {"status": "skipped", "reason": "file_missing", "path": config_path}

    with open(config_path) as f:
        fresh_config = json.load(f)

    config_doc.config_json = json.dumps(fresh_config)
    config_doc.last_synced = frappe.utils.now()
    config_doc.save(ignore_permissions=True)
    frappe.db.commit()

    log.info(f"refresh_config_from_disk: refreshed {vertical_type} from {config_path}")
    return {
        "status": "refreshed",
        "vertical_type": vertical_type,
        "path": config_path,
        "keys": sorted(fresh_config.keys()),
    }
