import frappe


def _app_installed(app):
	return app in frappe.get_installed_apps()


def sync_client_from_crm(doc, method=None):
	if not doc.crm_lead or not _app_installed("crm"):
		return
	try:
		lead = frappe.get_doc("CRM Lead", doc.crm_lead)
		if not doc.email and getattr(lead, "email", None):
			doc.db_set("email", lead.email, update_modified=False)
	except frappe.DoesNotExistError:
		pass


def sync_client_to_erpnext(doc, method=None):
	if not _app_installed("erpnext"):
		return
	if doc.erpnext_customer and frappe.db.exists("Customer", doc.erpnext_customer):
		return
	if not frappe.db.exists("DocType", "Customer"):
		return
	customer = frappe.get_doc({
		"doctype": "Customer",
		"customer_name": doc.full_name,
		"customer_type": "Company" if doc.client_type == "Corporate" else "Individual",
		"email_id": doc.email,
		"mobile_no": doc.phone,
	})
	customer.insert(ignore_permissions=True)
	doc.db_set("erpnext_customer", customer.name, update_modified=False)


def sync_policy_to_erpnext(doc, method=None):
	if not _app_installed("erpnext"):
		return
	if not frappe.db.exists("DocType", "Sales Invoice"):
		return


def sync_claim_ticket(doc, method=None):
	if not _app_installed("helpdesk"):
		return
	if doc.status in ("Submitted", "Documents Pending") and frappe.db.exists("DocType", "HD Ticket"):
		existing = frappe.db.exists("HD Ticket", {"subject": ["like", f"%{doc.claim_number}%"]})
		if existing:
			return
