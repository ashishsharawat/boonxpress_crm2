"""Sanity check that the test framework is wired up."""

import frappe
from frappe.tests.utils import FrappeTestCase


class TestSanity(FrappeTestCase):
    def test_frappe_imports(self):
        self.assertIsNotNone(frappe)

    def test_app_installed(self):
        installed = frappe.get_installed_apps()
        self.assertIn("boonxpress_crm", installed)
