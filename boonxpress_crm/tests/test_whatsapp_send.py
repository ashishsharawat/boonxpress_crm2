"""Tests for boonxpress_crm.api.whatsapp_send — template resolution.

The actual Meta API send needs WABA + phone number ID. Here we test
template resolution and the fallback-to-Communication path that runs
when frappe_whatsapp isn't installed.
"""

import os

import frappe
from frappe.tests.utils import FrappeTestCase

from boonxpress_crm.api.whatsapp_send import (
    _load_template_set,
    _templates_dir,
    VALID_TEMPLATES,
    send,
)


class TestTemplateLoading(FrappeTestCase):
    def test_templates_dir_exists(self):
        self.assertTrue(os.path.isdir(_templates_dir()))

    def test_all_verticals_have_templates(self):
        # Every vertical with a template JSON must define the 4 valid
        # templates so the welcome / reminder / re-engagement / consent
        # flows work uniformly.
        base = _templates_dir()
        for fname in os.listdir(base):
            if not fname.endswith(".json"):
                continue
            data = _load_template_set(fname[:-5])
            templates = data.get("templates") or {}
            for required in VALID_TEMPLATES:
                self.assertIn(required, templates, f"{fname} missing {required}")
                spec = templates[required]
                self.assertIn("meta_template_name", spec)
                self.assertIn("language_code", spec)
                self.assertIn("body_params", spec)

    def test_load_unknown_vertical_falls_back_to_general(self):
        result = _load_template_set("nonexistent_vertical_xyz")
        # general.json is shipped, so we should always get a template set
        self.assertIn("templates", result)


class TestSendValidation(FrappeTestCase):
    def test_invalid_template_rejected(self):
        result = send("not_a_real_template", "+919999900001", {})
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["reason"], "invalid_template")

    def test_missing_recipient_rejected(self):
        result = send("welcome", "", {})
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["reason"], "missing_recipient")

    def test_send_falls_back_when_frappe_whatsapp_missing(self):
        # frappe_whatsapp is not installed in the boonxpress_crm test
        # context; the wrapper should fall back to creating a Communication
        # entry rather than crashing.
        result = send(
            template="welcome",
            recipient="+919999900099",
            params={"name": "Test User"},
            vertical_type="general",
        )
        # Either truly sent (if installed) or queued via fallback — both ok
        self.assertIn(result["status"], ("sent", "queued"))
