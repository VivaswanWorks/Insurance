import frappe


ROLES = [
	"Insurance Manager",
	"Insurance Agent",
	"Claims Adjuster",
	"Compliance Officer",
	"Insurance User",
]


def after_install():
	ensure_roles()
	ensure_module()


def after_migrate():
	ensure_roles()


def ensure_roles():
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			doc = frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1})
			doc.insert(ignore_permissions=True)


def ensure_module():
	if not frappe.db.exists("Module Def", "Insurance"):
		frappe.get_doc({
			"doctype": "Module Def",
			"module_name": "Insurance",
			"app_name": "insurance",
		}).insert(ignore_permissions=True)
