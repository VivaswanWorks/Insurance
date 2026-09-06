frappe.ui.form.on('Insurance Quotation', {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.status !== 'Converted') {
			frm.add_custom_button(__('Convert to Policy'), () => {
				frappe.call({
					method: 'insurance.api.convert_quotation',
					args: { quotation: frm.doc.name },
					callback(r) {
						if (r.message) {
							frappe.set_route('Form', 'Insurance Policy', r.message)
						}
					},
				})
			}).addClass('btn-primary')
		}
	},
	scheme(frm) {
		frm.trigger('recalc')
	},
	age(frm) {
		frm.trigger('recalc')
	},
	sum_insured(frm) {
		frm.trigger('recalc')
	},
	members(frm) {
		frm.trigger('recalc')
	},
	recalc(frm) {
		if (!frm.doc.scheme || !frm.doc.sum_insured) return
		frappe.call({
			method: 'insurance.api.calculate_premium',
			args: {
				scheme: frm.doc.scheme,
				age: frm.doc.age,
				sum_insured: frm.doc.sum_insured,
				members: frm.doc.members || 1,
			},
			callback(r) {
				if (!r.message) return
				frm.set_value('net_premium', r.message.net_premium)
				frm.set_value('tax_amount', r.message.tax_amount)
				frm.set_value('total_premium', r.message.total_premium)
				frm.set_value('breakdown', r.message.breakdown)
			},
		})
	},
})
