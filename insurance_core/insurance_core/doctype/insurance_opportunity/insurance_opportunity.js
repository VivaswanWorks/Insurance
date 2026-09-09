frappe.ui.form.on('Insurance Opportunity', {
	refresh(frm) {
		if (!frm.is_new() && !frm.doc.converted_quotation && frm.doc.insurance_scheme) {
			frm.add_custom_button(__('Create Quotation'), () => {
				frappe.call({
					method: 'insurance_core.insurance_core.doctype.insurance_opportunity.insurance_opportunity.create_quotation',
					args: { opportunity: frm.doc.name },
					callback(r) {
						if (r.message) {
							frappe.set_route('Form', 'Insurance Quotation', r.message)
						}
					},
				})
			})
		}
	},
})
