from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare

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
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', required=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', required=True)
    is_origin_so = fields.Boolean(default=False, copy=False)

    @api.onchange('analytic_account_id')
    def update_analytic_account(self):
        for line in self.order_line:
            line.account_analytic_id = self.analytic_account_id.id

    @api.onchange('analytic_tag_ids')
    def update_analytic_tags(self):
        for line in self.order_line:
            line.analytic_tag_ids = self.analytic_tag_ids.ids

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

    def action_view_invoice(self):
        '''
        This function returns an action that display existing vendor bills of given purchase order ids.
        When only one found, show the vendor bill immediately.
        '''
        action = self.env.ref('aly_firnas.aly_action_view_purchase_advance_payment_inv')
        result = action.read()[0]
        create_bill = self.env.context.get('create_bill', False)
        res = self.env.ref('aly_firnas.aly_view_purchase_advance_payment_inv', False)
        form_view = [(res and res.id or False, 'form')]
        result['views'] = form_view
        return result

    def _get_invoiceable_lines(self, final=False):
        """Return the invoiceable lines for order `self`."""
        invoiceable_line_ids = []
        pending_section = None
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        for line in self.order_line:
            if line.qty_to_invoice > 0 or (line.qty_to_invoice <= 0 and final) or line.display_type == 'line_note':
                if pending_section:
                    invoiceable_line_ids.append(pending_section.id)
                    pending_section = None
                invoiceable_line_ids.append(line.id)

        return self.env['purchase.order.line'].browse(invoiceable_line_ids)

    def _prepare_invoice(self):
        invoice_vals = {
            'ref': self.partner_ref or '',
            'type': 'in_invoice',
            'narration': self.name,
            'invoice_origin': self.name,
            'currency_id': self.currency_id.id,
            'date': self.date_order,
            'invoice_date': self.date_order,
            'invoice_date_due': self.date_order,
            'invoice_payment_term_id': self.partner_id.property_supplier_payment_term_id or self.payment_term_id,
            'invoice_user_id': self.user_id.id,
            'p_order_id': self.id,
            'purchase_id': self.id,
            'partner_id': self.partner_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_id.property_account_position_id.id,
            'analytic_account_id': self.analytic_account_id.id,
            'analytic_tag_ids': self.analytic_tag_ids.ids,
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
        }
        return invoice_vals

    def _get_invoice_line_sequence(self, new=0, old=0):
        return new or old

    def action_create_invoice(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        # 1) Create invoices.
        invoice_vals_list = []
        for order in self:

            invoice_vals = order._prepare_invoice()
            invoiceable_lines = order._get_invoiceable_lines(final)

            if not invoiceable_lines and not invoice_vals['invoice_line_ids']:
                raise UserError(
                    _('There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

            # there is a chance the invoice_vals['invoice_line_ids'] already contains data when
            # another module extends the method `_prepare_invoice()`. Therefore, instead of
            # replacing the invoice_vals['invoice_line_ids'], we append invoiceable lines into it
            invoice_vals['invoice_line_ids'] += [
                (0, 0, line._prepare_account_move_line())
                for line in invoiceable_lines
            ]

            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(_(
                'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

        # 3) Create invoices.

        # As part of the invoice creation, we make sure the sequence of multiple SO do not interfere
        # in a single invoice. Example:
        # SO 1:
        # - Section A (sequence: 10)
        # - Product A (sequence: 11)
        # SO 2:
        # - Section B (sequence: 10)
        # - Product B (sequence: 11)
        #
        # If SO 1 & 2 are grouped in the same invoice, the result will be:
        # - Section A (sequence: 10)
        # - Section B (sequence: 10)
        # - Product A (sequence: 11)
        # - Product B (sequence: 11)
        #
        # Resequencing should be safe, however we resequence only if there are less invoices than
        # orders, meaning a grouping might have been done. This could also mean that only a part
        # of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
        if len(invoice_vals_list) < len(self):
            SaleOrderLine = self.env['purchase.order.line']
            for invoice in invoice_vals_list:
                sequence = 1
                for line in invoice['invoice_line_ids']:
                    line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
                    sequence += 1

        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
        moves = self.env['account.move'].sudo().with_context(default_type='in_invoice').create(invoice_vals_list)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view('mail.message_origin_link',
                                        values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
                                        subtype_id=self.env.ref('mail.mt_note').id
                                        )
        return moves

    def action_return_view_invoice(self):
        '''
        This function returns an action that display existing vendor bills of given purchase order ids.
        When only one found, show the vendor bill immediately.
        '''
        action = self.env.ref('account.action_move_in_invoice_type')
        result = action.read()[0]
        create_bill = self.env.context.get('create_bill', False)
        # override the context to get rid of the default filtering
        result['context'] = {
            'default_type': 'in_invoice',
            'default_company_id': self.company_id.id,
            'default_purchase_id': self.id,
            'default_partner_id': self.partner_id.id,
        }
        # Invoice_ids may be filtered depending on the user. To ensure we get all
        # invoices related to the purchase order, we read them in sudo to fill the
        # cache.
        self.sudo()._read(['invoice_ids'])
        # choose the view_mode accordingly
        if len(self.invoice_ids) > 1 and not create_bill:
            result['domain'] = "[('id', 'in', " + str(self.invoice_ids.ids) + ")]"
        else:
            res = self.env.ref('account.view_move_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                result['views'] = form_view
            # Do not set an invoice_id if we want to create a new bill.
            if not create_bill:
                result['res_id'] = self.invoice_ids.id or False
        result['context']['default_invoice_origin'] = self.name
        result['context']['default_ref'] = self.partner_ref
        return result