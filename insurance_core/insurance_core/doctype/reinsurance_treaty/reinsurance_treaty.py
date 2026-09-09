import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class ReinsuranceTreaty(Document):
	def validate(self):
		if flt(self.cession_percentage) <= 0 or flt(self.cession_percentage) > 100:
			frappe.throw(_("Cession % must be between 0 and 100."), title=_("Invalid Cession"))
		if self.effective_from and self.effective_to:
			if getdate(self.effective_to) < getdate(self.effective_from):
				frappe.throw(_("Effective To must be on or after Effective From."))
		if self.reinsurer:
			ptype = frappe.db.get_value("Insurance Provider", self.reinsurer, "provider_type")
			if ptype and ptype not in ("Reinsurer", "Partner Insurer", "Public", "Private"):
				frappe.msgprint(
					_("Selected provider type is {0}; expected Reinsurer.").format(ptype),
					indicator="orange",
					title=_("Provider Type"),
				)
