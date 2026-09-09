import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, cint, date_diff, flt, getdate, nowdate

from insurance_core.premium import calculate_premium as _calculate_premium


class InsurancePolicy(Document):
	def validate(self):
		self.set_missing_values()
		self.validate_dates()
		self.validate_scheme()
		self.compute_totals()
		self.compute_member_ages()
		self.evaluate_issuance_eligibility()

	def set_missing_values(self):
		if self.scheme and not self.provider:
			self.provider = frappe.db.get_value("Insurance Scheme", self.scheme, "provider")
		if self.start_date and not self.end_date:
			months = cint(frappe.db.get_value("Insurance Scheme", self.scheme, "policy_term_months")) or 12
			self.end_date = add_months(self.start_date, months)
		if self.end_date and not self.renewal_date:
			self.renewal_date = self.end_date
		if self.premium_amount and self.tax_amount is None:
			gst = flt(frappe.db.get_value("Insurance Scheme", self.scheme, "tax_gst_rate"))
			self.tax_amount = flt(self.premium_amount) * gst / 100.0
		self.total_premium = flt(self.premium_amount) + flt(self.tax_amount)
		if self.commission_rate and self.premium_amount and not self.commission_amount:
			self.commission_amount = flt(self.premium_amount) * flt(self.commission_rate) / 100.0

	def validate_dates(self):
		if self.start_date and self.end_date and getdate(self.end_date) <= getdate(self.start_date):
			frappe.throw(_("End date must be after start date."), title=_("Invalid Policy Period"))

	def validate_scheme(self):
		if not self.scheme:
			return
		status = frappe.db.get_value("Insurance Scheme", self.scheme, "status")
		if status != "Active" and self.status not in ("Draft", "Cancelled"):
			frappe.throw(
				_("Only Active schemes can be used on a policy. Scheme status is {0}.").format(status),
				title=_("Inactive Scheme"),
			)
		if self.sum_assured:
			mn, mx = frappe.db.get_value(
				"Insurance Scheme", self.scheme, ["minimum_sum_assured", "maximum_sum_assured"]
			)
			if mn and flt(self.sum_assured) < flt(mn):
				frappe.throw(_("Sum assured is below the scheme minimum of {0}.").format(mn), title=_("Sum Assured"))
			if mx and flt(self.sum_assured) > flt(mx):
				frappe.throw(_("Sum assured exceeds the scheme maximum of {0}.").format(mx), title=_("Sum Assured"))

	def compute_totals(self):
		self.total_premium = flt(self.premium_amount) + flt(self.tax_amount)

	def compute_member_ages(self):
		for row in self.get("policy_members") or []:
			if row.date_of_birth:
				row.age = int(date_diff(nowdate(), row.date_of_birth) / 365.25)

	def evaluate_issuance_eligibility(self):
		if getattr(self.flags, "ignore_eligibility", False):
			return
		if self.status not in ("Active", "Grace Period"):
			return
		if not frappe.db.exists("DocType", "Client Eligibility Criteria"):
			return
		from insurance_core.eligibility import evaluate_policy_eligibility

		evaluate_policy_eligibility(
			self, throw=self.status == "Active" and (self.is_new() or self.has_value_changed("status"))
		)

	def on_update(self):
		self.sync_client_stage()
		self.maybe_accrue_commission()
		if hasattr(self, "sync_linked_apps"):
			self.sync_linked_apps()

	def maybe_accrue_commission(self):
		if self.status != "Active":
			return
		if not (self.is_new() or self.has_value_changed("status")):
			return
		try:
			from insurance_core.commission import accrue_commission

			event = "Renewal" if self.policy_type == "Renewal" else "Issue"
			accrue_commission(self, event=event)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Policy Commission Accrual")

	def after_insert(self):
		self.copy_scheme_coverages()
		self.apply_checklist_template()

	def copy_scheme_coverages(self):
		if self.get("policy_coverages") or not self.scheme:
			return
		if not frappe.db.exists("DocType", "Scheme Coverage Item"):
			return
		scheme = frappe.get_doc("Insurance Scheme", self.scheme)
		for row in scheme.get("coverage_details") or []:
			self.append(
				"policy_coverages",
				{
					"coverage_name": row.coverage_name,
					"description": row.description,
					"is_mandatory": row.is_mandatory,
					"max_limit": row.max_limit,
					"percentage": row.percentage,
					"notes": row.notes,
				},
			)
		if self.get("policy_coverages"):
			self.db_update()
			self.update_child_table("policy_coverages")

	def apply_checklist_template(self):
		if self.get("compliance_checklist"):
			return
		if not frappe.db.exists("DocType", "Compliance Checklist Template"):
			return
		templates = frappe.get_all(
			"Compliance Checklist Template",
			filters={"applies_to": "Insurance Policy", "is_active": 1},
			pluck="name",
		)
		for name in templates:
			tmpl = frappe.get_doc("Compliance Checklist Template", name)
			for item in tmpl.get("items") or []:
				self.append("compliance_checklist", {"item": item.item, "completed": 0})
		if self.get("compliance_checklist"):
			self.db_update()
			self.update_child_table("compliance_checklist")

	def sync_client_stage(self):
		if not self.client or not frappe.db.exists("Insurance Client", self.client):
			return
		stage = None
		if self.status == "Active":
			stage = "Active"
		elif self.status == "Expired":
			stage = "Lapsed"
		elif self.status == "Grace Period":
			stage = "At Risk"
		elif self.status == "Lapsed":
			stage = "Lapsed"
		if stage:
			frappe.db.set_value("Insurance Client", self.client, "lifecycle_stage", stage)

	def recalculate_premium(self):
		age = None
		for row in self.get("policy_members") or []:
			if row.is_primary and row.age:
				age = row.age
				break
		result = _calculate_premium(
			self.scheme,
			age=age,
			sum_insured=self.sum_assured,
			members=len(self.get("policy_members") or []) or 1,
			policy=self.name,
		)
		self.premium_amount = result["net_premium"]
		self.tax_amount = result["tax_amount"]
		self.total_premium = result["total_premium"]
		return result


