frappe.ui.form.on('Client Eligibility Criteria', {
	refresh(frm) {
		frm.trigger('toggle_scope_fields');
		frm.trigger('toggle_logic_fields');
		frm.trigger('toggle_override');
	},
	applies_to(frm) {
		frm.trigger('toggle_scope_fields');
	},
	evaluation_method(frm) {
		frm.trigger('toggle_logic_fields');
	},
	failure_action(frm) {
		frm.trigger('toggle_override');
	},
	is_mandatory(frm) {
		if (frm.doc.is_mandatory && !frm.doc.failure_action) {
			frm.set_value('failure_action', 'Block Submission');
		}
	},
	toggle_scope_fields(frm) {
		frm.toggle_reqd('scheme_type', frm.doc.applies_to === 'Specific Scheme Type');
		frm.toggle_display('scheme_type', frm.doc.applies_to === 'Specific Scheme Type');
		frm.toggle_reqd('insurance_scheme', frm.doc.applies_to === 'Specific Scheme');
		frm.toggle_display('insurance_scheme', frm.doc.applies_to === 'Specific Scheme');
		frm.toggle_reqd('insurance_provider', frm.doc.applies_to === 'Specific Provider');
		frm.toggle_display('insurance_provider', frm.doc.applies_to === 'Specific Provider');
	},
	toggle_logic_fields(frm) {
		const method = frm.doc.evaluation_method;
		frm.toggle_display(['source_doctype', 'field_to_check', 'operator', 'expected_value'], method === 'Field Check');
		frm.toggle_reqd('source_doctype', method === 'Field Check');
		frm.toggle_reqd('field_to_check', method === 'Field Check');
		frm.toggle_display('python_expression', method === 'Expression');
		frm.toggle_reqd('python_expression', method === 'Expression');
		frm.toggle_display('custom_script', method === 'Script');
		frm.toggle_reqd('custom_script', method === 'Script');
		frm.toggle_display('external_api', method === 'External API');
		frm.toggle_reqd('external_api', method === 'External API');
		frm.toggle_display('checklist_items', method === 'Checklist');
	},
	toggle_override(frm) {
		frm.toggle_display('override_role', frm.doc.failure_action === 'Require Override');
		frm.toggle_reqd('override_role', frm.doc.failure_action === 'Require Override');
	}
});
