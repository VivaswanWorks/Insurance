frappe.ui.form.on('Insurance Policy', {
	refresh(frm) {
		frm.trigger('show_integration_links')
		if (!frm.is_new() && ['Active', 'Grace Period', 'Expired'].includes(frm.doc.status)) {
			frm.add_custom_button(__('Create Renewal'), () => {
				frappe.call({
					method: 'insurance_core.api.create_renewal',
					args: { policy: frm.doc.name },
					callback(r) {
						if (r.message) {
							frappe.set_route('Form', 'Insurance Policy', r.message)
						}
					},
				})
			})
		}
		if (!frm.is_new() && frm.doc.scheme) {
			frm.add_custom_button(__('Recalculate Premium'), () => {
				frappe.call({
					method: 'insurance_core.api.calculate_premium',
					args: {
						scheme: frm.doc.scheme,
						sum_insured: frm.doc.sum_assured,
						members: (frm.doc.policy_members || []).length || 1,
					},
					callback(r) {
						if (!r.message) return
						frm.set_value('premium_amount', r.message.net_premium)
						frm.set_value('tax_amount', r.message.tax_amount)
						frm.set_value('total_premium', r.message.total_premium)
					},
				})
			})
		}
	},
	scheme(frm) {
		if (frm.doc.scheme) {
			frappe.db.get_value('Insurance Scheme', frm.doc.scheme, 'provider', (r) => {
				if (r && r.provider) frm.set_value('provider', r.provider)
			})
		}
	},
	show_integration_links(frm) {
		if (frm.doc.crm_lead) {
			frm.add_custom_button(__('Open CRM Lead'), () => {
				frappe.set_route('Form', 'CRM Lead', frm.doc.crm_lead)
			}, __('Frappe Apps'))
		}
		if (frm.doc.erpnext_customer) {
			frm.add_custom_button(__('Open Customer'), () => {
				frappe.set_route('Form', 'Customer', frm.doc.erpnext_customer)
			}, __('Frappe Apps'))
		}
	},
})
