# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint
import json
from six import string_types
from frappe.integrations.utils import make_post_request
no_cache = 1


def get_context(context):
	args = frappe._dict(frappe.local.form_dict)
	from sslcommerz_lib import SSLCOMMERZ
	gateway_settings = frappe.get_single("Sslcommerz Settings")
	settings = { 'store_id': gateway_settings.store_id, 'store_pass': gateway_settings.store_password, 'issandbox': True }
	sslcz = SSLCOMMERZ(settings)
	post_body = {}
	post_body['tran_id'] = args.get("tran_id")
	post_body['val_id'] = args.get("val_id")
	post_body['amount'] =  args.get("amount")
	post_body['card_type'] =  args.get("card_type")
	post_body['store_amount'] =  args.get("store_amount")
	post_body['card_no'] =  args.get("card_no")
	post_body['bank_tran_id'] =  args.get("bank_tran_id")
	post_body['status'] =  args.get("status")
	post_body['tran_date'] =  args.get("tran_date")
	post_body['currency'] =  args.get("currency")
	post_body['card_issuer'] =  args.get("card_issuer")
	post_body['card_brand'] =  args.get("card_brand")
	post_body['error'] =  args.get("error")
	post_body['card_sub_brand'] =  args.get("card_sub_brand")
	post_body['card_issuer_country'] =  args.get("card_issuer_country")
	post_body['card_issuer_country_code'] =  args.get("card_issuer_country_code")
	post_body['store_id'] =  args.get("store_id")
	post_body['verify_sign'] =  args.get("verify_sign")
	post_body['verify_key'] =  args.get("verify_key")
	post_body['verify_sign_sha2'] =  args.get("verify_sign_sha2")
	post_body['currency_type'] =  args.get("currency_type")
	post_body['currency_amount'] =  args.get("currency_amount")
	post_body['currency_rate'] =  args.get("currency_rate")
	post_body['base_fair'] =  args.get("base_fair")
	post_body['value_a'] =  args.get("value_a")
	post_body['value_b'] =  args.get("value_b")
	post_body['value_c'] =  args.get("value_c")
	post_body['value_d'] =  args.get("value_d")
	post_body['risk_level'] =  args.get("risk_level")
	post_body['risk_title'] =  args.get("risk_title")
	reference_docname = frappe.db.get_value("Integration Request", args.get("tran_id"),"reference_docname")
	context.redirect_url = frappe.utils.get_url()+"/sslcommerz_payment_failed"
	if sslcz.hash_validate_ipn(post_body):
		response = sslcz.validationTransactionOrder(post_body['val_id'])
		if response.get("status") == "VALIDATED" or response.get("status") == "VALID":
			redirect_resp = order_payment_success(response.get("tran_id"),response)
			context.redirect_url = redirect_resp.get("redirect_to")
	
	if frappe.session.user == "Guest":
		payment_request = frappe.get_doc("Payment Request",reference_docname)
		reference_doc = frappe.get_doc(payment_request.reference_doctype,payment_request.reference_name)
		if payment_request.reference_doctype == "Sales Order":
			user = frappe.db.get_value("Contact",reference_doc.contact_person,"user")
			frappe.log_error(user,"loog")
			frappe.local.login_manager.user = user
			frappe.local.login_manager.post_login()

@frappe.whitelist(allow_guest=True)
def order_payment_success(integration_request, params):
	# params = json.loads(params)
	integration = frappe.get_doc("Integration Request", integration_request)
	integration.status = "Completed"
	# Update integration request
	integration.update_status(params, integration.status)
	integration.reload()

	data = json.loads(integration.data)
	controller = frappe.get_doc("Sslcommerz Settings")

	# Update payment and integration data for payment controller object
	controller.integration_request = integration
	controller.data = frappe._dict(data)

	# Authorize payment
	resp =  controller.authorize_payment()
	return resp



	



