from odoo import api, fields, models, _
from datetime import datetime


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def get_report_filename(self, report_type):
        x = self
        project_name = self.analytic_account_id.name[0:10]
        po_name = self.name
        report_type_string = ' PO' if report_type == 'po' else ' RFQ'
        report_number = '2700' if report_type == 'po' else '2500'
        current_time = time = datetime.now()
        current_time_str = time.strftime("%y%m%d")
        file_name = project_name + '- ' + report_number + '-00- ' + po_name + '_' + current_time_str
        return file_name

    def _get_default_po_scope_schedule(self):
        return self.env['ir.config_parameter'].sudo().get_param('aly_po_scope_schedule')

    def _get_default_po_payment_schedule(self):
        return self.env['ir.config_parameter'].sudo().get_param('aly_po_payment_schedule')

    def _get_default_po_acceptance(self):
        return self.env['ir.config_parameter'].sudo().get_param('aly_po_acceptance')

    is_print_delivery_section = fields.Boolean(string='Delivery Section', default=False, required=False)
    is_print_firnas_signature = fields.Boolean(string='Firnas Shuman Signature', default=False, required=False)
    is_print_vendor_signature = fields.Boolean(string='Vendor Signature', default=False, required=False)
    is_print_scope_schedule = fields.Boolean(string='Print Scope and Schedule', default=False, required=False)
    is_print_payment_schedule = fields.Boolean(string='Print Payment Schedule', default=False, required=False)
    is_print_acceptance = fields.Boolean(string='Print Acceptance', default=False, required=False)
    vendor_contact = fields.Many2one('res.partner', string='Vendor Contacts', required=False, domain="[('parent_id', '=', partner_id)]")
    po_scope_schedule = fields.Html(string="Scope and Schedule", default=_get_default_po_scope_schedule)
    po_payment_schedule = fields.Html(string="Payment Schedule and Term", default=_get_default_po_payment_schedule)
    po_acceptance = fields.Html(string="Acceptance", default=_get_default_po_acceptance)
