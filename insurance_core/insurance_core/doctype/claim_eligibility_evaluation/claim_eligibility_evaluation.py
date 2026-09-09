import frappe
from frappe import _
from frappe.model.document import Document


class ClaimEligibilityEvaluation(Document):
	def validate(self):
		if not self.evaluation_datetime:
			self.evaluation_datetime = frappe.utils.now_datetime()
		if not self.evaluated_by:
			self.evaluated_by = frappe.session.user

	def on_update(self):
		if self.overridden_by and not self.override_reason:
			frappe.throw(_("Override Reason is required when an override is applied."), title=_("Missing Override Reason"))
