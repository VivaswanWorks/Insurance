import frappe
from frappe.tests.utils import FrappeTestCase


class TestNetworkHospital(FrappeTestCase):
	def test_doctype_exists(self):
		self.assertTrue(frappe.db.exists("DocType", "Network Hospital"))
