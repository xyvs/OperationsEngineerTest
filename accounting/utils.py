#!/user/bin/env python2.7

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from accounting import db
from models import Contact, Invoice, Payment, Policy

"""
#######################################################
This is the base code for the engineer project.
#######################################################
"""

class PolicyAccounting(object):
	"""
	 Each policy has its own instance of accounting.
	"""
	def __init__(self, policy_id):
		self.policy = Policy.query.filter_by(id=policy_id).one()

		if not self.policy.invoices:
			self.make_invoices()

	def return_account_balance(self, date_cursor=None):
		"""
		 This function return the total due amount at a given date.
		"""
		if not date_cursor:
			date_cursor = datetime.now().date()

		# Select all the invoices
		invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
								.filter(Invoice.bill_date <= date_cursor)\
								.order_by(Invoice.bill_date)\
								.all()

		# Calculate the total due amount
		due_now = 0
		for invoice in invoices:
			due_now += invoice.amount_due

		# Select all the payments made
		payments = Payment.query.filter_by(policy_id=self.policy.id)\
								.filter(Payment.transaction_date <= date_cursor)\
								.all()

		# Calculate the due amount without the payments already made
		for payment in payments:
			due_now -= payment.amount_paid

		return due_now

	def make_payment(self, contact_id=None, date_cursor=None, amount=0):
		"""
		 This function make a payment to a given insured.
		"""
		if not date_cursor:
			date_cursor = datetime.now().date()

		# Evaluate insured
		if not contact_id:
			try:
				contact_id = self.policy.named_insured
			except:
				print 'This policy doesn\'t have an insured assigned!'

		# Make payment and commit
		payment = Payment(self.policy.id,
							contact_id,
							amount,
							date_cursor)
		db.session.add(payment)
		db.session.commit()

		return payment

	def evaluate_cancellation_pending_due_to_non_pay(self, date_cursor=None):
		"""
		 If this function returns true, an invoice
		 on a policy has passed the due date without
		 being paid in full. However, it has not necessarily
		 made it to the cancel_date yet.
		"""
		if not date_cursor:
			date_cursor = datetime.now().date()

		due_amount = self.return_account_balance(date_cursor)

		if due_amount != 0:
				invoices = Invoice.query\
					.filter_by(policy_id=self.policy.id)\
					.filter(Invoice.due_date < date_cursor)\
					.filter(Invoice.cancel_date > date_cursor)\
					.all()

				return len(invoices) > 0
		else:
			return False

	def evaluate_cancel(self, date_cursor=None):
		"""
		 This fuction evaluates the if a policy can be canceled.
		"""
		if not date_cursor:
			date_cursor = datetime.now().date()

		# Select cancelled invoices
		invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
								.filter(Invoice.cancel_date <= date_cursor)\
								.order_by(Invoice.bill_date)\
								.all()

		# Evaluate policy cancelation
		for invoice in invoices:
			if not self.return_account_balance(invoice.cancel_date):
				continue
			else:
				print "THIS POLICY SHOULD HAVE CANCELED"
				break
		else:
			print "THIS POLICY SHOULD NOT CANCEL"


	def make_invoices(self):
		"""
		 This function generates the all the policy invoices
		 based on the chosen schedule.
		"""

		# Delete all invoices
		for invoice in self.policy.invoices:
			invoice.delete()

		# Define Billing Schedules
		billing_schedules = {'Annual': None, 'Two-Pay': 2, 'Quarterly': 4, 'Monthly': 12}

		# Generate first invoice
		invoices = []
		first_invoice = Invoice(self.policy.id,
								self.policy.effective_date, #bill_date
								self.policy.effective_date + relativedelta(months=1), #due
								self.policy.effective_date + relativedelta(months=1, days=14), #cancel
								self.policy.annual_premium)
		invoices.append(first_invoice)

		# Generate more invoices if needed
		if self.policy.billing_schedule == "Annual":
			pass

		elif self.policy.billing_schedule == "Two-Pay":
			# Calculate amount per invoice
			first_invoice.amount_due = first_invoice.amount_due / billing_schedules.get(self.policy.billing_schedule)
			
			# Generates more invoices based on the quantity
			for i in range(1, billing_schedules.get(self.policy.billing_schedule)):

				# Calculate invoice date
				months_after_eff_date = i*6
				bill_date = self.policy.effective_date + relativedelta(months=months_after_eff_date)

				# Generate Invoice
				invoice = Invoice(self.policy.id,
									bill_date,
									bill_date + relativedelta(months=1),
									bill_date + relativedelta(months=1, days=14),
									self.policy.annual_premium / billing_schedules.get(self.policy.billing_schedule))
				invoices.append(invoice)

		elif self.policy.billing_schedule == "Quarterly":
			# Calculate amount per invoice
			first_invoice.amount_due = first_invoice.amount_due / billing_schedules.get(self.policy.billing_schedule)
			
			# Generates more invoices based on the quantity
			for i in range(1, billing_schedules.get(self.policy.billing_schedule)):

				# Calculate invoice date
				months_after_eff_date = i*3
				bill_date = self.policy.effective_date + relativedelta(months=months_after_eff_date)

				# Generate Invoice
				invoice = Invoice(self.policy.id,
									bill_date,
									bill_date + relativedelta(months=1),
									bill_date + relativedelta(months=1, days=14),
									self.policy.annual_premium / billing_schedules.get(self.policy.billing_schedule))
				invoices.append(invoice)

		elif self.policy.billing_schedule == "Monthly":
			# Calculate amount per invoice
			first_invoice.amount_due = first_invoice.amount_due / billing_schedules.get(self.policy.billing_schedule)
			
			# Generates more invoices based on the quantity
			for i in range(1, billing_schedules.get(self.policy.billing_schedule)):

				# Calculate invoice date
				months_after_eff_date = i*1
				bill_date = self.policy.effective_date + relativedelta(months=months_after_eff_date)

				# Generate Invoice
				invoice = Invoice(self.policy.id,
									bill_date,
									bill_date + relativedelta(months=1),
									bill_date + relativedelta(months=1, days=14),
									self.policy.annual_premium / billing_schedules.get(self.policy.billing_schedule))
				invoices.append(invoice)

		else:
			print "You have chosen a bad billing schedule."

		# Commit Invoices
		for invoice in invoices:
			db.session.add(invoice)
		db.session.commit()

