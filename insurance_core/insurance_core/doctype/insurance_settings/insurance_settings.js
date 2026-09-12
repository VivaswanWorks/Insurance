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
						"• Schemes (Health, Motor, Travel, Property)<br>" +
						"• Agents, Network Hospitals<br>" +
						"• ~40 Clients, ~30 Policies, ~25 Claims<br>" +
						"• Opportunities, Quotations, Grievances<br><br>" +
						"Existing records with the same IDs are skipped (idempotent)."
				),
				() => {
					frappe.call({
						method: "insurance_core.demo_data.install_demo_data_from_ui",
						freeze: true,
						freeze_message: __("Seeding Indian demo data…"),
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
