"""Tests for boonxpress_crm.api.onboarding — checklist + sample data."""

import os

import frappe
from frappe.tests.utils import FrappeTestCase

from boonxpress_crm.api.onboarding import (
    CHECKLIST_STEPS,
    _fixtures_dir,
    get_checklist,
    mark_step_complete,
)


class TestOnboardingChecklist(FrappeTestCase):
    def test_checklist_has_required_steps(self):
        keys = {s["key"] for s in CHECKLIST_STEPS}
        # Every step the PRD §3.3 listed for first-login must exist
        for required in ("connect_whatsapp", "invite_team", "import_contacts"):
            self.assertIn(required, keys)

    def test_get_checklist_returns_completion_state(self):
        result = get_checklist()
        self.assertEqual(len(result), len(CHECKLIST_STEPS))
        for item in result:
            self.assertIn("key", item)
            self.assertIn("label", item)
            self.assertIn("completed", item)

    def test_unknown_step_rejected(self):
        with self.assertRaises(Exception):
            mark_step_complete("not_a_real_step")


class TestSampleDataFixtures(FrappeTestCase):
    def test_fixtures_dir_exists(self):
        self.assertTrue(os.path.isdir(_fixtures_dir()))

    def test_general_fixture_present(self):
        # general.json is the always-available fallback
        path = os.path.join(_fixtures_dir(), "general.json")
        self.assertTrue(os.path.exists(path))

    def test_at_least_one_vertical_fixture_present(self):
        # We ship sample data for at least salon, medspa, usedcar
        names = {f for f in os.listdir(_fixtures_dir()) if f.endswith(".json")}
        for required in ("salon.json", "general.json"):
            self.assertIn(required, names)
