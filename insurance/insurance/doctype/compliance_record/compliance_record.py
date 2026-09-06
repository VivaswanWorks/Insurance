import frappe
from frappe.model.document import Document


class ComplianceRecord(Document):
	def validate(self):
		self.set_missing_values()

	def set_missing_values(self):
		pass

	def on_update(self):
		if hasattr(self, "sync_linked_apps"):
			self.sync_linked_apps()
