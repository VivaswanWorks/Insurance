frappe.ui.form.on('Policy Endorsement', {
	refresh(frm) {
		if (!frm.is_new() && ['Approved', 'Submitted'].includes(frm.doc.status)) {
			frm.add_custom_button(__('Apply to Policy'), () => {
				frappe.call({
					method: 'insurance_core.api.apply_endorsement',
					args: { name: frm.doc.name },
					callback(r) {
						if (r.message) frm.reload_doc()
					},
				})
			}).addClass('btn-primary')
		}
	},
})
