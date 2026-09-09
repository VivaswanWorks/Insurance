frappe.ui.form.on('Policy Endorsement', {
	refresh(frm) {
		if (frm.is_new()) return

		if (['Draft', 'Submitted'].includes(frm.doc.status)) {
			frm.add_custom_button(__('Approve'), () => {
				frappe.call({
					method: 'insurance_core.api.approve_endorsement',
					args: { name: frm.doc.name },
					callback(r) {
						if (r.message) frm.reload_doc()
					},
				})
			}, __('Workflow'))

			frm.add_custom_button(__('Reject'), () => {
				frappe.prompt(
					[{ fieldname: 'reason', fieldtype: 'Small Text', label: __('Reason'), reqd: 1 }],
					(values) => {
						frappe.call({
							method: 'insurance_core.api.reject_endorsement',
							args: { name: frm.doc.name, reason: values.reason },
							callback(r) {
								if (r.message) frm.reload_doc()
							},
						})
					},
					__('Reject Endorsement'),
					__('Reject')
				)
			}, __('Workflow'))
		}

		if (['Approved', 'Submitted'].includes(frm.doc.status)) {
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

		if (frm.doc.policy && frm.doc.endorsement_type) {
			frm.add_custom_button(__('Estimate Premium Impact'), () => {
				frappe.call({
					method: 'insurance_core.api.estimate_endorsement_impact',
					args: {
						policy: frm.doc.policy,
						endorsement_type: frm.doc.endorsement_type,
						new_value: frm.doc.new_value,
						effective_date: frm.doc.effective_date,
					},
					callback(r) {
						if (r.message) {
							frm.set_value('premium_impact', r.message.premium_impact)
							if (r.message.old_value) frm.set_value('old_value', r.message.old_value)
							frappe.show_alert({ message: __('Impact estimated'), indicator: 'green' })
						}
					},
				})
			})
		}
	},
})
