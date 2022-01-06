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
	frappe.log_error(args,"response")
	reference_docname = frappe.db.get_value("Integration Request", args.get("tran_id"),"reference_docname")
	if frappe.session.user == "Guest":
		payment_request = frappe.get_doc("Payment Request",reference_docname)
		reference_doc = frappe.get_doc(payment_request.reference_doctype,payment_request.reference_name)
		if payment_request.reference_doctype == "Sales Order":
			user = frappe.db.get_value("Contact",reference_doc.contact_person,"user")
			frappe.log_error(user,"loog")
			frappe.local.login_manager.user = user
			frappe.local.login_manager.post_login()