@frappe.whitelist()
def create_renewal(policy):
	src = frappe.get_doc("Insurance Policy", policy)
	if not src.scheme:
		frappe.throw(_("Source policy has no scheme."), title=_("Cannot Renew"))
	doc = frappe.copy_doc(src)
	doc.policy_number = f"{src.policy_number}-R"
	doc.policy_type = "Renewal"
	doc.previous_policy = src.name
	doc.status = "Draft"
	doc.payment_status = "Unpaid"
	doc.issue_date = nowdate()
	doc.start_date = src.end_date
	months = cint(frappe.db.get_value("Insurance Scheme", src.scheme, "policy_term_months")) or 12
	doc.end_date = add_months(doc.start_date, months)
	doc.renewal_date = doc.end_date
	doc.name = None
	doc.insert()
	doc.recalculate_premium()
	doc.save()
	return doc.name


def send_expiry_reminders():
	from insurance_core.tasks import queue_communication

	settings_days = [30, 15, 7]
	if frappe.db.exists("DocType", "Insurance Settings"):
		raw = frappe.db.get_single_value("Insurance Settings", "reminder_days") or "30,15,7"
		settings_days = [cint(x.strip()) for x in str(raw).split(",") if x.strip()]
	today = getdate(nowdate())
	for days in settings_days:
		target = frappe.utils.add_days(today, days)
		policies = frappe.get_all(
			"Insurance Policy",
			filters={"status": ["in", ["Active", "Grace Period"]], "end_date": target},
			fields=["name", "client", "end_date", "agent", "policy_number"],
		)
		for p in policies:
			queue_communication(
				template="Policy Expiring",
				subject=_("Policy {0} expires in {1} days").format(p.policy_number, days),
				related_doctype="Insurance Policy",
				related_name=p.name,
				client=p.client,
				agent=p.agent,
				body=_("Policy {0} expires on {1}.").format(p.policy_number, p.end_date),
			)


def send_premium_reminders():
	from insurance_core.tasks import queue_communication

	today = getdate(nowdate())
	due = frappe.get_all(
		"Insurance Policy",
		filters={
			"status": ["in", ["Active", "Grace Period"]],
			"next_premium_due": today,
			"payment_status": ["!=", "Paid"],
		},
		fields=["name", "client", "agent", "policy_number", "next_premium_due"],
	)
	for p in due:
		queue_communication(
			template="Premium Due",
			subject=_("Premium due for {0}").format(p.policy_number),
			related_doctype="Insurance Policy",
			related_name=p.name,
			client=p.client,
			agent=p.agent,
			body=_("Premium for policy {0} is due on {1}.").format(p.policy_number, p.next_premium_due),
		)
	overdue = frappe.get_all(
		"Insurance Policy",
		filters={
			"status": ["in", ["Active", "Grace Period"]],
			"next_premium_due": ["<", today],
			"payment_status": ["!=", "Paid"],
		},
		fields=["name", "client", "agent", "policy_number", "next_premium_due"],
	)
	for p in overdue:
		frappe.db.set_value("Insurance Policy", p.name, "payment_status", "Overdue")
		queue_communication(
			template="Premium Overdue",
			subject=_("Premium overdue for {0}").format(p.policy_number),
			related_doctype="Insurance Policy",
			related_name=p.name,
			client=p.client,
			agent=p.agent,
			body=_("Premium for policy {0} was due on {1}.").format(p.policy_number, p.next_premium_due),
		)


def expire_policies():
	today = nowdate()
	frappe.db.sql(
		"""
		update `tabInsurance Policy`
		set status = 'Expired'
		where status in ('Active', 'Grace Period') and end_date < %s
		""",
		(today,),
	)
