import frappe
from frappe import _
from frappe.utils import flt, now_datetime


def _settings():
	if frappe.db.exists("DocType", "Insurance Settings"):
		return frappe.get_single("Insurance Settings")
	return None


def calculate_premium(scheme, age=None, sum_insured=None, members=1, extras=None, log=True, policy=None, quotation=None):
	"""Return net, tax, total and breakdown for a scheme + quote params."""
	if isinstance(scheme, str):
		scheme = frappe.get_doc("Insurance Scheme", scheme)

	age = int(age or 0)
	sum_insured = flt(sum_insured)
	members = int(members or 1)
	extras = extras or {}

	net = 0.0
	notes = []
	basis = scheme.get("premium_basis") or "Flat"

	slabs = scheme.get("premium_table") or []
	matched = None
	def _g(row, key, default=None):
		if isinstance(row, dict):
			return row.get(key, default)
		return row.get(key, default) if hasattr(row, "get") else getattr(row, key, default)

	for row in slabs:
		age_ok = True
		age_from, age_to = _g(row, "age_from"), _g(row, "age_to")
		if age_from is not None and age and age < int(age_from):
			age_ok = False
		if age_to is not None and age and age > int(age_to):
			age_ok = False
		si_ok = True
		si_from, si_to = _g(row, "sum_insured_from"), _g(row, "sum_insured_to")
		if si_from and sum_insured and sum_insured < flt(si_from):
			si_ok = False
		if si_to and sum_insured and sum_insured > flt(si_to):
			si_ok = False
		if age_ok and si_ok:
			matched = row
			break

	if matched:
		if flt(_g(matched, "premium_amount")):
			net = flt(_g(matched, "premium_amount"))
			notes.append(_("Slab premium {0}").format(net))
		elif flt(_g(matched, "premium_rate")) and sum_insured:
			net = flt(sum_insured) * flt(_g(matched, "premium_rate")) / 100.0
			notes.append(_("Slab rate {0}% of sum insured").format(_g(matched, "premium_rate")))
	elif basis == "Sum Insured" and sum_insured and flt(scheme.get("tax_gst_rate")):
		net = flt(sum_insured) * 0.01
		notes.append(_("Fallback 1% of sum insured"))
	elif flt(scheme.get("minimum_sum_assured")) and sum_insured:
		net = max(flt(sum_insured) * 0.01, 0)
		notes.append(_("Fallback 1% of sum insured"))
	else:
		net = 0.0
		notes.append(_("No matching premium slab"))

	if basis == "Per Member" and members > 1:
		net = net * members
		notes.append(_("Multiplied by {0} members").format(members))

	for rule in scheme.get("loading_discount_rules") or []:
		criteria = (_g(rule, "criteria") or "").strip().lower()
		apply_rule = False
		if not criteria:
			apply_rule = True
		elif extras.get(criteria) or extras.get(_g(rule, "criteria")):
			apply_rule = True
		if not apply_rule:
			continue
		delta = 0.0
		if flt(_g(rule, "percentage")):
			delta = net * flt(_g(rule, "percentage")) / 100.0
		elif flt(_g(rule, "amount")):
			delta = flt(_g(rule, "amount"))
		if _g(rule, "rule_type") == "Discount":
			net -= delta
			notes.append(_("Discount {0}: -{1}").format(_g(rule, "criteria") or "", delta))
		else:
			net += delta
			notes.append(_("Loading {0}: +{1}").format(_g(rule, "criteria") or "", delta))

	net = max(net, 0.0)
	gst_rate = flt(scheme.get("tax_gst_rate") or 0)
	if scheme.get("gst_applicable") in (0, "0", False):
		gst_rate = 0.0
	tax = net * gst_rate / 100.0
	total = net + tax
	breakdown = "; ".join(notes)

	result = {
		"net_premium": net,
		"tax_amount": tax,
		"total_premium": total,
		"gst_rate": gst_rate,
		"breakdown": breakdown,
		"scheme": scheme.name,
	}

	if log and frappe.db.exists("DocType", "Premium Calculation Log"):
		doc = frappe.get_doc({
			"doctype": "Premium Calculation Log",
			"scheme": scheme.name,
			"policy": policy,
			"quotation": quotation,
			"age": age,
			"sum_insured": sum_insured,
			"members": members,
			"net_premium": net,
			"tax_amount": tax,
			"total_premium": total,
			"breakdown": breakdown,
			"calculated_by": frappe.session.user if getattr(frappe, "session", None) else None,
			"calculated_at": now_datetime(),
		})
		doc.insert(ignore_permissions=True)

	return result
