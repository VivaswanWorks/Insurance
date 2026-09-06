import frappe
from frappe.tests.utils import FrappeTestCase


class TestInsuranceSettings(FrappeTestCase):
	def test_doctype_exists(self):
		self.assertTrue(frappe.db.exists("DocType", "Insurance Settings"))
