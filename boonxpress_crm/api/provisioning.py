import frappe
import subprocess
import secrets
import string


@frappe.whitelist()
def on_tenant_created(doc, method):
    """Triggered after a Boon Tenant record is created on the control site.

    Enqueues the actual site provisioning as a background job.
    """
    frappe.enqueue(
        "boonxpress_crm.api.provisioning.provision_tenant",
        queue="long",
        timeout=600,
        slug=doc.slug,
        business_name=doc.business_name,
        owner_email=doc.owner_email,
        vertical_type=doc.vertical_type,
    )


def provision_tenant(slug, business_name, owner_email, vertical_type):
    """Provision a new Frappe CRM site for a tenant.

    This runs as a background job on the control site.
    Steps:
    1. Create new Frappe site with isolated MariaDB database
    2. Install required apps (frappe, crm, boonxpress_crm)
    3. Create admin user with API key
    4. Set vertical config on the new site
    5. Update Boon Tenant status to Active
    """
    site_domain = frappe.conf.get("tenant_domain", "enabble.com")
    site_name = f"{slug}.{site_domain}"
    bench_path = frappe.conf.get("bench_path", "/home/frappe/frappe-bench")
    db_root_password = frappe.conf.get("mariadb_root_password", "")

    admin_password = _generate_password()

    try:
        # Step 1: Create site
        _run_bench(bench_path, [
            "new-site", site_name,
            "--mariadb-root-password", db_root_password,
            "--admin-password", admin_password,
            "--no-mariadb-socket",
        ])

        # Step 2: Install apps
        # frappe_whatsapp is included so every tenant can connect their own
        # WABA via Embedded Signup (v0.4.0). The app must already be in the
        # Press bench (added once per bench, not per tenant); if it isn't
        # we log + continue so provisioning doesn't fail on greenfield benches.
        apps_to_install = ["crm", "boonxpress_crm", "frappe_whatsapp"]
        for app in apps_to_install:
            try:
                _run_bench(bench_path, [
                    "--site", site_name,
                    "install-app", app,
                ])
            except subprocess.CalledProcessError as e:
                if app == "frappe_whatsapp":
                    frappe.log_error(
                        f"frappe_whatsapp not yet present in bench {bench_path}; "
                        f"site {site_name} will need manual install once added. {e}",
                        "boonxpress_crm.provisioning",
                    )
                    continue
                raise

        # Step 3: Set site config
        _run_bench(bench_path, [
            "--site", site_name,
            "set-config", "vertical_type", vertical_type,
        ])
        _run_bench(bench_path, [
            "--site", site_name,
            "set-config", "business_name", business_name,
        ])

        # Step 4: Enable scheduler
        _run_bench(bench_path, [
            "--site", site_name,
            "enable-scheduler",
        ])

        # Step 5: Update tenant record
        tenant = frappe.get_doc("Boon Tenant", slug)
        tenant.status = "Active"
        tenant.site_url = site_name
        tenant.admin_password = admin_password
        tenant.activated_at = frappe.utils.now()
        tenant.save(ignore_permissions=True)
        frappe.db.commit()

        frappe.logger().info(f"Tenant {slug} provisioned successfully at {site_name}")

    except Exception as e:
        # Rollback: try to drop the site if it was created
        try:
            _run_bench(bench_path, [
                "drop-site", site_name,
                "--mariadb-root-password", db_root_password,
                "--no-backup",
            ])
        except Exception:
            pass

        # Update tenant status to failed
        try:
            tenant = frappe.get_doc("Boon Tenant", slug)
            tenant.status = "Failed"
            tenant.notes = (tenant.notes or "") + f"\nProvisioning failed: {str(e)}"
            tenant.save(ignore_permissions=True)
            frappe.db.commit()
        except Exception:
            pass

        frappe.log_error(f"Failed to provision tenant {slug}: {str(e)}", "Tenant Provisioning Error")
        raise


def deprovision_tenant(slug, take_backup=True):
    """Deprovision (deactivate) a tenant site."""
    site_domain = frappe.conf.get("tenant_domain", "enabble.com")
    site_name = f"{slug}.{site_domain}"
    bench_path = frappe.conf.get("bench_path", "/home/frappe/frappe-bench")
    db_root_password = frappe.conf.get("mariadb_root_password", "")

    try:
        if take_backup:
            _run_bench(bench_path, ["--site", site_name, "backup"])

        _run_bench(bench_path, [
            "drop-site", site_name,
            "--mariadb-root-password", db_root_password,
        ])

        tenant = frappe.get_doc("Boon Tenant", slug)
        tenant.status = "Deactivated"
        tenant.save(ignore_permissions=True)
        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Failed to deprovision tenant {slug}: {str(e)}", "Tenant Deprovisioning Error")
        raise


def _generate_password(length=16):
    chars = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(secrets.choice(chars) for _ in range(length))


def _run_bench(bench_path, args, timeout=300):
    cmd = ["bench"] + args
    result = subprocess.run(
        cmd,
        cwd=bench_path,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise Exception(f"bench command failed: {' '.join(args)}\n{result.stderr}")
    return result.stdout
