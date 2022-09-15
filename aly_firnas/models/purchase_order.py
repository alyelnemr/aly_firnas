from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import AccessError, UserError, ValidationError

READONLY_STATES = {
    'to approve': [('readonly', True)],
    'purchase': [('readonly', True)],
    'done': [('readonly', True)],
    'cancel': [('readonly', True)],
}


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

    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('waiting approval', 'Waiting Approval'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    purchase_order_approve_user_id = fields.Many2one('res.users',
                                                     string='User To Approve', states=READONLY_STATES,
                                                     domain=[('is_user_to_approve', '=', True)],
                                                     required=True)
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

    def action_submit_to_approve(self):
        for rec in self:
            if not rec.purchase_order_approve_user_id:
                raise UserError(_('Please Set User To Approve'))
            rec.state = 'waiting approval'

    def _add_supplier_to_product(self):
        # Add the partner in the supplier list of the product if the supplier is not registered for
        # this product. We limit to 10 the number of suppliers for a product to avoid the mess that
        # could be caused for some generic products ("Miscellaneous").
        for line in self.order_line:
            # Do not add a contact as a supplier
            partner = self.partner_id if not self.partner_id.parent_id else self.partner_id.parent_id
            if line.product_id and partner not in line.product_id.seller_ids.mapped('name') and len(
                    line.product_id.seller_ids) <= 10:
                # Convert the price in the right currency.
                currency = partner.property_purchase_currency_id or self.env.company.currency_id
                price = self.currency_id._convert(line.price_unit, currency, line.company_id,
                                                  line.date_order or fields.Date.today(), round=False)
                # Compute the price for the template's UoM, because the supplier's UoM is related to that UoM.
                if line.product_id.product_tmpl_id.uom_po_id != line.product_uom:
                    default_uom = line.product_id.product_tmpl_id.uom_po_id
                    price = line.product_uom._compute_price(price, default_uom)

                supplierinfo = {
                    'name': partner.id,
                    'sequence': max(line.product_id.seller_ids.mapped('sequence')) + 1 if line.product_id.seller_ids else 1,
                    'min_qty': 0.0,
                    'price': price,
                    'currency_id': currency.id,
                    'delay': 0,
                }
                # In case the order partner is a contact address, a new supplierinfo is created on
                # the parent company. In this case, we keep the product name and code.
                seller = line.product_id._select_seller(
                    partner_id=line.partner_id,
                    quantity=line.product_qty,
                    date=line.order_id.date_order and line.order_id.date_order.date(),
                    uom_id=line.product_uom)
                if seller:
                    supplierinfo['product_name'] = seller.product_name
                    supplierinfo['product_code'] = seller.product_code
                vals = {
                    'seller_ids': [(0, 0, supplierinfo)],
                }
                try:
                    line.product_id.sudo().write(vals)
                except AccessError:  # no write access rights -> just ignore
                    break

    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent', 'waiting approval']:
                continue
            if (order.purchase_order_approve_user_id and order.purchase_order_approve_user_id == self.env.user):
                order._add_supplier_to_product()
                # Deal with double validation process
                if order.company_id.po_double_validation == 'one_step' \
                        or (order.company_id.po_double_validation == 'two_step' \
                            and order.amount_total < self.env.company.currency_id._convert(
                            order.company_id.po_double_validation_amount, order.currency_id, order.company_id,
                            order.date_order or fields.Date.today())) \
                        or order.user_has_groups('purchase.group_purchase_manager'):
                    order.button_approve()
                else:
                    order.write({'state': 'to approve'})
            else:
                raise ValidationError('You Are Not Allowed To Confirm!')
        return True
