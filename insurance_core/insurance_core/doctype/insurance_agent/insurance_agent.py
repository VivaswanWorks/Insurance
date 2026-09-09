import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class InsuranceAgent(Document):
	def validate(self):
		self.set_missing_values()
		if self.license_valid_upto and getdate(self.license_valid_upto) < getdate(nowdate()):
			if self.status == "Active":
				self.status = "Suspended"
				frappe.msgprint(
					_("Agent license expired. Status set to Suspended."),
					title=_("License Expired"),
					indicator="orange",
				)

	def set_missing_values(self):
		if not self.agent_code and self.agent_name:
			from frappe.model.naming import make_autoname

			self.agent_code = make_autoname("AGT-.#####")
