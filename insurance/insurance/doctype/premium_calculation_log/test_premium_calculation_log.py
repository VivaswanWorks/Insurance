import frappe
from frappe.tests.utils import FrappeTestCase


class TestPremiumCalculationLog(FrappeTestCase):
	def test_doctype_exists(self):
		self.assertTrue(frappe.db.exists("DocType", "Premium Calculation Log"))
