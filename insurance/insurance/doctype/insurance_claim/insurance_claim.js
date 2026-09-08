frappe.ui.form.on('Insurance Claim', {
	refresh(frm) {
		frm.trigger('show_integration_links');
		frm.trigger('show_eligibility_button');
	},
	show_eligibility_button(frm) {
		if (frm.is_new()) {
			return;
		}
		frm.add_custom_button(__('Re-evaluate Eligibility'), () => {
			frappe.call({
				method: 'insurance.eligibility.recalculate_score',
				args: { claim_name: frm.doc.name },
				freeze: true,
				freeze_message: __('Evaluating eligibility...'),
				callback(r) {
					if (!r.message) {
						return;
					}
					frm.reload_doc();
					const msg = r.message;
					frappe.msgprint({
						title: __('Claim Success Score'),
						indicator: msg.can_submit ? 'green' : 'red',
						message: __('Status: {0}<br>Score: {1}%', [msg.overall_status, msg.overall_score])
					});
				}
			});
		}, __('Eligibility'));
		if (frm.doc.latest_eligibility_evaluation) {
			frm.add_custom_button(__('Open Evaluation Log'), () => {
				frappe.set_route('Form', 'Claim Eligibility Evaluation', frm.doc.latest_eligibility_evaluation);
			}, __('Eligibility'));
		}
	},
	show_integration_links(frm) {
		if (frm.doc.crm_lead) {
			frm.add_custom_button(__('Open CRM Lead'), () => {
				frappe.set_route('Form', 'CRM Lead', frm.doc.crm_lead);
			}, __('Frappe Apps'));
		}
		if (frm.doc.erpnext_customer) {
			frm.add_custom_button(__('Open Customer'), () => {
				frappe.set_route('Form', 'Customer', frm.doc.erpnext_customer);
			}, __('Frappe Apps'));
		}
		if (frm.doc.helpdesk_ticket) {
			frm.add_custom_button(__('Open Ticket'), () => {
				frappe.set_route('Form', 'HD Ticket', frm.doc.helpdesk_ticket);
			}, __('Frappe Apps'));
		}
	}
});
