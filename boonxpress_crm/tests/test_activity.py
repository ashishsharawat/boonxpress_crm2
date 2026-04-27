"""Tests for boonxpress_crm.api.activity.get_feed()."""

import frappe
from frappe.tests.utils import FrappeTestCase

from boonxpress_crm.api.activity import get_feed
from boonxpress_crm.tests.conftest import make_lead, cleanup_test_records


class TestActivityFeed(FrappeTestCase):
    @classmethod
    def tearDownClass(cls):
        cleanup_test_records()
        super().tearDownClass()

    def test_empty_feed_for_new_lead(self):
        lead = make_lead()
        result = get_feed(person_id=lead.name)
        self.assertEqual(result["events"], [])
        self.assertIsNone(result["next_cursor"])

    def test_feed_includes_comment(self):
        lead = make_lead()
        c = frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Comment",
            "reference_doctype": "CRM Lead",
            "reference_name": lead.name,
            "content": "Note about this lead",
        })
        c.insert(ignore_permissions=True)
        result = get_feed(person_id=lead.name)
        note_events = [e for e in result["events"] if e["type"] == "note"]
        self.assertGreaterEqual(len(note_events), 1)
        self.assertTrue(any("Note about this lead" in e["content"] for e in note_events))

    def test_filter_chips_excludes_non_matching(self):
        lead = make_lead()
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Comment",
            "reference_doctype": "CRM Lead",
            "reference_name": lead.name,
            "content": "Note",
        }).insert(ignore_permissions=True)
        result = get_feed(person_id=lead.name, filter_type="messages")
        # Notes should be excluded from the messages filter
        types = {e["type"] for e in result["events"]}
        self.assertNotIn("note", types)

    def test_pagination_returns_cursor(self):
        lead = make_lead()
        for i in range(60):
            frappe.get_doc({
                "doctype": "Comment",
                "comment_type": "Comment",
                "reference_doctype": "CRM Lead",
                "reference_name": lead.name,
                "content": f"Note {i}",
            }).insert(ignore_permissions=True)
        result = get_feed(person_id=lead.name, page_size=50)
        self.assertEqual(len(result["events"]), 50)
        self.assertIsNotNone(result["next_cursor"])
