frappe.ui.form.on('Insurance Scheme', {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('Calculate Premium'), () => {
				const d = new frappe.ui.Dialog({
					title: __('Calculate Premium'),
					fields: [
						{ fieldname: 'age', label: __('Age'), fieldtype: 'Int', reqd: 1 },
						{ fieldname: 'sum_insured', label: __('Sum Insured'), fieldtype: 'Currency', reqd: 1 },
						{ fieldname: 'members', label: __('Members'), fieldtype: 'Int', default: 1 },
					],
					primary_action_label: __('Calculate'),
					primary_action(values) {
						frappe.call({
							method: 'insurance.api.calculate_premium',
							args: {
								scheme: frm.doc.name,
								age: values.age,
								sum_insured: values.sum_insured,
								members: values.members || 1,
							},
							callback(r) {
								if (!r.message) return
								frappe.msgprint({
									title: __('Premium'),
									message: __('Net {0} + tax {1} = {2}<br>{3}', [
										r.message.net_premium,
										r.message.tax_amount,
										r.message.total_premium,
										r.message.breakdown || '',
									]),
								})
								d.hide()
							},
						})
					},
				})
				d.show()
			})
		}
	},
})
