# You will probably need more methods from flask but this one is a good start.
from flask import render_template, jsonify, request

# Import things from Flask that we need.
from accounting import app, db

# Import our models
from models import Contact, Invoice, Policy

# Import our Utilities
from utils import PolicyAccounting

# Import Date
from datetime import date, datetime

# Routing for the server.
@app.route("/")
def index():
	return render_template('index.html')

@app.route("/api/policies", methods=['GET'])
def policies_json():

	# Query policies
	policies = Policy.query.all()

	# Generate Dict
	policies_dict = [{
		'id': policy.id,
		'policy_number': policy.policy_number,
		'effective_date': str(policy.effective_date),
		'status': policy.status,
		'billing_schedule': policy.billing_schedule,
		'annual_premium': policy.annual_premium,
		'named_insured': Contact.query.filter_by(id=policy.named_insured).one().name,
		'agent': Contact.query.filter_by(id=policy.agent).one().name,
	} for policy in policies]

	# Format content
	content = { 'policies' : policies_dict }

	return jsonify(content)

@app.route("/api/policy/<policy_id>", methods=['GET'])
def policy_json(policy_id):

	# Get date from get parameters
	date_cursor_response = request.args.get('date')
	date_splitted = date_cursor_response.split('-')

	# Set date based on the parameter
	if len(date_splitted) != 3:
		date_cursor = datetime.now().date()
	else:
		year,month,day = date_splitted
		date_cursor = date(int(year), int(month), int(day))
	
	# Get Policy
	try:
		policy = Policy.query.filter_by(id=policy_id).one()
	except:
		policy = None

	# Show error if policy doesn't exists
	if not policy:
		return jsonify({'error':'Policy not found!'})

	# Generate Policy Accounting
	pa = PolicyAccounting(policy.id)

	# Generate and format content
	policies_dict = pa.generate_policy_dict(date_cursor)
	content = { 'policy' : policies_dict }

	return jsonify(content)
