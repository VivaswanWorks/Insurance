import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime, nowdate


class InsuranceClaim(Document):
	def validate(self):
		self.set_missing_values()
		self.validate_amounts()
		self.stamp_documents()
		self.evaluate_eligibility()

	def set_missing_values(self):
		if self.policy:
			pol = frappe.db.get_value(
				"Insurance Policy",
				self.policy,
				["client", "scheme", "provider"],
				as_dict=True,
			)
			if pol:
				self.client = self.client or pol.client
				self.scheme = self.scheme or pol.scheme
				self.provider = self.provider or pol.provider
		if not self.reported_date:
			self.reported_date = self.submission_date or nowdate()
		if self.status in ("Approved", "Partially Approved") and not self.approved_amount:
			self.approved_amount = self.claimed_amount
		if self.status == "Settled" and not self.settled_amount:
			self.settled_amount = self.approved_amount or self.claimed_amount
		if self.status == "Settled" and not self.settlement_date:
			self.settlement_date = nowdate()

	def stamp_documents(self):
		for row in self.get("claim_documents") or []:
			if not row.uploaded_on:
				row.uploaded_on = now_datetime()
			if not row.uploaded_by:
				row.uploaded_by = frappe.session.user

	def validate_amounts(self):
		if not self.policy or not self.claimed_amount:
			return
		sum_assured = flt(frappe.db.get_value("Insurance Policy", self.policy, "sum_assured"))
		if sum_assured and flt(self.claimed_amount) > sum_assured:
			frappe.throw(
				_("Claimed amount {0} exceeds policy sum assured {1}.").format(
					self.claimed_amount, sum_assured
				),
				title=_("Amount Exceeds Coverage"),
			)
		paid = flt(frappe.db.sql(
			"""
			select coalesce(sum(settled_amount), 0) from `tabInsurance Claim`
			where policy = %s and name != %s and status in ('Settled', 'Approved', 'Partially Approved')
			""",
			(self.policy, self.name or ""),
		)[0][0])
		remaining = sum_assured - paid
		if sum_assured and flt(self.claimed_amount) > remaining and remaining >= 0:
			frappe.msgprint(
				_("Remaining coverage on this policy is {0} after prior claims.").format(remaining),
				title=_("Coverage Remaining"),
				indicator="orange",
			)
		if self.status == "Settled":
			template_items = [c for c in (self.get("compliance_checklist") or []) if not c.completed]
			if template_items:
				frappe.throw(
					_("Complete the compliance checklist before settling this claim."),
					title=_("Checklist Incomplete"),
				)

	def evaluate_eligibility(self):
		if getattr(self.flags, "ignore_eligibility", False):
			return
		if not frappe.db.exists("DocType", "Client Eligibility Criteria"):
			return
		from insurance_core.eligibility import evaluate_claim_eligibility

		should_throw = self.status not in (None, "Draft")
		result = evaluate_claim_eligibility(self, throw=should_throw)
		if self.meta.has_field("eligibility_score"):
			self.eligibility_score = result.overall_score
			self.eligibility_status = result.overall_status
			self.eligibility_can_submit = 1 if result.can_submit else 0
			if result.evaluation_name:
				self.latest_eligibility_evaluation = result.evaluation_name

	def on_update(self):
		self.log_status_change()
		self.sync_policy_status()
		self.notify_status()
		if hasattr(self, "sync_linked_apps"):
			self.sync_linked_apps()

	def after_insert(self):
		self.apply_checklist_template()
		self.persist_eligibility_log()

	def persist_eligibility_log(self):
		if getattr(self.flags, "ignore_eligibility", False):
			return
		if not frappe.db.exists("DocType", "Client Eligibility Criteria"):
			return
		from insurance_core.eligibility import evaluate_claim_eligibility

		result = evaluate_claim_eligibility(self, throw=False)
		updates = {}
		if self.meta.has_field("eligibility_score"):
			updates["eligibility_score"] = result.overall_score
			updates["eligibility_status"] = result.overall_status
			updates["eligibility_can_submit"] = 1 if result.can_submit else 0
		if result.evaluation_name and self.meta.has_field("latest_eligibility_evaluation"):
			updates["latest_eligibility_evaluation"] = result.evaluation_name
		for field, value in updates.items():
			self.db_set(field, value, update_modified=False)

	def apply_checklist_template(self):
		if self.get("compliance_checklist"):
			return
		if not frappe.db.exists("DocType", "Compliance Checklist Template"):
			return
		templates = frappe.get_all(
			"Compliance Checklist Template",
			filters={"applies_to": "Insurance Claim", "is_active": 1},
			pluck="name",
		)
		for name in templates:
			tmpl = frappe.get_doc("Compliance Checklist Template", name)
			for item in tmpl.get("items") or []:
				self.append("compliance_checklist", {"item": item.item, "completed": 0})
		if self.get("compliance_checklist"):
			self.db_update()
			self.update_child_table("compliance_checklist")

	def log_status_change(self):
		if self.is_new() or not frappe.db.exists("DocType", "Claim Assessment Log"):
			return
		prev = self.get_doc_before_save()
		if not prev or prev.status == self.status:
			return
		frappe.get_doc({
			"doctype": "Claim Assessment Log",
			"claim": self.name,
			"from_status": prev.status,
			"to_status": self.status,
			"comment": self.remarks or self.assessment_notes,
			"user": frappe.session.user,
			"logged_at": now_datetime(),
		}).insert(ignore_permissions=True)

	def sync_policy_status(self):
		if not self.policy:
			return
		if self.status in ("Submitted", "Under Review", "Documents Pending", "Additional Info Required"):
			current = frappe.db.get_value("Insurance Policy", self.policy, "status")
			if current == "Active":
				frappe.db.set_value("Insurance Policy", self.policy, "status", "Claimed")
		if self.status == "Settled":
			open_claims = frappe.db.count(
				"Insurance Claim",
				{"policy": self.policy, "name": ["!=", self.name], "status": ["not in", ["Settled", "Closed", "Rejected"]]},
			)
			if not open_claims:
				frappe.db.set_value("Insurance Policy", self.policy, "status", "Settled")

	def notify_status(self):
		from insurance_core.tasks import queue_communication

		prev = self.get_doc_before_save()
		if not prev or prev.status == self.status:
			return
		mapping = {
			"Submitted": ("Claim Submitted", _("Claim {0} submitted")),
			"Additional Info Required": ("Claim Info Required", _("Additional information required for claim {0}")),
			"Approved": ("Claim Approved", _("Claim {0} approved")),
			"Partially Approved": ("Claim Approved", _("Claim {0} partially approved")),
			"Rejected": ("Claim Rejected", _("Claim {0} rejected")),
			"Settled": ("Claim Settled", _("Claim {0} settled")),
		}
		if self.status not in mapping:
			return
		template, subject = mapping[self.status]
		queue_communication(
			template=template,
			subject=subject.format(self.claim_number or self.name),
			related_doctype="Insurance Claim",
			related_name=self.name,
			client=self.client,
			agent=self.agent,
			body=subject.format(self.claim_number or self.name),
		)
