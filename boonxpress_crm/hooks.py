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
}

# Scheduler Events
scheduler_events = {
    "hourly": [
        "boonxpress_crm.api.appointments.send_appointment_reminders",
    ],
}
