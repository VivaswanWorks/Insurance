import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class CommissionRule(Document):
	def validate(self):
		if not self.rule_name:
			frappe.throw(_("Rule Name is required."))
		if flt(self.rate) < 0:
			frappe.throw(_("Commission rate cannot be negative."), title=_("Invalid Rate"))
		if flt(self.fixed_amount) < 0:
			frappe.throw(_("Fixed amount cannot be negative."), title=_("Invalid Amount"))
		if not flt(self.rate) and not flt(self.fixed_amount):
			frappe.throw(_("Provide a commission rate and/or fixed amount."), title=_("Missing Rate"))
