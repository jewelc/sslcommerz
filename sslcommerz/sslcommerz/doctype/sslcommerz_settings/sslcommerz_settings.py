# Copyright (c) 2021, Tridotstech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import json
from frappe.model.document import Document
from six.moves.urllib.parse import urlencode
from frappe.model.document import Document
from frappe.utils import get_url, call_hook_method, cint, get_timestamp
from frappe.integrations.utils import (make_get_request, make_post_request, create_request_log,
	create_payment_gateway)


class SslcommerzSettings(Document):
	supported_currencies = ["BDT"]
	def validate(self):
		create_payment_gateway('Sslcommerz')
		call_hook_method('payment_gateway_enabled', gateway='Sslcommerz')

	def validate_transaction_currency(self, currency):
		if currency not in self.supported_currencies:
			frappe.throw(_("Please select another payment method. Razorpay does not support transactions in currency '{0}'").format(currency))
	def get_payment_url(self, **kwargs):
		integration_request = create_request_log(kwargs, "Host", "Sslcommerz")
		doc = frappe.get_doc("Integration Request", integration_request.name)
		payment_details = json.loads(doc.data)
		# return get_url("/sslcommerz_checkout?token={0}".format(integration_request.name))
		gateway_url = get_gateway_url(payment_details,integration_request.name)
		frappe.log_error(gateway_url.get("GatewayPageURL"),'gateway_url')
		return gateway_url.get("GatewayPageURL")

	def authorize_payment(self):
		"""
		An authorization is performed when user’s payment details are successfully authenticated by the bank.
		The money is deducted from the customer’s account, but will not be transferred to the merchant’s account
		until it is explicitly captured by merchant.
		"""
		data = json.loads(self.integration_request.data)
		redirect_to = data.get('redirect_to') or None
		redirect_message = data.get('redirect_message') or None
		if self.data.reference_doctype and self.data.reference_docname:
			custom_redirect_to = None
			try:
				frappe.flags.data = data
				custom_redirect_to = frappe.get_doc(self.data.reference_doctype,
					self.data.reference_docname).run_method("on_payment_authorized", "Completed")

			except Exception:
				frappe.log_error(frappe.get_traceback())

			if custom_redirect_to:
				redirect_to = custom_redirect_to

		redirect_url = 'sslcommerz_payment_success?doctype={0}&docname={1}'.format(self.data.reference_doctype, self.data.reference_docname)
		if redirect_to:
			redirect_url += '&' + urlencode({'redirect_to': redirect_to})
		if redirect_message:
			redirect_url += '&' + urlencode({'redirect_message': redirect_message})
		frappe.log_error(redirect_url,"redirect_url")
		return {
			"redirect_to": redirect_url,
			"status": "Completed"
		}

def get_gateway_url(payment_details,integration_request):
	payment_request = frappe.get_doc("Payment Request",payment_details.get("reference_docname"))
	reference_doc = frappe.get_doc(payment_request.reference_doctype,payment_request.reference_name)
	settings = frappe.get_single("Sslcommerz Settings")
	customer_address = frappe.get_doc("Address",reference_doc.customer_address)
	customer_shipping_address = frappe.get_doc("Address",reference_doc.customer_address)
	post_data = {}
	from sslcommerz_lib import SSLCOMMERZ 
	is_sandbox = False
	if settings.is_sandbox == 1:
		is_sandbox = True
	settings = { 'store_id': settings.store_id, 'store_pass': settings.store_password, 'issandbox': is_sandbox }
	sslcz = SSLCOMMERZ(settings)
	post_body = {}
	post_body['total_amount'] = payment_details.get("amount")
	post_body['currency'] = "BDT"
	post_body['tran_id'] = integration_request
	# post_body['success_url'] = frappe.utils.get_url()+"/api/method/sslcommerz.sslcommerz.doctype.sslcommerz_settings.sslcommerz_settings.make_payment_status"
	post_body['success_url'] = frappe.utils.get_url()+"/sslcommerz_checkout"
	post_body['fail_url'] = frappe.utils.get_url()+"/sslcommerz_payment_failed?doctype={0}&docname={1}".format("Payment Request", payment_details.get("reference_docname"))
	post_body['cancel_url'] = frappe.utils.get_url()
	post_body['emi_option'] = 0
	post_body['cus_name'] = reference_doc.customer
	post_body['cus_email'] = frappe.session.user
	post_body['cus_phone'] = customer_address.phone
	post_body['cus_add1'] = customer_address.address_line1
	post_body['cus_city'] = customer_address.address_line1
	post_body['cus_country'] = "Bangladesh"
	post_body['shipping_method'] = "NO"
	post_body['multi_card_name'] = ""
	post_data['ship_name']=reference_doc.customer
	post_data['ship_add1'] =customer_shipping_address.address_line1
	post_data['ship_add2']=customer_shipping_address.address_line2
	post_data['ship_city']=customer_shipping_address.city
	post_data['ship_state']=customer_shipping_address.state
	post_data['ship_postcode']=customer_shipping_address.pincode
	post_data['ship_country']=customer_shipping_address.country
	post_body['num_of_item'] = len(reference_doc.items)
	post_body['value_a'] = "Payment against Payment Request - "+payment_details.get("reference_docname")
	post_body['value_b'] = "Payment against Sales Order - "+ reference_doc.name
	product_name = ''
	for x in reference_doc.items:
		product_name += x.item_code
	post_body['product_name'] = product_name
	post_body['product_category'] = "Website Products"
	post_body['product_profile'] = "general"
	response = sslcz.createSession(post_body) # API response
	return response