################################
# The functions below are for the db and 
# shouldn't need to be edited.
################################
def build_or_refresh_db():
	db.drop_all()
	db.create_all()
	insert_data()
	print "DB Ready!"

def insert_data():
	#Contacts
	contacts = []
	john_doe_agent = Contact('John Doe', 'Agent')
	contacts.append(john_doe_agent)
	john_doe_insured = Contact('John Doe', 'Named Insured')
	contacts.append(john_doe_insured)
	bob_smith = Contact('Bob Smith', 'Agent')
	contacts.append(bob_smith)
	anna_white = Contact('Anna White', 'Named Insured')
	contacts.append(anna_white)
	joe_lee = Contact('Joe Lee', 'Agent')
	contacts.append(joe_lee)
	ryan_bucket = Contact('Ryan Bucket', 'Named Insured')
	contacts.append(ryan_bucket)

	for contact in contacts:
		db.session.add(contact)
	db.session.commit()

	policies = []
	p1 = Policy('Policy One', date(2015, 1, 1), 365)
	p1.billing_schedule = 'Annual'
	p1.named_insured = john_doe_insured.id
	p1.agent = bob_smith.id
	policies.append(p1)

	p2 = Policy('Policy Two', date(2015, 2, 1), 1600)
	p2.billing_schedule = 'Quarterly'
	p2.named_insured = anna_white.id
	p2.agent = joe_lee.id
	policies.append(p2)

	p3 = Policy('Policy Three', date(2015, 1, 1), 1200)
	p3.billing_schedule = 'Monthly'
	p3.named_insured = ryan_bucket.id
	p3.agent = john_doe_agent.id
	policies.append(p3)

	for policy in policies:
		db.session.add(policy)
	db.session.commit()

	for policy in policies:
		PolicyAccounting(policy.id)

	payment_for_p2 = Payment(p2.id, anna_white.id, 400, date(2015, 2, 1))
	db.session.add(payment_for_p2)
	db.session.commit()

