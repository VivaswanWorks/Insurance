from frappe.model.document import Document
from frappe.utils import date_diff, nowdate


class PolicyMember(Document):
	def validate(self):
		self.set_missing_values()

	def set_missing_values(self):
		if self.date_of_birth and not self.age:
			self.age = int(date_diff(nowdate(), self.date_of_birth) / 365.25)
