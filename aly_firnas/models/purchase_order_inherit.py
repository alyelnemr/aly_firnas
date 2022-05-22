from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _get_default_po_scope_schedule(self):
        return self.env['ir.config_parameter'].sudo().get_param('aly_po_scope_schedule')

    def _get_default_po_payment_schedule(self):
        return self.env['ir.config_parameter'].sudo().get_param('aly_po_payment_schedule')

    def _get_default_po_acceptance(self):
        return self.env['ir.config_parameter'].sudo().get_param('aly_po_acceptance')

    is_print_delivery_section = fields.Boolean(string='Delivery Section', default=False, required=False)
    is_print_firnas_signature = fields.Boolean(string='Firnas Shuman Signature', default=False, required=False)
    is_print_vendor_signature = fields.Boolean(string='Vendor Signature', default=False, required=False)
    vendor_contact = fields.Many2one('res.partner', string='Vendor Contacts', required=False, domain="[('parent_id', '=', partner_id)]")
    po_scope_schedule = fields.Html(string="Scope and Schedule", default=_get_default_po_scope_schedule)
    po_payment_schedule = fields.Html(string="Payment Schedule and Term", default=_get_default_po_payment_schedule)
    po_acceptance = fields.Html(string="Acceptance", default=_get_default_po_acceptance)
    date_order = fields.Date('Order Date', readonly=False, default = fields.Datetime.now)
    date_planned = fields.Date(string='Receipt Date', index=True)
