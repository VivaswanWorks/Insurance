from frappe import _


def get_data():
	return [
		{
			"module_name": "Insurance Core",
			"category": "Modules",
			"label": _("Insurance Core"),
			"color": "#1d4ed8",
			"icon": "/assets/insurance_core/images/insurance.svg",
			"type": "module",
			"description": _("Policies, claims, commissions, cashless & reinsurance"),
		}
	]
