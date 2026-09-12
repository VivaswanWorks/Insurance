frappe.ui.form.on("Insurance Settings", {
	refresh(frm) {
		if (!frappe.user.has_role("System Manager") && !frappe.user.has_role("Insurance Manager")) {
			return;
		}
		frm.add_custom_button(__("Install Demo Data"), () => {
			frappe.confirm(
				__(
					"Install bulky Indian-context demo data?<br><br>" +
						"<b>This will create sample:</b><br>" +
						"• Insurance Providers (Star, HDFC ERGO, ICICI Lombard, Bajaj, New India, GIC Re, TPAs)<br>" +
						"• ~20 Schemes (2–4 per underwriting provider: Health, Motor, Travel, Property)<br>" +
						"• 25 Agents, 30 Network Hospitals<br>" +
						"• ~800 Clients, ~600 Policies (distributed across schemes), ~150 Claims<br>" +
						"• ~200 Opportunities / Quotations, ~50 Grievances<br><br>" +
						"This may take a few minutes. Existing records with the same IDs are skipped (idempotent)."
				),
				() => {
					frappe.call({
						method: "insurance_core.demo_data.install_demo_data_from_ui",
						freeze: true,
						freeze_message: __("Seeding Indian demo data (large volume)…"),
						callback(r) {
							if (!r.exc) {
								frm.reload_doc();
							}
						},
					});
				}
			);
		}, __("Demo / Sample Data"));
	},
});
