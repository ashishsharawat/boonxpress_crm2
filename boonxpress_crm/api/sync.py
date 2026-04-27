import frappe
import json
import requests


@frappe.whitelist()
def on_tenant_updated(doc, method):
    """Triggered when a Boon Tenant record is updated on the control site.

    If vertical_type changed, push new config to the tenant site.
    """
    if doc.has_value_changed("vertical_type") and doc.status == "Active":
        frappe.enqueue(
            "boonxpress_crm.api.sync.push_config",
            queue="short",
            tenant_slug=doc.slug,
        )


def push_config(tenant_slug):
    """Push vertical config from control site to a tenant site.

    Reads the Boon Vertical Template, builds the full config JSON,
    and calls set_config on the tenant site.
    """
    tenant = frappe.get_doc("Boon Tenant", tenant_slug)

    if not tenant.site_url or tenant.status != "Active":
        frappe.logger().warning(f"Cannot push config to {tenant_slug}: site not active")
        return

    # Get the vertical template
    template_name = tenant.vertical_type
    if not frappe.db.exists("Boon Vertical Template", template_name):
        frappe.log_error(f"Vertical template {template_name} not found", "Config Sync Error")
        return

    template = frappe.get_doc("Boon Vertical Template", template_name)

    # Build config JSON from template
    config = {
        "vertical_type": template.template_name,
        "display_name": template.display_name,
        "icon": template.icon or "",
        "color_scheme": json.loads(template.color_scheme or "{}"),
        "nav_items": json.loads(template.nav_items or "[]"),
        "home_component": template.home_component or "GeneralHome",
        "visible_modules": json.loads(template.visible_modules or "[]"),
        "hidden_modules": json.loads(template.hidden_modules or "[]"),
        "contact_fields": json.loads(template.contact_fields or "[]"),
        "lead_fields": json.loads(template.lead_fields or "[]"),
        "stats_config": json.loads(template.stats_config or "[]"),
        "terminology": json.loads(template.terminology or "{}"),
        "fab_actions": json.loads(template.fab_actions or "[]"),
    }

    # Push to tenant site
    site_url = tenant.site_url
    if not site_url.startswith("http"):
        site_url = f"https://{site_url}"

    api_key = tenant.api_key
    api_secret = tenant.get_password("api_secret") if tenant.api_secret else ""

    if not api_key or not api_secret:
        frappe.log_error(f"No API credentials for tenant {tenant_slug}", "Config Sync Error")
        return

    try:
        response = requests.post(
            f"{site_url}/api/method/boonxpress_crm.api.vertical.set_config",
            json={
                "config_json": json.dumps(config),
                "vertical_type": template.template_name,
                "business_name": tenant.business_name,
            },
            headers={
                "Authorization": f"token {api_key}:{api_secret}",
            },
            timeout=30,
        )

        if response.status_code == 200:
            frappe.logger().info(f"Config pushed to {tenant_slug} successfully")
        else:
            frappe.log_error(
                f"Failed to push config to {tenant_slug}: {response.status_code} {response.text}",
                "Config Sync Error"
            )
    except Exception as e:
        frappe.log_error(f"Config sync failed for {tenant_slug}: {str(e)}", "Config Sync Error")
