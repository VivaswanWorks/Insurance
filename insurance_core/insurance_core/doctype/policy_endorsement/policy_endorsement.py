import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, date_diff, flt, getdate, now_datetime, nowdate

from insurance_core.premium import calculate_premium as _calculate_premium


class PolicyEndorsement(Document):
	def validate(self):
		self.set_missing_values()
		self.validate_policy()
		self.capture_old_values()
		self.estimate_premium_impact()

	def set_missing_values(self):
		if not self.effective_date:
			self.effective_date = nowdate()
		if not self.endorsement_number:
			self.endorsement_number = self.name

	def validate_policy(self):
		if not self.policy:
			frappe.throw(_("Policy is required."), title=_("Missing Policy"))
		status = frappe.db.get_value("Insurance Policy", self.policy, "status")
		if status in ("Cancelled", "Expired", "Lapsed") and self.endorsement_type != "Correction":
			frappe.throw(
				_("Cannot endorse a policy with status {0}.").format(status),
				title=_("Invalid Policy Status"),
			)

	def capture_old_values(self):
		"""Snapshot current policy values for audit when old_value is empty."""
		if self.old_value or not self.policy:
			return
		policy = frappe.get_doc("Insurance Policy", self.policy)
		if self.endorsement_type == "Sum Insured Change":
			self.old_value = str(flt(policy.sum_assured))
		elif self.endorsement_type == "Address Change":
			client = frappe.db.get_value("Insurance Client", policy.client, "address") if policy.client else ""
			self.old_value = client or ""
		elif self.endorsement_type == "Cancellation":
			self.old_value = policy.status
		elif self.endorsement_type in ("Member Addition", "Member Deletion"):
			members = [m.member_name for m in (policy.get("policy_members") or [])]
			self.old_value = ", ".join(members)

	def estimate_premium_impact(self):
		"""Estimate additional/refund premium when not set manually."""
		if self.flags.get("skip_premium_estimate"):
			return
		if self.endorsement_type not in ("Sum Insured Change", "Member Addition", "Member Deletion"):
			if self.endorsement_type == "Cancellation" and self.premium_impact in (None, ""):
				self.premium_impact = self._pro_rata_refund()
			return

		policy = frappe.get_doc("Insurance Policy", self.policy)
		old_premium = flt(policy.premium_amount)
		age = self._primary_age(policy)
		members = len(policy.get("policy_members") or []) or 1
		sum_insured = flt(policy.sum_assured)

		if self.endorsement_type == "Sum Insured Change" and self.new_value:
			try:
				sum_insured = flt(self.new_value)
			except Exception:
				pass
		elif self.endorsement_type == "Member Addition":
			members += 1
		elif self.endorsement_type == "Member Deletion":
			members = max(1, members - 1)

		if not policy.scheme:
			return
		result = _calculate_premium(
			policy.scheme,
			age=age,
			sum_insured=sum_insured,
			members=members,
			log=False,
		)
		new_premium = flt(result.get("net_premium"))
		self.premium_impact = flt(new_premium - old_premium, 2)

	def _pro_rata_refund(self):
		policy = frappe.get_doc("Insurance Policy", self.policy)
		if not policy.start_date or not policy.end_date:
			return 0
		total_days = max(date_diff(getdate(policy.end_date), getdate(policy.start_date)), 1)
		remaining = max(date_diff(getdate(policy.end_date), getdate(self.effective_date or nowdate())), 0)
		return -flt(policy.total_premium or policy.premium_amount) * remaining / total_days

	@staticmethod
	def _primary_age(policy):
		for row in policy.get("policy_members") or []:
			if row.is_primary and row.age:
				return cint(row.age)
		for row in policy.get("policy_members") or []:
			if row.age:
				return cint(row.age)
		return None

	def on_update(self):
		if self.status == "Approved" and not self.approved_by:
			self.db_set("approved_by", frappe.session.user, update_modified=False)
		if self.status == "Applied" and not self.applied_on:
			self.apply_to_policy()

	def apply_to_policy(self):
		policy = frappe.get_doc("Insurance Policy", self.policy)
		policy.flags.ignore_eligibility = True

		if self.endorsement_type == "Sum Insured Change" and self.new_value:
			policy.sum_assured = flt(self.new_value)

		elif self.endorsement_type == "Member Addition" and self.new_value:
			member = self._parse_member_payload(self.new_value)
			if member:
				policy.append("policy_members", member)

		elif self.endorsement_type == "Member Deletion" and self.new_value:
			target = self.new_value.strip().lower()
			remaining = []
			for row in policy.get("policy_members") or []:
				if (row.member_name or "").strip().lower() != target:
					remaining.append(row.as_dict())
			policy.set("policy_members", [])
			for row in remaining:
				policy.append("policy_members", row)

		elif self.endorsement_type == "Address Change" and self.new_value and policy.client:
			frappe.db.set_value("Insurance Client", policy.client, "address", self.new_value)

		elif self.endorsement_type == "Nominee Change":
			note = (policy.notes or "") + f"\nNominee updated via {self.name}: {self.new_value}"
			policy.notes = note.strip()

		elif self.endorsement_type == "Correction" and self.new_value:
			self._apply_correction(policy)

		elif self.endorsement_type == "Cancellation":
			policy.status = "Cancelled"

		if self.premium_impact:
			policy.premium_amount = flt(policy.premium_amount) + flt(self.premium_impact)
			gst = 0
			if policy.scheme:
				gst = flt(frappe.db.get_value("Insurance Scheme", policy.scheme, "tax_gst_rate"))
			policy.tax_amount = flt(policy.premium_amount) * gst / 100.0
			policy.total_premium = flt(policy.premium_amount) + flt(policy.tax_amount)

		policy.save(ignore_permissions=True)
		self.db_set("applied_on", now_datetime(), update_modified=False)
		self.db_set("status", "Applied", update_modified=False)

		if flt(self.premium_impact) > 0:
			try:
				from insurance_core.commission import accrue_commission

				accrue_commission(policy.name, event="Issue", premium_override=flt(self.premium_impact))
			except Exception:
				frappe.log_error(frappe.get_traceback(), "Endorsement Commission Accrual")

	def _parse_member_payload(self, raw):
		raw = (raw or "").strip()
		if not raw:
			return None
		if raw.startswith("{"):
			try:
				data = json.loads(raw)
				return {
					"member_name": data.get("member_name") or data.get("name"),
					"relationship": data.get("relationship") or "Other",
					"date_of_birth": data.get("date_of_birth"),
					"gender": data.get("gender"),
					"sum_insured": data.get("sum_insured"),
					"is_primary": cint(data.get("is_primary")),
				}
			except Exception:
				pass
		return {"member_name": raw, "relationship": "Other"}

	def _apply_correction(self, policy):
		raw = (self.new_value or "").strip()
		if not raw:
			return
		data = {}
		if raw.startswith("{"):
			try:
				data = json.loads(raw)
			except Exception:
				frappe.throw(_("Correction new_value must be valid JSON."), title=_("Invalid Correction"))
		else:
			for line in raw.splitlines():
				if "=" in line:
					k, v = line.split("=", 1)
					data[k.strip()] = v.strip()
		allowed = {
			"policy_number",
			"coverage_level",
			"premium_frequency",
			"riders",
			"notes",
			"proposal_number",
		}
		for field, value in data.items():
			if field in allowed:
				policy.set(field, value)


