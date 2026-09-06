import frappe
from frappe import _
from frappe.utils import add_days, cint, getdate, now_datetime, nowdate


def _opted_in(client, channel):
	if not client or not frappe.db.exists("Insurance Client", client):
		return True
	field = {"Email": "email_opt_in", "SMS": "sms_opt_in", "WhatsApp": "whatsapp_opt_in"}.get(channel)
	if not field:
		return True
	if not frappe.db.has_column("Insurance Client", field):
		return True
	val = frappe.db.get_value("Insurance Client", client, field)
	return val in (None, 1, "1", True)


def queue_communication(template, subject, related_doctype, related_name, client=None, agent=None, body=None, channel="Email"):
	if not frappe.db.exists("DocType", "Insurance Communication"):
		return
	if not _opted_in(client, channel):
		return
	exists = frappe.db.exists(
		"Insurance Communication",
		{
			"related_doctype": related_doctype,
			"related_name": related_name,
			"template": template,
			"status": ["in", ["Queued", "Draft", "Sent"]],
		},
	)
	if exists:
		return
	recipient = None
	if client:
		recipient = frappe.db.get_value("Insurance Client", client, "email")
	doc = frappe.get_doc({
		"doctype": "Insurance Communication",
		"subject": subject,
		"channel": channel,
		"template": template,
		"recipient": recipient or client or "unknown",
		"client": client,
		"related_doctype": related_doctype,
		"related_name": related_name,
		"scheduled_at": now_datetime(),
		"status": "Queued",
		"agent": agent,
		"body": body or subject,
	})
	if frappe.db.has_column("Insurance Communication", "comm_id"):
		doc.comm_id = frappe.generate_hash(length=10)
	doc.insert(ignore_permissions=True)
	return doc.name


def send_renewal_reminders():
	from insurance.insurance.doctype.insurance_policy.insurance_policy import send_expiry_reminders

	send_expiry_reminders()
	cutoff = add_days(nowdate(), 30)
	policies = frappe.get_all(
		"Insurance Policy",
		filters={"status": ["in", ["Active", "Grace Period"]], "renewal_date": ["<=", cutoff]},
		fields=["name", "client", "renewal_date", "agent", "policy_number"],
	)
	for p in policies:
		queue_communication(
			template="Renewal Reminder",
			subject=_("Renewal reminder — {0}").format(p.policy_number),
			related_doctype="Insurance Policy",
			related_name=p.name,
			client=p.client,
			agent=p.agent,
			body=_("Policy {0} renews on {1}.").format(p.policy_number, p.renewal_date),
		)


def send_premium_reminders():
	from insurance.insurance.doctype.insurance_policy.insurance_policy import send_premium_reminders as _send

	_send()


def expire_policies():
	from insurance.insurance.doctype.insurance_policy.insurance_policy import expire_policies as _expire

	_expire()


def mark_overdue_compliance():
	frappe.db.sql(
		"""
		update `tabCompliance Record`
		set status = 'Overdue'
		where due_date < %s and status not in ('Closed', 'Approved', 'Overdue')
		""",
		(nowdate(),),
	)
	if frappe.db.exists("DocType", "Insurance Grievance"):
		frappe.db.sql(
			"""
			update `tabInsurance Grievance`
			set status = 'Escalated'
			where due_date < %s and status in ('Open', 'Acknowledged', 'In Progress')
			""",
			(nowdate(),),
		)
	if frappe.db.exists("DocType", "Client KYC"):
		frappe.db.sql(
			"""
			update `tabClient KYC`
			set status = 'Expired'
			where valid_upto < %s and status = 'Verified'
			""",
			(nowdate(),),
		)


def lapse_grace_policies():
	grace = 15
	if frappe.db.exists("DocType", "Insurance Settings"):
		grace = cint(frappe.db.get_single_value("Insurance Settings", "grace_period_days")) or 15
	frappe.db.sql(
		"""
		update `tabInsurance Policy`
		set status = 'Lapsed'
		where status = 'Grace Period' and renewal_date < %s
		""",
		(add_days(nowdate(), -grace),),
	)
	lapsed = frappe.get_all(
		"Insurance Policy",
		filters={"status": "Lapsed", "modified": [">=", add_days(nowdate(), -1)]},
		fields=["name", "client", "policy_number", "agent"],
	)
	for p in lapsed:
		queue_communication(
			template="Policy Lapsed",
			subject=_("Policy {0} has lapsed").format(p.policy_number),
			related_doctype="Insurance Policy",
			related_name=p.name,
			client=p.client,
			agent=p.agent,
			body=_("Policy {0} has lapsed.").format(p.policy_number),
		)
		if p.client:
			frappe.db.set_value("Insurance Client", p.client, "lifecycle_stage", "Lapsed")


def flush_queued_communications():
	queued = frappe.get_all(
		"Insurance Communication",
		filters={"status": "Queued", "scheduled_at": ["<=", now_datetime()]},
		pluck="name",
	)
	for name in queued:
		frappe.db.set_value("Insurance Communication", name, "status", "Sent")
