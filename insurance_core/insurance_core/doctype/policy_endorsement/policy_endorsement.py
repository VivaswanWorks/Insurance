import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime, nowdate


class PolicyEndorsement(Document):
	def validate(self):
		self.set_missing_values()
		if not self.policy:
			frappe.throw(_("Policy is required."), title=_("Missing Policy"))

	def set_missing_values(self):
		if not self.effective_date:
			self.effective_date = nowdate()
		if not self.endorsement_number:
			self.endorsement_number = self.name

	def on_update(self):
		if self.status == "Approved" and not self.approved_by:
			self.db_set("approved_by", frappe.session.user, update_modified=False)
		if self.status == "Applied" and not self.applied_on:
			self.apply_to_policy()

	def apply_to_policy(self):
		policy = frappe.get_doc("Insurance Policy", self.policy)
		if self.endorsement_type == "Sum Insured Change" and self.new_value:
			try:
				policy.sum_assured = flt(self.new_value)
			except Exception:
				pass
		if self.endorsement_type == "Cancellation":
			policy.status = "Cancelled"
		if self.premium_impact:
			policy.premium_amount = flt(policy.premium_amount) + flt(self.premium_impact)
			policy.total_premium = flt(policy.premium_amount) + flt(policy.tax_amount)
		policy.flags.ignore_validate = False
		policy.save(ignore_permissions=True)
		self.db_set("applied_on", now_datetime(), update_modified=False)
		self.db_set("status", "Applied", update_modified=False)


@frappe.whitelist()
def apply_endorsement(name):
	doc = frappe.get_doc("Policy Endorsement", name)
	if doc.status not in ("Approved", "Submitted"):
		frappe.throw(_("Endorsement must be Approved before it can be applied."), title=_("Not Approved"))
	doc.status = "Applied"
	doc.apply_to_policy()
	doc.save()
	return doc.name
