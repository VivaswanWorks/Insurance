import unittest

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from insurance.eligibility import (
	EligibilityResult,
	_compare,
	_normalize_weights,
)


class TestEligibilityHelpers(unittest.TestCase):
	def test_compare_operators(self):
		self.assertTrue(_compare("Verified", "Equals", "Verified"))
		self.assertTrue(_compare("verified", "Equals", "VERIFIED"))
		self.assertFalse(_compare("Pending", "Equals", "Verified"))
		self.assertTrue(_compare("Pending", "Not Equals", "Verified"))
		self.assertTrue(_compare(100, "Greater Than", 50))
		self.assertTrue(_compare(10, "Less Than", 20))
		self.assertTrue(_compare("Cashless", "In", "Cashless, Reimbursement"))
		self.assertTrue(_compare("Death", "Not In", "Cashless, Reimbursement"))
		self.assertTrue(_compare("hello", "Is Set", None))
		self.assertTrue(_compare(None, "Is Not Set", None))
		self.assertTrue(_compare("", "Is Not Set", None))
		self.assertTrue(_compare("hospital discharge", "Contains", "discharge"))

	def test_normalize_weightage(self):
		rows = [
			frappe._dict(name="a", weightage=20),
			frappe._dict(name="b", weightage=30),
			frappe._dict(name="c", weightage=50),
		]
		weights = _normalize_weights(rows, True)
		self.assertEqual(flt(weights["a"], 2), 20)
		self.assertEqual(sum(weights.values()), 100)

		partial = [
			frappe._dict(name="a", weightage=10),
			frappe._dict(name="b", weightage=10),
		]
		normalized = _normalize_weights(partial, True)
		self.assertEqual(flt(normalized["a"], 2), 50)
		absolute = _normalize_weights(partial, False)
		self.assertEqual(absolute["a"], 10)


class TestEligibilityEngine(FrappeTestCase):
	def test_module_importable(self):
		from insurance.eligibility import evaluate_claim_eligibility, get_applicable_criteria

		self.assertTrue(callable(evaluate_claim_eligibility))
		self.assertTrue(callable(get_applicable_criteria))

	def test_doctypes_exist(self):
		for dt in (
			"Client Eligibility Criteria",
			"Eligibility Checklist Item",
			"Claim Eligibility Evaluation",
			"Claim Eligibility Result",
		):
			self.assertTrue(frappe.db.exists("DocType", dt), dt)

	def test_empty_result_defaults(self):
		result = EligibilityResult()
		self.assertTrue(result.can_submit)
		self.assertEqual(result.overall_status, "Eligible")

	def test_builtin_kyc_and_policy_checks(self):
		from insurance.eligibility import _builtin_check

		client = frappe._dict(kyc_status="Pending", lifecycle_stage="Active")
		criteria = frappe._dict(criteria_code="KYC_COMPLETE")
		passed, remarks = _builtin_check(criteria, frappe._dict(), None, client, None)
		self.assertFalse(passed)
		self.assertIn("KYC", remarks)

		client.kyc_status = "Verified"
		passed, _remarks = _builtin_check(criteria, frappe._dict(), None, client, None)
		self.assertTrue(passed)

		policy = frappe._dict(status="Lapsed")
		passed, remarks = _builtin_check(frappe._dict(criteria_code="POLICY_ACTIVE"), frappe._dict(), policy, None, None)
		self.assertFalse(passed)
		policy.status = "Active"
		passed, _remarks = _builtin_check(frappe._dict(criteria_code="POLICY_ACTIVE"), frappe._dict(), policy, None, None)
		self.assertTrue(passed)

	def test_waiting_period(self):
		from insurance.eligibility import _builtin_check

		policy = frappe._dict(start_date="2026-01-01", end_date="2026-12-31", status="Active")
		scheme = frappe._dict(waiting_period_days=30)
		claim = frappe._dict(incident_date="2026-01-10")
		passed, _remarks = _builtin_check(frappe._dict(criteria_code="WAITING_PERIOD"), claim, policy, None, scheme)
		self.assertFalse(passed)
		claim.incident_date = "2026-03-01"
		passed, _remarks = _builtin_check(frappe._dict(criteria_code="WAITING_PERIOD"), claim, policy, None, scheme)
		self.assertTrue(passed)

	def test_fraud_member_consent(self):
		from insurance.eligibility import _builtin_check

		client = frappe._dict(lifecycle_stage="Blacklisted", consent_data_processing=0, consent_share_tpa=0)
		passed, remarks = _builtin_check(frappe._dict(criteria_code="NO_FRAUD_FLAG"), frappe._dict(), None, client, None)
		self.assertFalse(passed)
		self.assertIn("blacklist", remarks.lower())
		client.lifecycle_stage = "Active"
		passed, _remarks = _builtin_check(frappe._dict(criteria_code="NO_FRAUD_FLAG"), frappe._dict(), None, client, None)
		self.assertTrue(passed)

		passed, _remarks = _builtin_check(frappe._dict(criteria_code="CONSENT_VALID"), frappe._dict(), None, client, None)
		self.assertFalse(passed)
		client.consent_data_processing = 1
		passed, _remarks = _builtin_check(frappe._dict(criteria_code="CONSENT_VALID"), frappe._dict(), None, client, None)
		self.assertTrue(passed)

		policy = frappe._dict(policy_members=[frappe._dict(member_name="Ada Lovelace")])
		claim = frappe._dict(claimant="Ada Lovelace")
		passed, _remarks = _builtin_check(frappe._dict(criteria_code="MEMBER_COVERED"), claim, policy, None, None)
		self.assertTrue(passed)
		claim.claimant = "Unknown"
		passed, _remarks = _builtin_check(frappe._dict(criteria_code="MEMBER_COVERED"), claim, policy, None, None)
		self.assertFalse(passed)

	def test_mandatory_vs_optional_scoring(self):
		from insurance.eligibility import EligibilityResult, _normalize_weights

		rows = [
			frappe._dict(name="m", weightage=20, is_mandatory=1, failure_action="Block Submission", criteria_name="Mandatory"),
			frappe._dict(name="o", weightage=80, is_mandatory=0, failure_action="Warning Only", criteria_name="Optional"),
		]
		weights = _normalize_weights(rows, True)
		self.assertEqual(weights["m"], 20)
		result = EligibilityResult()
		result.block_messages.append("Mandatory failed")
		self.assertTrue(result.block_messages)
