import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class InsuranceCommunication(Document):
	def validate(self):
		self.set_missing_values()

	def set_missing_values(self):
		if not self.scheduled_at:
			self.scheduled_at = now_datetime()
		if self.related_doctype == "Insurance Policy" and self.related_name and not self.client:
			self.client = frappe.db.get_value("Insurance Policy", self.related_name, "client")
		if self.client and not self.recipient:
			self.recipient = frappe.db.get_value("Insurance Client", self.client, "email")
