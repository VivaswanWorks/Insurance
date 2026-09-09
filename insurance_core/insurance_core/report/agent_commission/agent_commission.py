import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	filters = filters or {}
	columns = [
		{"label": _("Agent"), "fieldname": "agent", "fieldtype": "Link", "options": "Insurance Agent", "width": 160},
		{"label": _("Policy"), "fieldname": "policy", "fieldtype": "Link", "options": "Insurance Policy", "width": 140},
		{"label": _("Event"), "fieldname": "event", "fieldtype": "Data", "width": 90},
		{"label": _("Premium"), "fieldname": "premium_amount", "fieldtype": "Currency", "width": 110},
		{"label": _("Rate %"), "fieldname": "rate", "fieldtype": "Percent", "width": 80},
		{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 110},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": _("Payout Date"), "fieldname": "payout_date", "fieldtype": "Date", "width": 110},
	]

	q_filters = {}
	if filters.get("agent"):
		q_filters["agent"] = filters.agent
	if filters.get("status"):
		q_filters["status"] = filters.status
	if filters.get("from_date") and filters.get("to_date"):
		q_filters["creation"] = ["between", [filters.from_date, filters.to_date]]
	elif filters.get("from_date"):
		q_filters["creation"] = [">=", filters.from_date]
	elif filters.get("to_date"):
		q_filters["creation"] = ["<=", filters.to_date]

	data = frappe.get_all(
		"Commission Payout",
		filters=q_filters,
		fields=["agent", "policy", "event", "premium_amount", "rate", "amount", "status", "payout_date"],
		order_by="creation desc",
	)

	total = sum(flt(r.amount) for r in data)
	if data:
		data.append(
			{
				"agent": _("Total"),
				"amount": total,
			}
		)
	return columns, data
