import frappe
from frappe.tests.utils import FrappeTestCase


class TestClientEligibilityCriteria(FrappeTestCase):
	def test_doctype_exists(self):
		self.assertTrue(frappe.db.exists("DocType", "Client Eligibility Criteria"))

	def test_criteria_code_normalized(self):
		from insurance.insurance.doctype.client_eligibility_criteria.client_eligibility_criteria import (
			ClientEligibilityCriteria,
		)

		doc = frappe.new_doc("Client Eligibility Criteria")
		doc.criteria_name = "Test KYC"
		doc.criteria_code = "kyc complete"
		doc.applies_to = "All Schemes"
		doc.status = "Active"
		doc.evaluation_stage = "Claim Intake"
		doc.is_mandatory = 1
		doc.weightage = 10
		doc.failure_action = "Block Submission"
		doc.severity = "High"
		doc.evaluation_method = "Expression"
		doc.python_expression = "True"
		doc.set_missing_values()
		self.assertEqual(doc.criteria_code, "KYC_COMPLETE")
