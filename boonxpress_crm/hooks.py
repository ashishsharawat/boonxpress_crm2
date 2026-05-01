app_name = "boonxpress_crm"
app_title = "BoonXpress CRM"
app_description = "Multi-tenant mobile-first CRM with vertical-specific UI skins"
app_publisher = "Boon Xpress"
app_email = "dev@boonxpress.com"
app_license = "MIT"

# Website route rules for SPA
website_route_rules = [
    {"from_route": "/booncrm/<path:app_path>", "to_route": "booncrm"},
]

# Doc Events
doc_events = {
    "Boon Tenant": {
        "after_insert": "boonxpress_crm.api.provisioning.on_tenant_created",
        "on_update": "boonxpress_crm.api.sync.on_tenant_updated",
    },
    # 5-user cap (PRD §3.3 — User Management 5-user cap)
    "User": {
        "before_insert": "boonxpress_crm.api.billing.enforce_user_cap",
    },
    # Auto-send vertical-specific welcome WhatsApp on lead creation.
    # Falls back to logging a Communication entry if frappe_whatsapp
    # isn't installed yet — safe to enable before WABA verification.
    "CRM Lead": {
        "after_insert": "boonxpress_crm.api.whatsapp_send.on_lead_after_insert",
    },
}

# Scheduler Events
scheduler_events = {
    "hourly": [
        "boonxpress_crm.api.appointments.send_appointment_reminders",
    ],
}

# After every `bench migrate`, refresh the cached vertical config on this
# site from the latest JSON shipped in vertical_configs/. Existing tenants
# automatically pick up new schema keys (conversion_mode, leads_segments,
# profile_fields, etc.) without manual UI edits.
#
# v0.3.0: also seed the WhatsApp Conversation Pricing table on first
# migrate so wallet.check_and_reserve has prices available without a
# manual setup step.
after_migrate = [
    "boonxpress_crm.api.vertical.refresh_config_from_disk",
    "boonxpress_crm.api.wallet.seed_pricing_table",
]

# After fresh app install on a tenant site — load per-vertical sample
# data so the dashboard isn't empty on first login. Idempotent: checks
# Boon Tenant Config.sample_data_loaded first.
after_install = "boonxpress_crm.api.onboarding.after_install"
