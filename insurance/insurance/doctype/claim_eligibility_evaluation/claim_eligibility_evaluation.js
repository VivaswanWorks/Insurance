frappe.ui.form.on('Claim Eligibility Evaluation', {
	refresh(frm) {
		if (frm.doc.insurance_claim) {
			frm.add_custom_button(__('Open Claim'), () => {
				frappe.set_route('Form', 'Insurance Claim', frm.doc.insurance_claim);
			});
		}
		if (frm.doc.insurance_policy) {
			frm.add_custom_button(__('Open Policy'), () => {
				frappe.set_route('Form', 'Insurance Policy', frm.doc.insurance_policy);
			});
		}
	}
});
