"""BoonCRM SPA www page — serves the built Vue 3 SPA shell.

Reads the Vite-generated manifest at request time to inject
content-hashed asset URLs into the template, so cache invalidation is
path-based (survives Cloudflare). Also injects vertical config and
current user info so the Vue app can decide whether to show the login
screen or the main app.
"""

import json
import os

import frappe


no_cache = 1
sitemap = 0


_MANIFEST_PATHS = [
    # Vite 5 default location
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "public",
        "frontend",
        ".vite",
        "manifest.json",
    ),
    # Older Vite versions
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "public",
        "frontend",
        "manifest.json",
    ),
]


def _load_manifest():
    """Return parsed Vite manifest dict, or empty dict if not found."""
    for path in _MANIFEST_PATHS:
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                continue
    return {}


def _resolve_assets(manifest):
    """Find the entry chunk and its CSS in the Vite manifest.

    Returns (index_js, index_css) as URL paths under
    /assets/boonxpress_crm/frontend/. Falls back to non-hashed
    names if the manifest is unavailable.
    """
    base = "/assets/boonxpress_crm/frontend/"
    entry = None
    for value in manifest.values():
        if value.get("isEntry"):
            entry = value
            break

    if not entry:
        return base + "assets/index.js", base + "assets/index.css"

    js = base + entry["file"]
    css = ""
    css_files = entry.get("css") or []
    if css_files:
        css = base + css_files[0]
    return js, css


def get_context(context):
    """Build context for the BoonCRM SPA template."""
    csrf_token = frappe.sessions.get_csrf_token()
    vertical_type = frappe.conf.get("vertical_type", "general")
    business_name = frappe.conf.get("business_name", "BoonCRM")

    config = None
    try:
        if frappe.db.exists("DocType", "Boon Tenant Config"):
            doc = frappe.get_single("Boon Tenant Config")
            if doc.config_json:
                config = json.loads(doc.config_json)
                business_name = doc.business_name or business_name
                vertical_type = doc.vertical_type or vertical_type
    except Exception:
        pass

    if not config:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "..",
            "vertical_configs",
            f"{vertical_type}.json",
        )
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)

    if config is None:
        config = {"vertical_type": "general", "display_name": "BoonCRM"}

    config["business_name"] = business_name

    user_info = None
    if frappe.session.user and frappe.session.user != "Guest":
        try:
            user_doc = frappe.db.get_value(
                "User",
                frappe.session.user,
                ["full_name", "email", "user_image"],
                as_dict=True,
            )
            if user_doc:
                user_info = {
                    "email": frappe.session.user,
                    "full_name": user_doc.get("full_name"),
                    "image": user_doc.get("user_image"),
                }
        except Exception:
            pass

    manifest = _load_manifest()
    index_js, index_css = _resolve_assets(manifest)

    context.csrf_token = csrf_token
    context.vertical_type = vertical_type
    context.business_name = business_name
    context.booncrm_config = json.dumps(config)
    context.booncrm_user = json.dumps(user_info)
    context.index_js = index_js
    context.index_css = index_css
    context.safe_render = False
