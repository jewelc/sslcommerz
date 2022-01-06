# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _

from erpnext.e_commerce.doctype.e_commerce_settings.e_commerce_settings import show_attachments

def get_context(context):
	context.no_cache = 1
	context.show_sidebar = True
	context.doc = frappe.get_doc("Sales Order", frappe.form_dict.name)
	if hasattr(context.doc, "set_indicator"):
		context.doc.set_indicator()

	if show_attachments():
		context.attachments = get_attachments(frappe.form_dict.doctype, frappe.form_dict.name)

	context.parents = frappe.form_dict.parents
	context.title = frappe.form_dict.name
	context.payment_ref = frappe.db.get_value("Payment Request",
		{"reference_name": frappe.form_dict.name}, "name")

	context.enabled_checkout = frappe.get_doc("E Commerce Settings").enable_checkout

	default_print_format = frappe.db.get_value('Property Setter', dict(property='default_print_format', doc_type=frappe.form_dict.doctype), "value")
	if default_print_format:
		context.print_format = default_print_format
	else:
		context.print_format = "Standard"

	if not frappe.has_website_permission(context.doc):
		frappe.throw(_("Not Permitted"), frappe.PermissionError)

	# check for the loyalty program of the customer
	customer_loyalty_program = frappe.db.get_value("Customer", context.doc.customer, "loyalty_program")
	if customer_loyalty_program:
		from erpnext.accounts.doctype.loyalty_program.loyalty_program import (
			get_loyalty_program_details_with_points,
		)
		loyalty_program_details = get_loyalty_program_details_with_points(context.doc.customer, customer_loyalty_program)
		context.available_loyalty_points = int(loyalty_program_details.get("loyalty_points"))
	context.flow_status = "Placed"
	pick_list = frappe.db.get_all("Pick List Item",filters={"sales_order":frappe.form_dict.name,'docstatus':1})
	if pick_list:
		if len(pick_list) == len(context.doc.items):
			context.flow_status = "In Progress"
			delivery_notes = frappe.db.get_all("Delivery Note Item",filters={"against_sales_order":frappe.form_dict.name,'docstatus':1})
			frappe.log_error(delivery_notes,"delivery_notes")
			if len(delivery_notes) == len(context.doc.items):
				context.flow_status = "Delivery In Progress"
			closed_delivery_notes = frappe.db.sql("""SELECT DI.name FROM `tabDelivery Note Item` DI INNER JOIN
								`tabDelivery Note` D ON DI.parent = D.name
								WHERE D.status ='Closed' AND DI.against_sales_order = %(order_id)s AND D.docstatus = 1
								""",{"order_id":frappe.form_dict.name},as_dict=1)
			if len(closed_delivery_notes) == len(context.doc.items):
				context.flow_status = "Delivered"
def get_attachments(dt, dn):
        return frappe.get_all("File",
			fields=["name", "file_name", "file_url", "is_private"],
			filters = {"attached_to_name": dn, "attached_to_doctype": dt, "is_private":0})
