#!/user/bin/env python2.7

import unittest
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from accounting import db
from models import Contact, Invoice, Payment, Policy
from utils import PolicyAccounting

"""
#######################################################
Test Suite for Accounting
#######################################################
"""

class TestBillingSchedules(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.test_agent = Contact('Test Agent', 'Agent')
		cls.test_insured = Contact('Test Insured', 'Named Insured')
		db.session.add(cls.test_agent)
		db.session.add(cls.test_insured)
		db.session.commit()

		cls.policy = Policy('Test Policy', date(2015, 1, 1), 1200)
		db.session.add(cls.policy)
		cls.policy.named_insured = cls.test_insured.id
		cls.policy.agent = cls.test_agent.id
		db.session.commit()

	@classmethod
	def tearDownClass(cls):
		db.session.delete(cls.test_insured)
		db.session.delete(cls.test_agent)
		db.session.delete(cls.policy)
		db.session.commit()

	def setUp(self):
		pass

	def tearDown(self):
		for invoice in self.policy.invoices:
			db.session.delete(invoice)
		db.session.commit()

	def test_annual_billing_schedule(self):
		self.policy.billing_schedule = "Annual"
		#No invoices currently exist
		self.assertFalse(self.policy.invoices)
		#Invoices should be made when the class is initiated
		pa = PolicyAccounting(self.policy.id)
		self.assertEquals(len(self.policy.invoices), 1)
		self.assertEquals(self.policy.invoices[0].amount_due, self.policy.annual_premium)

	def test_monthly_billing_schedule(self):
		self.policy.billing_schedule = "Monthly"
		#No invoices currently exist
		self.assertFalse(self.policy.invoices)
		#Invoices should be made when the class is initiated
		pa = PolicyAccounting(self.policy.id)
		self.assertEquals(len(self.policy.invoices), 12)
		self.assertEquals(self.policy.invoices[0].amount_due, self.policy.annual_premium / 12)


class TestReturnAccountBalance(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.test_agent = Contact('Test Agent', 'Agent')
		cls.test_insured = Contact('Test Insured', 'Named Insured')
		db.session.add(cls.test_agent)
		db.session.add(cls.test_insured)
		db.session.commit()

		cls.policy = Policy('Test Policy', date(2015, 1, 1), 1200)
		cls.policy.named_insured = cls.test_insured.id
		cls.policy.agent = cls.test_agent.id
		db.session.add(cls.policy)
		db.session.commit()

	@classmethod
	def tearDownClass(cls):
		db.session.delete(cls.test_insured)
		db.session.delete(cls.test_agent)
		db.session.delete(cls.policy)
		db.session.commit()

	def setUp(self):
		self.payments = []

	def tearDown(self):
		for invoice in self.policy.invoices:
			db.session.delete(invoice)
		for payment in self.payments:
			db.session.delete(payment)
		db.session.commit()

	def test_annual_on_eff_date(self):
		self.policy.billing_schedule = "Annual"
		pa = PolicyAccounting(self.policy.id)
		self.assertEquals(pa.return_account_balance(date_cursor=self.policy.effective_date), 1200)

	def test_quarterly_on_eff_date(self):
		self.policy.billing_schedule = "Quarterly"
		pa = PolicyAccounting(self.policy.id)
		self.assertEquals(pa.return_account_balance(date_cursor=self.policy.effective_date), 300)

	def test_monthly_on_eff_date(self):
		self.policy.billing_schedule = "Monthly"
		pa = PolicyAccounting(self.policy.id)
		self.assertEquals(pa.return_account_balance(date_cursor=self.policy.effective_date), 100)

	def test_quarterly_on_last_installment_bill_date(self):
		self.policy.billing_schedule = "Quarterly"
		pa = PolicyAccounting(self.policy.id)
		invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
								.order_by(Invoice.bill_date).all()
		self.assertEquals(pa.return_account_balance(date_cursor=invoices[3].bill_date), 1200)

	def test_monthly_on_last_installment_bill_date(self):
		self.policy.billing_schedule = "Monthly"
		pa = PolicyAccounting(self.policy.id)
		invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
								.order_by(Invoice.bill_date).all()
		self.assertEquals(pa.return_account_balance(date_cursor=invoices[11].bill_date), 1200)

	def test_quarterly_on_second_installment_bill_date_with_full_payment(self):
		self.policy.billing_schedule = "Quarterly"
		pa = PolicyAccounting(self.policy.id)
		invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
								.order_by(Invoice.bill_date).all()
		self.payments.append(pa.make_payment(contact_id=self.policy.named_insured,
											 date_cursor=invoices[1].bill_date, amount=600))
		self.assertEquals(pa.return_account_balance(date_cursor=invoices[1].bill_date), 0)

	def test_monthly_on_second_installment_bill_date_with_full_payment(self):
		self.policy.billing_schedule = "Monthly"
		pa = PolicyAccounting(self.policy.id)
		invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
								.order_by(Invoice.bill_date).all()
		self.payments.append(pa.make_payment(contact_id=self.policy.named_insured,
											 date_cursor=invoices[1].bill_date, amount=200))
		self.assertEquals(pa.return_account_balance(date_cursor=invoices[1].bill_date), 0)

class TestPolicyCreation(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.test_agent = Contact('Test Agent', 'Agent')
		cls.test_insured = Contact('Test Insured', 'Named Insured')
		db.session.add(cls.test_agent)
		db.session.add(cls.test_insured)
		db.session.commit()

		cls.policy = Policy('Test Policy', date(2015, 1, 1), 500)
		cls.policy.named_insured = cls.test_insured.id
		cls.policy.agent = cls.test_agent.id
		db.session.add(cls.policy)
		db.session.commit()

	@classmethod
	def tearDownClass(cls):
		db.session.delete(cls.test_insured)
		db.session.delete(cls.test_agent)
		db.session.delete(cls.policy)
		db.session.commit()

	def tearDown(self):
		for invoice in self.policy.invoices:
			db.session.delete(invoice)
		db.session.commit()

	def test_policy_with_two_pay_billing(self):
		self.policy.billing_schedule = "Two-Pay"
		pa = PolicyAccounting(self.policy.id)
		invoices = Invoice.query.filter_by(policy_id=self.policy.id).all()
		self.assertEqual(len(invoices), 2)

	def test_policy_with_annual_billing(self):
		self.policy.billing_schedule = "Annual"
		pa = PolicyAccounting(self.policy.id)
		invoices = Invoice.query.filter_by(policy_id=self.policy.id).all()
		self.assertEqual(len(invoices), 1)

	def test_policy_with_quarterly_billing(self):
		self.policy.billing_schedule = "Quarterly"
		pa = PolicyAccounting(self.policy.id)
		invoices = Invoice.query.filter_by(policy_id=self.policy.id).all()
		self.assertEqual(len(invoices), 4)

	def test_policy_with_monthly_billing(self):
		self.policy.billing_schedule = "Monthly"
		pa = PolicyAccounting(self.policy.id)
		invoices = Invoice.query.filter_by(policy_id=self.policy.id).all()
		self.assertEqual(len(invoices), 12)

class TestEvaluateCancellationPendingDueToNonPay(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.test_agent = Contact('Test Agent', 'Agent')
		cls.test_insured = Contact('Test Insured', 'Named Insured')
		db.session.add(cls.test_agent)
		db.session.add(cls.test_insured)
		db.session.commit()

		cls.policy = Policy('Test Policy', date(2015, 1, 1), 1200)
		cls.policy.named_insured = cls.test_insured.id
		cls.policy.agent = cls.test_agent.id
		db.session.add(cls.policy)
		db.session.commit()

	@classmethod
	def tearDownClass(cls):
		db.session.delete(cls.test_insured)
		db.session.delete(cls.test_agent)
		db.session.delete(cls.policy)
		db.session.commit()

	def setUp(self):
		self.payments = []
		self.policy.billing_schedule = "Monthly"
		self.pa = PolicyAccounting(self.policy.id)

	def tearDown(self):
		for invoice in self.policy.invoices:
			db.session.delete(invoice)
		for payment in self.payments:
			db.session.delete(payment)
		db.session.commit()

	def test_evaluate_cancellation_before_due_date(self):
		self.date_cursor = date(2015, 2, 1)

		self.assertFalse(
				self.pa.evaluate_cancellation_pending_due_to_non_pay(self.date_cursor)
		)

	def test_evaluate_cancellation_with_payment_on_due_date(self):
		self.date_cursor = date(2015, 2, 2)
		self.payment_date = date(2015, 2, 1)

		self.payments.append(
			self.pa.make_payment(contact_id=self.policy.named_insured,
				date_cursor=self.payment_date, amount=200)
		)

		self.assertFalse(
				self.pa.evaluate_cancellation_pending_due_to_non_pay(self.date_cursor)
		)

	def test_evaluate_cancellation_without_payment_on_due_date(self):
		self.date_cursor = date(2015, 2, 2)

		self.assertTrue(
				self.pa.evaluate_cancellation_pending_due_to_non_pay(self.date_cursor)
		)

	def test_evaluate_cancellation_without_payment_on_cancel_date(self):
		self.date_cursor = date(2015, 2, 15)

		self.assertFalse(
				self.pa.evaluate_cancellation_pending_due_to_non_pay(self.date_cursor)
		)

	def test_evaluate_cancellation_with_no_full_payment_on_due_date(self):
		self.date_cursor = date(2015, 2, 2)
		self.payment_date = date(2015, 2, 1)

		self.payments.append(
			self.pa.make_payment(contact_id=self.policy.named_insured,
				date_cursor=self.payment_date, amount=100)
		)

		self.assertTrue(
				self.pa.evaluate_cancellation_pending_due_to_non_pay(self.date_cursor)
		)

	def test_evaluate_cancellation_with_no_full_payment_on_cancel_date(self):
		self.date_cursor = date(2015, 2, 15)
		self.payment_date = date(2015, 2, 1)

		self.payments.append(
			self.pa.make_payment(contact_id=self.policy.named_insured,
				date_cursor=self.payment_date, amount=100)
		)

		self.assertFalse(
				self.pa.evaluate_cancellation_pending_due_to_non_pay(self.date_cursor)
		)

class TestChangeSchedule(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.test_agent = Contact('Test Agent', 'Agent')
		cls.test_insured = Contact('Test Insured', 'Named Insured')
		db.session.add(cls.test_agent)
		db.session.add(cls.test_insured)
		db.session.commit()

		cls.policy = Policy('Test Policy', date(2015, 1, 1), 1200)
		cls.policy.named_insured = cls.test_insured.id
		cls.policy.agent = cls.test_agent.id
		db.session.add(cls.policy)
		db.session.commit()

	@classmethod
	def tearDownClass(cls):
		db.session.delete(cls.test_insured)
		db.session.delete(cls.test_agent)
		db.session.delete(cls.policy)
		db.session.commit()

	def setUp(self):
		self.payments = []
		self.policy.billing_schedule = "Quarterly"
		self.pa = PolicyAccounting(self.policy.id)

	def tearDown(self):
		for invoice in self.policy.invoices:
			db.session.delete(invoice)
		for payment in self.payments:
			db.session.delete(payment)
		db.session.commit()

	def test_without_schedule_change(self):
		# Calculate the numeber of invoices
		number_of_invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
			.filter_by(deleted=False).count()

		self.assertEquals(number_of_invoices, 4)

	def test_with_monthly_schedule_change(self):
		# Change the billing schedule
		self.pa.change_schedule("Monthly")
		
		# Calculate the numeber of invoices
		number_of_invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
			.filter_by(deleted=False).count()

		self.assertEquals(number_of_invoices, 12)

	def test_with_anual_schedule_change(self):
		# Change the billing schedule
		self.pa.change_schedule("Annual")
		
		# Calculate the numeber of invoices
		number_of_invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
			.filter_by(deleted=False).count()

		self.assertEquals(number_of_invoices, 1)

	def test_balance_with_billing_changed(self):
		self.date_cursor = date(2015, 3, 1)

		# Change the billing schedule
		self.pa.change_schedule("Monthly")

		# Calculate the balance
		balance = self.pa.return_account_balance(self.date_cursor)

		# Assert the Balance
		self.assertEquals(balance, 300)


class TestPolicyCancellation(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.test_agent = Contact('Test Agent', 'Agent')
		cls.test_insured = Contact('Test Insured', 'Named Insured')
		db.session.add(cls.test_agent)
		db.session.add(cls.test_insured)
		db.session.commit()

		cls.policy = Policy('Test Policy', date(2015, 1, 1), 1200)
		cls.policy.named_insured = cls.test_insured.id
		cls.policy.agent = cls.test_agent.id
		db.session.add(cls.policy)
		db.session.commit()

	@classmethod
	def tearDownClass(cls):
		db.session.delete(cls.test_insured)
		db.session.delete(cls.test_agent)
		db.session.delete(cls.policy)
		db.session.commit()

	def setUp(self):
		self.payments = []
		self.policy.billing_schedule = "Monthly"
		self.pa = PolicyAccounting(self.policy.id)

	def tearDown(self):
		for invoice in self.policy.invoices:
			db.session.delete(invoice)
		for payment in self.payments:
			db.session.delete(payment)
		db.session.commit()

	def test_policy_evaluate_cancellation(self):
		date_cursor = date(2015, 6, 1)
		self.assertTrue(self.pa.evaluate_cancel(date_cursor))

	def test_policy_evaluate_cancellation_for_underwriting(self):
		date_cursor = date(2015, 3, 1)
		self.assertTrue(self.pa.evaluate_cancel(date_cursor))

	def test_policy_cancelation(self):
		date_cursor = date(2015, 3, 1)

		# Make Cancelation
		cancelation = self.pa.cancel_policy("Cancelation Description", date_cursor)

		from time import sleep

		sleep(60)
		self.assertTrue(cancelation)

