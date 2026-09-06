import frappe
from frappe.utils import add_days, nowdate, now_datetime


def send_renewal_reminders():
	cutoff = add_days(nowdate(), 30)
	policies = frappe.get_all(
		"Insurance Policy",
		filters={"status": ["in", ["Active", "Grace Period"]], "renewal_date": ["<=", cutoff]},
		fields=["name", "client", "renewal_date", "agent", "policy_number"],
	)
	for p in policies:
		exists = frappe.db.exists(
			"Insurance Communication",
			{"related_doctype": "Insurance Policy", "related_name": p.name, "template": "Renewal Reminder", "status": ["in", ["Queued", "Draft", "Sent"]]},
		)
		if exists:
			continue
		client_email = frappe.db.get_value("Insurance Client", p.client, "email")
		doc = frappe.get_doc({
			"doctype": "Insurance Communication",
			"subject": f"Renewal reminder — {p.policy_number}",
			"channel": "Email",
			"template": "Renewal Reminder",
			"recipient": client_email or p.client,
			"related_doctype": "Insurance Policy",
			"related_name": p.name,
			"scheduled_at": now_datetime(),
			"status": "Queued",
			"agent": p.agent,
			"body": f"Policy {p.policy_number} renews on {p.renewal_date}.",
		})
		doc.insert(ignore_permissions=True)


def mark_overdue_compliance():
	frappe.db.sql(
		"""
		update `tabCompliance Record`
		set status = 'Overdue'
		where due_date < %s and status not in ('Closed', 'Approved', 'Overdue')
		""",
		(nowdate(),),
	)


def lapse_grace_policies():
	frappe.db.sql(
		"""
		update `tabInsurance Policy`
		set status = 'Lapsed'
		where status = 'Grace Period' and renewal_date < %s
		""",
		(add_days(nowdate(), -15),),
	)


def flush_queued_communications():
	queued = frappe.get_all(
		"Insurance Communication",
		filters={"status": "Queued", "scheduled_at": ["<=", now_datetime()]},
		pluck="name",
	)
	for name in queued:
		frappe.db.set_value("Insurance Communication", name, "status", "Sent")