@frappe.whitelist()
def apply_endorsement(name):
	doc = frappe.get_doc("Policy Endorsement", name)
	if doc.status not in ("Approved", "Submitted"):
		frappe.throw(
			_("Endorsement must be Approved (or Submitted) before it can be applied."),
			title=_("Not Approved"),
		)
	if not frappe.has_permission("Policy Endorsement", "write", doc=doc):
		frappe.throw(_("Not permitted to apply endorsement."), frappe.PermissionError)
	doc.status = "Applied"
	doc.apply_to_policy()
	doc.save()
	return doc.name


@frappe.whitelist()
def approve_endorsement(name):
	doc = frappe.get_doc("Policy Endorsement", name)
	if doc.status not in ("Draft", "Submitted"):
		frappe.throw(_("Only Draft or Submitted endorsements can be approved."), title=_("Invalid Status"))
	if "Insurance Manager" not in frappe.get_roles() and "System Manager" not in frappe.get_roles():
		frappe.throw(_("Only Insurance Managers can approve endorsements."), frappe.PermissionError)
	doc.status = "Approved"
	doc.approved_by = frappe.session.user
	doc.save()
	return doc.name


@frappe.whitelist()
def reject_endorsement(name, reason=None):
	doc = frappe.get_doc("Policy Endorsement", name)
	if doc.status in ("Applied", "Rejected"):
		frappe.throw(_("Cannot reject an endorsement that is already {0}.").format(doc.status))
	doc.status = "Rejected"
	if reason:
		doc.description = (doc.description or "") + f"\nRejection reason: {reason}"
	doc.save()
	return doc.name


@frappe.whitelist()
def estimate_impact(policy, endorsement_type, new_value=None, effective_date=None):
	"""API helper for UI to preview premium impact without saving."""
	doc = frappe.get_doc(
		{
			"doctype": "Policy Endorsement",
			"policy": policy,
			"endorsement_type": endorsement_type,
			"new_value": new_value,
			"effective_date": effective_date or nowdate(),
			"description": "estimate",
			"status": "Draft",
		}
	)
	doc.flags.skip_premium_estimate = False
	doc.estimate_premium_impact()
	return {"premium_impact": flt(doc.premium_impact), "old_value": doc.old_value}
