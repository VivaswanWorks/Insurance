import frappe
from frappe import _
from frappe.model.document import Document


class SchemePremiumSlab(Document):
	def validate(self):
		self.set_missing_values()

	def set_missing_values(self):
		pass
