function Policy(data) {
	this.id = ko.observable(data.id);
	this.policy_number = ko.observable(data.policy_number);
	this.effective_date = ko.observable(data.effective_date);
	this.status = ko.observable(data.status);
	this.billing_schedule = ko.observable(data.billing_schedule);
	this.annual_premium = ko.observable(data.annual_premium);
	this.named_insured = ko.observable(data.named_insured);
	this.agent = ko.observable(data.agent);
	this.invoices = ko.observableArray([]);
	this.payments = ko.observableArray([]);
	this.due_amount = ko.observable(data.due_amount);
	this.payed_amount = ko.observable(data.payed_amount);
	this.necessary_amount = ko.observable(data.necessary_amount);

}

function Invoice(data) {
	this.bill_date = ko.observable(data.bill_date);
	this.due_date = ko.observable(data.due_date);
	this.cancel_date = ko.observable(data.cancel_date);
	this.amount_due = ko.observable(data.amount_due);
}

function Payment(data) {
	this.amount_paid = ko.observable(data.amount_paid);
	this.transaction_date = ko.observable(data.transaction_date);
}

function PoliciesListViewModel() {
	
	// Data
	var self = this;
	self.policies = ko.observableArray([]);
	
	// Search Data
	self.policyNumber = ko.observable();
	self.policy = ko.observable();
	self.dateCursor = ko.observable('2015/02/01');
	self.displayPolicies = ko.observable(true)
	self.displayPolicy = ko.observable(false)

	// Functions
	getIndividualPolicy = function() {
		
		// Get Policy Data
		var policy = ko.utils.arrayFirst(self.policies(), function(category) {
			return category.id() == self.policyNumber();
		});
		
		if (policy) {
			
			// Get Date
			var dateCursor = self.dateCursor()

			// Call JSON
			$.getJSON("/api/policy/" + this.policyNumber(), { date: dateCursor }, function (response) {

				// Create objects of invoices
				var mappedInvoices = $.map(response['policy']['invoices'], function (item) {
					item_done =  new Invoice(item);
					return item_done
				});

				// Set policy invoices to mapped invoices
				policy.invoices(mappedInvoices);

				// Create objects of payments
				var mappedPayments = $.map(response['policy']['payments'], function (item) {
					item_done =  new Payment(item);
					return item_done
				});

				// Set policy payments to mapped payments
				policy.payments(mappedPayments);

				// Set other variables
				policy.due_amount(response['policy']['due_amount']);
				policy.payed_amount(response['policy']['payed_amount']);
				policy.necessary_amount(response['policy']['necessary_amount']);

				// Set self policy to this edited policy
				self.policy(policy)

				// Hide all policies and show just one
				self.displayPolicies(false)
				self.displayPolicy(true)

			});

		} else {
			
			// Hide policy view and show all policies
			self.displayPolicies(true)
			self.displayPolicy(false)

			alert('Policy not found!')
		}
	}

	// Get JSON Response
	$.getJSON("/api/policies", function (response) {

		// Create objects of policies
		var mappedPolicies = $.map(response['policies'], function (item) {
			item_done =  new Policy(item);
			return item_done
		});

		// Set object policies to mapped policies
		self.policies(mappedPolicies);
	});
}
$(document).ready(function() {
	// Start the binding
	ko.applyBindings(new PoliciesListViewModel());
});
