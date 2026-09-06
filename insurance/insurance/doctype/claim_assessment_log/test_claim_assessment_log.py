import frappe
from frappe.tests.utils import FrappeTestCase


class TestClaimAssessmentLog(FrappeTestCase):
	def test_doctype_exists(self):
		self.assertTrue(frappe.db.exists("DocType", "Claim Assessment Log"))
