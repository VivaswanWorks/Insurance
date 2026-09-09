frappe.ui.form.on('Insurance Claim', {
	refresh(frm) {
		frm.trigger('show_integration_links');
		frm.trigger('show_eligibility_button');
		frm.trigger('show_cashless_buttons');
		frm.trigger('show_reinsurance_buttons');
	},
	show_eligibility_button(frm) {
		if (frm.is_new()) {
			return;
		}
		frm.add_custom_button(__('Re-evaluate Eligibility'), () => {
			frappe.call({
				method: 'insurance_core.eligibility.recalculate_score',
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
	show_cashless_buttons(frm) {
		if (frm.is_new() || frm.doc.claim_type !== 'Cashless') {
			return;
		}
		frm.add_custom_button(__('Request / Open Authorization'), () => {
			if (frm.doc.cashless_authorization) {
				frappe.set_route('Form', 'Cashless Authorization', frm.doc.cashless_authorization);
				return;
			}
			frappe.call({
				method: 'insurance_core.cashless.request_cashless_authorization',
				args: { claim: frm.doc.name },
				freeze: true,
				callback(r) {
					if (r.message) {
						frm.reload_doc();
						frappe.set_route('Form', 'Cashless Authorization', r.message);
					}
				}
			});
		}, __('Cashless'));
	},
	show_reinsurance_buttons(frm) {
		if (frm.is_new()) {
			return;
		}
		frm.add_custom_button(__('Preview Cession'), () => {
			frappe.call({
				method: 'insurance_core.reinsurance.preview_claim_cession',
				args: { claim: frm.doc.name },
				callback(r) {
					const m = r.message || {};
					frappe.msgprint({
						title: __('Reinsurance Cession'),
						message: __(
							'Active: {0}<br>Type: {1}<br>Cession %: {2}<br>Gross: {3}<br>Cession amount: {4}<br>Retention: {5}',
							[
								m.active ? __('Yes') : __('No'),
								m.reinsurance_type || '—',
								m.cession_percentage || 0,
								m.gross_amount || 0,
								m.cession_amount || 0,
								m.retention_amount || 0,
							]
						),
					});
				}
			});
		}, __('Reinsurance'));
		if (['Settled', 'Approved', 'Partially Approved'].includes(frm.doc.status)) {
			frm.add_custom_button(__('Create Recovery'), () => {
				frappe.call({
					method: 'insurance_core.reinsurance.create_reinsurance_recovery',
					args: { claim: frm.doc.name },
					freeze: true,
					callback(r) {
						if (r.message) {
							frm.reload_doc();
							frappe.set_route('Form', 'Claim Recovery', r.message);
						}
					}
				});
			}, __('Reinsurance'));
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
