import frappe
from frappe.tests.utils import FrappeTestCase


class TestComplianceRecord(FrappeTestCase):
	def test_doctype_exists(self):
		self.assertTrue(frappe.db.exists("DocType", "Compliance Record"))
