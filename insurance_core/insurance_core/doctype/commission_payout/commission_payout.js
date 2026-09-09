frappe.ui.form.on('Commission Payout', {
	refresh(frm) {
		if (frm.is_new()) return
		if (frm.doc.status === 'Accrued') {
			frm.add_custom_button(__('Approve'), () => {
				frappe.call({
					method: 'insurance_core.api.approve_commission_payout',
					args: { name: frm.doc.name },
					callback(r) {
						if (r.message) frm.reload_doc()
					},
				})
			})
		}
		if (['Accrued', 'Approved'].includes(frm.doc.status)) {
			frm.add_custom_button(__('Mark Paid'), () => {
				frappe.call({
					method: 'insurance_core.api.mark_commission_paid',
					args: { name: frm.doc.name },
					callback(r) {
						if (r.message) frm.reload_doc()
					},
				})
			}).addClass('btn-primary')
		}
	},
})
