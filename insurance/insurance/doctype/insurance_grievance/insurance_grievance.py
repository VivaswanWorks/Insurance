import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, nowdate

from insurance.tasks import queue_communication


class InsuranceGrievance(Document):
	def validate(self):
		self.set_missing_values()

	def set_missing_values(self):
		if not self.due_date:
			self.due_date = add_days(nowdate(), self.tat_days or 15)
		if not self.grievance_number:
			self.grievance_number = self.name
		if self.status == "Resolved" and not self.resolved_on:
			self.resolved_on = nowdate()

	def after_insert(self):
		queue_communication(
			template="Grievance Acknowledgement",
			subject=_("Grievance {0} acknowledged").format(self.grievance_number or self.name),
			related_doctype="Insurance Grievance",
			related_name=self.name,
			client=self.client,
			body=_("We have received your grievance {0}.").format(self.grievance_number or self.name),
		)
