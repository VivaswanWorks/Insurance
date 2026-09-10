frappe.ui.form.on('Insurance Claim', {
	refresh(frm) {
		frm.trigger('toggle_policy_reqd');
		frm.trigger('show_integration_links');
		frm.trigger('show_eligibility_button');
		frm.trigger('show_ai_triage_button');
		frm.trigger('show_cashless_buttons');
		frm.trigger('show_reinsurance_buttons');
	},

	policy_source(frm) {
		frm.trigger('toggle_policy_reqd');
		if (frm.doc.policy_source === 'External') {
			frm.trigger('clear_policy_details');
		} else {
			// Switching to Internal — clear external policy number
			if (frm.doc.external_policy_number) {
				frm.set_value('external_policy_number', '');
			}
			if (frm.doc.policy) {
				frm.trigger('fetch_policy_details');
			}
		}
	},

	policy(frm) {
		if (frm.doc.policy_source === 'External') {
			return;
		}
		if (frm.doc.policy) {
			frm.trigger('fetch_policy_details');
		} else {
			frm.trigger('clear_policy_details');
		}
	},

	toggle_policy_reqd(frm) {
		const internal = (frm.doc.policy_source || 'Internal') === 'Internal';
		frm.toggle_reqd('policy', internal);
		frm.toggle_reqd('external_policy_number', !internal);
		frm.set_df_property(
			'policy',
			'description',
			internal
				? __('Select an internal policy; client, scheme, provider and agent will be filled automatically.')
				: __('Hidden for External claims. Use External Policy Number instead.')
		);
	},

	fetch_policy_details(frm) {
		if (!frm.doc.policy || frm.doc.policy_source === 'External') {
			return;
		}
		frappe.db.get_value(
			'Insurance Policy',
			frm.doc.policy,
			['client', 'scheme', 'provider', 'agent'],
			(r) => {
				if (!r) {
					return;
				}
				if (r.client) {
					frm.set_value('client', r.client);
				}
				if (r.scheme) {
					frm.set_value('scheme', r.scheme);
				}
				if (r.provider) {
					frm.set_value('provider', r.provider);
				}
				if (r.agent) {
					frm.set_value('agent', r.agent);
				}
			}
		);
	},

	clear_policy_details(frm) {
		// Leave form blank for external claims — clear auto-filled policy fields
		frm.set_value('policy', '');
		frm.set_value('client', '');
		frm.set_value('scheme', '');
		frm.set_value('provider', '');
		frm.set_value('agent', '');
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
	show_ai_triage_button(frm) {
		if (frm.is_new()) {
			return;
		}
		frm.add_custom_button(__('AI Triage'), () => {
			frappe.confirm(
				__('Run AI triage against eligibility rules and guidelines? This may update status (process / reject / pending).'),
				() => {
					frappe.call({
						method: 'insurance_core.ai_triage.run_claim_ai_triage',
						args: {
							claim_name: frm.doc.name,
							apply_status_change: 1
						},
						freeze: true,
						freeze_message: __('Running AI triage...'),
						callback(r) {
							if (!r.message) {
								return;
							}
							frm.reload_doc();
							const d = r.message.decision || {};
							const a = r.message.apply || {};
							const el = r.message.eligibility || {};
							const indicator =
								d.recommended_action === 'process'
									? 'green'
									: d.recommended_action === 'reject'
										? 'red'
										: 'orange';
							frappe.msgprint({
								title: __('AI Triage Result'),
								indicator,
								message: __(
									'Action: <b>{0}</b><br>Success probability: {1}%<br>Eligibility score: {2}% ({3})<br>Status now: {4}<br><br>{5}',
									[
										d.recommended_action || '—',
										d.success_probability != null ? Math.round(d.success_probability) : '—',
										el.overall_score != null ? Math.round(el.overall_score) : '—',
										el.overall_status || '—',
										a.status_changed_to || frm.doc.status || '—',
										d.reasons || ''
									]
								)
							});
							if (a.suggestion_document) {
								frappe.show_alert({
									message: __('Suggestion document attached'),
									indicator: 'blue'
								});
							}
						}
					});
				}
			);
		}, __('AI'));

		frm.add_custom_button(__('AI Triage (advisory only)'), () => {
			frappe.call({
				method: 'insurance_core.ai_triage.run_claim_ai_triage',
				args: {
					claim_name: frm.doc.name,
					apply_status_change: 0
				},
				freeze: true,
				freeze_message: __('Running AI triage (no status change)...'),
				callback(r) {
					if (!r.message) {
						return;
					}
					frm.reload_doc();
					const d = r.message.decision || {};
					frappe.msgprint({
						title: __('AI Triage (Advisory)'),
						indicator: 'blue',
						message: __(
							'Recommended: <b>{0}</b> ({1}%)<br><br>{2}<br><br>Missing: {3}<br>Improvements: {4}',
							[
								d.recommended_action || '—',
								d.success_probability != null ? Math.round(d.success_probability) : '—',
								d.reasons || '',
								d.missing_items || '—',
								d.suggested_improvements || '—'
							]
						)
					});
				}
			});
		}, __('AI'));

		if (frappe.user.has_role('System Manager') || frappe.user.has_role('Insurance Manager')) {
			frm.add_custom_button(__('Setup Flow Agent'), () => {
				frappe.call({
					method: 'insurance_core.ai_triage.setup_claim_ai_triage',
					freeze: true,
					callback(r) {
						frappe.msgprint({
							title: __('Flow Setup'),
							message: `<pre>${JSON.stringify(r.message || {}, null, 2)}</pre>`
						});
					}
				});
			}, __('AI'));
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
