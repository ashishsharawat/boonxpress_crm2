"""Tests for boonxpress_crm.api.embedded_signup — input validation +
config endpoint behavior.

Live token-exchange flows require Meta Business + WhatsApp App config and
are deferred until those are set up. We cover the locally-testable parts:
config endpoint shape, input validation, missing-platform handling.
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from boonxpress_crm.api import embedded_signup


class TestSignupConfig(FrappeTestCase):
    """get_signup_config returns the right shape and ready-flag."""

    def setUp(self):
        super().setUp()
        self._original_app_id = frappe.conf.get("meta_app_id")
        self._original_config_id = frappe.conf.get("meta_embedded_signup_config_id")

    def tearDown(self):
        if self._original_app_id is None:
            frappe.conf.pop("meta_app_id", None)
        else:
            frappe.conf["meta_app_id"] = self._original_app_id
        if self._original_config_id is None:
            frappe.conf.pop("meta_embedded_signup_config_id", None)
        else:
            frappe.conf["meta_embedded_signup_config_id"] = self._original_config_id
        super().tearDown()

    def test_not_ready_when_unconfigured(self):
        frappe.conf.pop("meta_app_id", None)
        frappe.conf.pop("meta_embedded_signup_config_id", None)
        result = embedded_signup.get_signup_config()
        self.assertFalse(result["ready"])
        self.assertEqual(result["meta_app_id"], "")
        self.assertEqual(result["config_id"], "")

    def test_ready_when_both_keys_set(self):
        frappe.conf["meta_app_id"] = "test_fb_app_id_123"
        frappe.conf["meta_embedded_signup_config_id"] = "test_config_id_456"
        result = embedded_signup.get_signup_config()
        self.assertTrue(result["ready"])
        self.assertEqual(result["meta_app_id"], "test_fb_app_id_123")
        self.assertEqual(result["config_id"], "test_config_id_456")

    def test_returns_graph_api_version(self):
        result = embedded_signup.get_signup_config()
        # We're standardised on v20.0; if Meta deprecates, update here + in module constant
        self.assertEqual(result["graph_api_version"], "v20.0")


class TestCompleteValidation(FrappeTestCase):
    """The complete() endpoint rejects malformed inputs cleanly."""

    def test_missing_code_rejected(self):
        result = embedded_signup.complete(code="", phone_number_id="123", waba_id="456")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "missing_code")

    def test_missing_phone_id_rejected(self):
        result = embedded_signup.complete(code="abc", phone_number_id="", waba_id="456")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "missing_phone_or_waba_id")

    def test_missing_waba_id_rejected(self):
        result = embedded_signup.complete(code="abc", phone_number_id="123", waba_id="")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "missing_phone_or_waba_id")

    def test_unconfigured_platform_rejects_complete(self):
        original_app_id = frappe.conf.get("meta_app_id")
        original_secret = frappe.conf.get("meta_app_secret")
        frappe.conf.pop("meta_app_id", None)
        frappe.conf.pop("meta_app_secret", None)
        try:
            result = embedded_signup.complete(code="abc", phone_number_id="123", waba_id="456")
            self.assertFalse(result["ok"])
            self.assertEqual(result["reason"], "platform_not_configured")
        finally:
            if original_app_id is not None:
                frappe.conf["meta_app_id"] = original_app_id
            if original_secret is not None:
                frappe.conf["meta_app_secret"] = original_secret


class TestStatusEndpoint(FrappeTestCase):
    def test_returns_disconnected_when_no_account(self):
        # On a test site with no WhatsApp Account doc, status() should be safe
        result = embedded_signup.status()
        self.assertIn("connected", result)
        # Either we don't have the doctype (frappe_whatsapp absent) or no rows
        if not result["connected"]:
            self.assertTrue(
                result.get("reason") == "frappe_whatsapp_not_installed"
                or "reason" not in result
            )

    def test_disconnect_safe_when_nothing_to_disconnect(self):
        # Should not raise when no account exists
        result = embedded_signup.disconnect()
        self.assertIn("ok", result)
