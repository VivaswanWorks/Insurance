import frappe


@frappe.whitelist()
def check_app_permission():
	return bool(set(frappe.get_roles()) & {
		"System Manager",
		"Insurance Manager",
		"Insurance Agent",
		"Claims Adjuster",
		"Compliance Officer",
		"Insurance User",
	})


@frappe.whitelist()
def ping():
	return {"ok": True, "user": frappe.session.user, "roles": frappe.get_roles()}
