frappe.ui.form.on('Cashless Authorization', {
	refresh(frm) {
		if (frm.is_new()) return;
		if (['Requested', 'Under Review', 'Query Raised'].includes(frm.doc.status)) {
			frm.add_custom_button(__('Approve'), () => {
				frappe.prompt(
					[
						{ fieldname: 'approved_amount', fieldtype: 'Currency', label: __('Approved Amount'), reqd: 1, default: frm.doc.requested_amount },
						{ fieldname: 'authorization_code', fieldtype: 'Data', label: __('Authorization Code') },
					],
					(values) => {
						frappe.call({
							method: 'insurance_core.cashless.approve_cashless_authorization',
							args: { name: frm.doc.name, ...values },
							freeze: true,
							callback: () => frm.reload_doc(),
						});
					},
					__('Approve Cashless Authorization'),
					__('Approve')
				);
			}, __('Actions'));
			frm.add_custom_button(__('Reject'), () => {
				frappe.prompt(
					[{ fieldname: 'reason', fieldtype: 'Small Text', label: __('Reason'), reqd: 1 }],
					(values) => {
						frappe.call({
							method: 'insurance_core.cashless.reject_cashless_authorization',
							args: { name: frm.doc.name, reason: values.reason },
							callback: () => frm.reload_doc(),
						});
					},
					__('Reject Authorization'),
					__('Reject')
				);
			}, __('Actions'));
		}
		if (frm.doc.status === 'Approved') {
			frm.add_custom_button(__('Mark Utilized'), () => {
				frappe.call({
					method: 'insurance_core.cashless.mark_cashless_utilized',
					args: { name: frm.doc.name },
					callback: () => frm.reload_doc(),
				});
			}, __('Actions'));
		}
	}
});
