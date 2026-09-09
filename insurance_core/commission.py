"""Commission calculation and accrual for Insurance Core.

Resolves Commission Rule by scheme / provider / event, accrues Commission Payout
records, and supports approval / payment status transitions.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, nowdate


def resolve_agent(policy_doc) -> str | None:
	"""Map policy.agent (Data) to an Insurance Agent name if possible."""
	raw = (policy_doc.get("agent") or "").strip()
	if not raw:
		return None
	if frappe.db.exists("Insurance Agent", raw):
		return raw
	# try by agent_code or agent_name
	name = frappe.db.get_value("Insurance Agent", {"agent_code": raw}, "name")
	if name:
		return name
	name = frappe.db.get_value("Insurance Agent", {"agent_name": raw}, "name")
	if name:
		return name
	return None


def find_commission_rule(scheme=None, provider=None, event="Issue"):
	"""Pick the most specific active Commission Rule.

	Priority: exact scheme > provider-only > global (no scheme/provider).
	"""
	if not frappe.db.exists("DocType", "Commission Rule"):
		return None

	filters = {"status": "Active", "event": event}
	rules = frappe.get_all(
		"Commission Rule",
		filters=filters,
		fields=["name", "scheme", "provider", "rate", "fixed_amount", "rule_name"],
	)
	if not rules:
		return None

	# exact scheme match
	if scheme:
		for r in rules:
			if r.scheme == scheme:
				return r
	# provider match without scheme
	if provider:
		for r in rules:
			if r.provider == provider and not r.scheme:
				return r
	# global
	for r in rules:
		if not r.scheme and not r.provider:
			return r
	return None


def calculate_commission(policy, event="Issue", premium_override=None):
	"""Return commission breakdown for a policy + event.

	Args:
		policy: Insurance Policy name or document
		event: Issue | Renewal | Collection
		premium_override: optional base premium (e.g. endorsement impact)
	"""
	if isinstance(policy, str):
		policy = frappe.get_doc("Insurance Policy", policy)

	premium = flt(premium_override if premium_override is not None else policy.premium_amount)
	rule = find_commission_rule(scheme=policy.scheme, provider=policy.provider, event=event)

	rate = 0.0
	fixed = 0.0
	rule_name = None
	if rule:
		rate = flt(rule.rate)
		fixed = flt(rule.fixed_amount)
		rule_name = rule.name
	elif flt(policy.commission_rate):
		rate = flt(policy.commission_rate)
	else:
		agent_name = resolve_agent(policy)
		if agent_name:
			rate = flt(frappe.db.get_value("Insurance Agent", agent_name, "default_commission_rate"))

	amount = (premium * rate / 100.0) + fixed
	return {
		"premium_amount": premium,
		"rate": rate,
		"fixed_amount": fixed,
		"amount": flt(amount, 2),
		"rule": rule_name,
		"event": event,
		"agent": resolve_agent(policy),
	}


def accrue_commission(policy, event="Issue", premium_override=None, reference=None):
	"""Create a Commission Payout in Accrued status if amount > 0.

	Skips when agent cannot be resolved or an identical accrual already exists.
	"""
	if isinstance(policy, str):
		policy_name = policy
		policy = frappe.get_doc("Insurance Policy", policy)
	else:
		policy_name = policy.name

	breakdown = calculate_commission(policy, event=event, premium_override=premium_override)
	if not breakdown["agent"]:
		return None
	if flt(breakdown["amount"]) <= 0:
		return None

	# idempotency: one accrual per policy+event+reference
	existing = frappe.db.exists(
		"Commission Payout",
		{
			"policy": policy_name,
			"event": event,
			"status": ["in", ["Accrued", "Approved", "Paid"]],
			"reference": reference or policy_name,
		},
	)
	if existing:
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "Commission Payout",
			"agent": breakdown["agent"],
			"policy": policy_name,
			"event": event,
			"premium_amount": breakdown["premium_amount"],
			"rate": breakdown["rate"],
			"amount": breakdown["amount"],
			"status": "Accrued",
			"reference": reference or policy_name,
		}
	)
	doc.insert(ignore_permissions=True)

	# keep policy commission fields in sync on issue/renewal
	if event in ("Issue", "Renewal"):
		frappe.db.set_value(
			"Insurance Policy",
			policy_name,
			{
				"commission_rate": breakdown["rate"],
				"commission_amount": breakdown["amount"],
			},
			update_modified=False,
		)
	return doc.name


@frappe.whitelist()
def accrue_for_policy(policy, event="Issue"):
	return accrue_commission(policy, event=event)


@frappe.whitelist()
def approve_payout(name):
	doc = frappe.get_doc("Commission Payout", name)
	if doc.status != "Accrued":
		frappe.throw(_("Only Accrued payouts can be approved."), title=_("Invalid Status"))
	if "Insurance Manager" not in frappe.get_roles() and "System Manager" not in frappe.get_roles():
		frappe.throw(_("Only Insurance Managers can approve payouts."), frappe.PermissionError)
	doc.status = "Approved"
	doc.save()
	return doc.name


@frappe.whitelist()
def mark_payout_paid(name, payout_date=None, reference=None):
	doc = frappe.get_doc("Commission Payout", name)
	if doc.status not in ("Accrued", "Approved"):
		frappe.throw(_("Payout must be Accrued or Approved before payment."), title=_("Invalid Status"))
	doc.status = "Paid"
	doc.payout_date = payout_date or nowdate()
	if reference:
		doc.reference = reference
	doc.save()
	return doc.name


@frappe.whitelist()
def get_agent_commission_summary(agent=None, from_date=None, to_date=None):
	"""Simple MIS helper for portal / reports."""
	filters = {}
	if agent:
		filters["agent"] = agent
	if from_date or to_date:
		filters["creation"] = []
		if from_date:
			filters["creation"].append(">=")
			filters["creation"].append(from_date)
		if to_date:
			filters["creation"].append("<=")
			filters["creation"].append(to_date)

	rows = frappe.get_all(
		"Commission Payout",
		filters=filters,
		fields=["status", "amount"],
	)
	summary = {"Accrued": 0.0, "Approved": 0.0, "Paid": 0.0, "Cancelled": 0.0, "total": 0.0}
	for r in rows:
		summary[r.status] = summary.get(r.status, 0) + flt(r.amount)
		summary["total"] += flt(r.amount)
	return summary
