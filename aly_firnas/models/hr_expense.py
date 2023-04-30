# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HRExpense(models.Model):
    _inherit = 'hr.expense'
    _check_company_auto = False

    @api.model
    def _get_employee_id_domain(self):
        res = [('id', '=', 0)]  # Nothing accepted by domain, by default
        if self.user_has_groups('hr_expense.group_hr_expense_user') or self.user_has_groups('account.group_account_user'):
            res = "['|', ('company_id', '=', False), ('company_id', 'in', [c.id for c in self.env.user.company_ids])]"  # Then, domain accepts everything
        elif self.user_has_groups('hr_expense.group_hr_expense_team_approver') and self.env.user.employee_ids:
            user = self.env.user
            employee = self.env.user.employee_id
            res = [
                '|', '|', '|',
                ('department_id.manager_id', '=', employee.id),
                ('parent_id', '=', employee.id),
                ('id', '=', employee.id),
                ('expense_manager_id', '=', user.id),
                '|', ('company_id', '=', False), ('company_id', 'in', [c.id for c in self.env.user.company_ids]),
            ]
        elif self.env.user.employee_id:
            employee = self.env.user.employee_id
            res = [('id', '=', employee.id), '|', ('company_id', '=', employee.company_id.id), ('company_id', 'in', [c.id for c in self.env.user.company_ids])]
        return ['|', ('company_id', '=', False), ('company_id', 'in', [c.id for c in self.env.user.company_ids])]

    def _get_discounted_price_unit(self):
        self.ensure_one()
        price = 0
        amount = self.unit_amount #if self.is_same_currency else self.total_amount_company
        if self.discount:
            price = amount * (1 - self.discount / 100)
        else:
            price = amount
        return price

    @api.depends('quantity', 'discount', 'unit_amount', 'tax_ids', 'currency_id')
    def _compute_amount(self):
        for expense in self:
            # expense.untaxed_amount = expense.unit_amount * expense.quantity
            unit_amount = expense._get_discounted_price_unit()
            expense.untaxed_amount = unit_amount * expense.quantity
            taxes = expense.tax_ids.compute_all(unit_amount, expense.currency_id, expense.quantity, expense.product_id,
                                                expense.employee_id.user_id.partner_id)
            expense.sub_total = taxes.get('total_excluded')
            expense.total_amount = taxes.get('total_included')

    @api.onchange('project_id', 'company_id', 'analytic_account_id')
    def _set_project_data(self):
        for expense in self:
            expense.analytic_tag_ids = [(5)]
            if expense.project_id:
                expense.company_id = expense.project_id.company_id.id
                expense.analytic_account_id = expense.project_id.analytic_account_id.id
                expense.employee_id = self._default_employee_id()
            if expense.analytic_account_id:
                expense.analytic_tag_ids = expense.analytic_account_id.analytic_tag_ids
            if expense.employee_id:
                if expense.analytic_tag_ids:
                    expense.analytic_tag_ids += expense.sudo().employee_id.analytic_tag_ids
                else:
                    expense.analytic_tag_ids = expense.sudo().employee_id.analytic_tag_ids
            if expense.sheet_id:
                expense.sheet_id.analytic_account_id = expense.analytic_account_id.id
                expense.sheet_id.analytic_tag_ids = expense.analytic_tag_ids

    @api.model
    def _default_employee_id(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])

    @api.model
    def _default_company_id(self):
        if self.project_id:
            return self.project_id.company_id
        return self.env.user.company_id

    def _compute_picking_count(self):
        if self.expense_picking_ids:
            self.picking_count = len(self.expense_picking_ids)
        elif self.expense_picking_id:
            self.picking_count = len(self.expense_picking_id)
        else:
            self.picking_count = 0

    def _default_picking_receive(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)], limit=1)
        if not types:
            types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return types[:1]

    @api.model
    def _default_journal_id(self):
        return False

    @api.model
    def _default_bank_journal_id(self):
        return False

    @api.depends('date', 'total_amount', 'company_currency_id')
    def _compute_total_amount_company(self):
        for expense in self:
            amount = 0
            if expense.company_currency_id:
                date_expense = expense.date
                amount = expense.currency_id._convert(
                    expense.total_amount, expense.company_currency_id,
                    expense.company_id, date_expense or fields.Date.today())
            expense.total_amount_company = amount if expense.total_amount_company == 0 else expense.total_amount_company

    @api.onchange('currency_id', 'company_id')
    def _change_currency(self):
        for expense in self:
            expense.is_same_currency = expense.currency_id == expense.company_id.currency_id

    @api.depends('picking_type_id', 'partner_id', 'product_id', 'company_id')
    def onchange_picking_type(self):
        self.location_id = False
        self.location_dest_id = False
        if self.picking_type_id:
            if self.picking_type_id.default_location_src_id:
                location_id = self.picking_type_id.default_location_src_id.id
            elif self.partner_id:
                location_id = self.partner_id.property_stock_supplier.id
            else:
                customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()

            if self.picking_type_id.default_location_dest_id:
                location_dest_id = self.picking_type_id.default_location_dest_id.id
            elif self.partner_id:
                location_dest_id = self.partner_id.property_stock_customer.id
            else:
                location_dest_id, supplierloc = self.env['stock.warehouse']._get_partner_locations()

            self.location_id = location_id
            self.location_dest_id = location_dest_id

    @api.model
    def _default_account_id(self):
        return self.env['ir.property'].get('property_account_expense_categ_id', 'product.category')

    @api.depends('sheet_id', 'sheet_id.account_move_id', 'sheet_id.state', 'state')
    def _compute_state(self):
        for expense in self:
            if not expense.sheet_id and expense.state == 'cancel':
                expense.state = 'cancel'
            if not expense.sheet_id or expense.sheet_id.state == 'draft':
                expense.state = "draft"
            elif expense.sheet_id.state == "cancel":
                expense.state = "refused"
            elif expense.sheet_id.state == "approve" or expense.sheet_id.state == "post":
                expense.state = "approved"
            elif not expense.sheet_id.account_move_id:
                expense.state = "reported"
            else:
                expense.state = "done"

    state = fields.Selection([
        ('draft', 'Draft'),
        ('received', 'Receiving'),
        ('to_submit', 'To Submit'),
        ('reported', 'Submitted'),
        ('approved', 'Approved'),
        ('done', 'Paid'),
        ('refused', 'Refused'),
        ('cancel', 'Cancelled')
    ], compute='_compute_state', string='Status', copy=False, index=True, readonly=True, store=True,
        help="Status of the expense.")
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', check_company=True,
                                          required=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', required=True,
                                        states={'post': [('readonly', True)], 'done': [('readonly', True)]},
                                        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    discount = fields.Float(string="Discount (%)", digits="Discount",
                            states={'approved': [('readonly', True)], 'done': [('readonly', True)]})
    tax_ids = fields.Many2many('account.tax', 'expense_tax', 'expense_id', 'tax_id',
                               domain="[('company_id', '=', company_id), ('type_tax_use', '=', 'purchase')]", string='Taxes',
                               states={'approved': [('readonly', True)], 'done': [('readonly', True)]})
    sub_total = fields.Monetary("Sub Total", compute='_compute_amount', store=True, currency_field='currency_id')
    is_same_currency = fields.Boolean("Is Same Currency as Company Currency", compute='_change_currency')
    product_type = fields.Selection(related='product_id.type')
    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', required=False, check_company=True,
                                      domain="[('code', '=', 'incoming'), ('company_id', '=', company_id)]",
                                      states={'approved': [('readonly', True)], 'done': [('readonly', True)]})
    picking_type_code = fields.Selection(related='picking_type_id.code')
    location_id = fields.Many2one('stock.location', "Source Location", compute=onchange_picking_type, store=False, check_company=True, readonly=False, required=False)
    location_dest_id = fields.Many2one('stock.location', "Destination Location", compute=onchange_picking_type, store=False, check_company=True, readonly=False, required=False)
    dest_address_id = fields.Many2one('res.partner', string='Dropship Address')
    default_location_dest_id_usage = fields.Selection(related='picking_type_id.default_location_dest_id.usage',
                                                      string='Destination Location Type', readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True,
                                  readonly=True, default=_default_employee_id, check_company=False)
    partner_id = fields.Many2one('res.partner', string='Vendor', required=False, change_default=True,
                                 tracking=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 states={'approved': [('readonly', False)], 'done': [('readonly', True)]})
    vendor_contact_id = fields.Many2one('res.partner', string='Vendor Contacts', required=False,
                                     domain="[('parent_id', '=', partner_id)]")
    project_id = fields.Many2one('project.project', 'Project', required=True, readonly=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=_default_company_id)
    account_id = fields.Many2one('account.account', string='Account', default=_default_account_id,
                                 domain="[('internal_type', '=', 'other'), ('company_id', '=', company_id)]",
                                 help="An expense account is expected", readonly=True)
    expense_picking_id = fields.Many2one('stock.picking', string="Picking ID", copy=False)
    expense_picking_ids = fields.Many2many('stock.picking', string="All Picking IDs", copy=False)
    picking_count = fields.Integer(string="Count", compute='_compute_picking_count', store=False)
    payment_mode = fields.Selection([
        ("own_account", "Employee (to reimburse)"),
        ("company_account", "Company")
    ], default='company_account', readonly=True, string="Paid By")
    attachment_document = fields.Binary(string='Attachment', required=False)
    journal_id = fields.Many2one('account.journal', string='Expense Journal',
                                 states={'done': [('readonly', True)], 'post': [('readonly', True)]}, check_company=False,
                                 domain="[('type', '=', 'purchase')]",
                                 default=_default_journal_id, help="The journal used when the expense is done.")
    bank_journal_id = fields.Many2one('account.journal', string='Bank Journal',
                                      states={'done': [('readonly', True)], 'post': [('readonly', True)]}, check_company=False,
                                      domain="[('type', 'in', ['cash', 'bank']), ('company_id', '=', company_id)]",
                                      default=_default_bank_journal_id,
                                      help="The payment method used when the expense is paid by the company.")
    sheet_ids = fields.Many2many('hr.expense.sheet', string="Expense Reports", copy=False)
    total_amount_company = fields.Monetary("Total (Company Currency)", compute='_compute_total_amount_company', store=True,
                                           currency_field='company_currency_id',
                                           states={'approved': [('readonly', False)], 'done': [('readonly', True)]})

    def action_view_picking(self):
        """ This function returns an action that display existing picking orders of given purchase order ids. When only one found, show the picking immediately.
        """
        action = self.env.ref('stock.action_picking_tree_all')
        result = action.read()[0]
        pick_ids = self.mapped('expense_picking_ids') or self.mapped('expense_picking_id')
        # choose the view_mode accordingly
        if not pick_ids or self.expense_picking_id.state == 'cancel':
            self.create_picking()
        pick_ids = self.mapped('expense_picking_ids') or self.mapped('expense_picking_id')
        if not pick_ids or len(pick_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % (pick_ids.ids)
        elif len(pick_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = pick_ids.id
        elif not pick_ids:
            return False
        return result

    @api.onchange('product_id', 'company_id')
    def _onchange_product_id(self):
        for expense in self:
            if expense.product_id:
                if not expense.name:
                    expense.name = expense.product_id.display_name or ''
                expense.product_uom_id = expense.product_id.uom_id  # taxes only from the same company
                expense.account_id = expense.product_id.product_tmpl_id.with_context(force_company=expense.company_id.id)._get_product_accounts()['expense']

    def _get_expense_account_source(self):
        self.ensure_one()
        if self.account_id:
            account = self.account_id
        elif self.product_id:
            account = self.product_id.product_tmpl_id.with_context(force_company=self.company_id.id)._get_product_accounts()[
                'expense']
            if not account:
                raise UserError(
                    _("No Expense account found for the product %s (or for its category), please configure one.") % (
                        self.product_id.name))
        else:
            account = self.env['ir.property'].with_context(force_company=self.company_id.id).get(
                'property_account_expense_categ_id', 'product.category')
            if not account:
                raise UserError(
                    _('Please configure Default Expense account for Product expense: `property_account_expense_categ_id`.'))
        return account

    def _get_account_move_line_values(self):
        move_line_values_by_expense = {}
        for expense in self:
            move_line_name = expense.employee_id.name + ': ' + expense.name.split('\n')[0][:64]
            account_src = expense._get_expense_account_source()
            account_dst = expense._get_expense_account_destination()
            account_date = expense.sheet_id.accounting_date or expense.date or fields.Date.context_today(expense)

            company_currency = expense.company_id.currency_id
            different_currency = expense.currency_id and expense.currency_id != company_currency

            move_line_values = []
            unit_amount = expense._get_discounted_price_unit()
            taxes = expense.tax_ids.with_context(round=True).compute_all(unit_amount, expense.currency_id,
                                                                         expense.quantity, expense.product_id)
            total_amount = 0.0
            total_amount_currency = 0.0
            partner_id = expense.employee_id.address_home_id.commercial_partner_id

            # source move line
            amount = taxes['total_excluded']
            amount_currency = False
            if different_currency:
                amount = expense.total_amount_company # get the value entered from the screen instead of converting currencies, as request from Eng. Mostafa El Bedawy
                # amount = expense.currency_id._convert(amount, company_currency, expense.company_id, account_date)
                amount_currency = taxes['total_excluded']
            move_line_src = {
                'name': expense.name,
                'quantity': expense.quantity or 1,
                'debit': amount if amount > 0 else 0,
                'credit': -amount if amount < 0 else 0,
                'amount_currency': amount_currency if different_currency else 0.0,
                'account_id': account_src.id,
                'product_id': expense.product_id.id,
                'product_uom_id': expense.product_uom_id.id,
                'analytic_account_id': expense.analytic_account_id.id,
                'analytic_tag_ids': [(6, 0, expense.analytic_tag_ids.ids)],
                'expense_id': expense.id,
                'partner_id': False,
                'tax_ids': [(6, 0, expense.tax_ids.ids)],
                'tag_ids': [(6, 0, taxes['base_tags'])],
                'currency_id': expense.currency_id.id if different_currency else False,
            }
            move_line_values.append(move_line_src)
            total_amount += -move_line_src['debit'] or move_line_src['credit']
            total_amount_currency += -move_line_src['amount_currency'] if move_line_src['currency_id'] else (
                        -move_line_src['debit'] or move_line_src['credit'])

            # taxes move lines
            for tax in taxes['taxes']:
                amount = tax['amount']
                amount_currency = False
                if different_currency:
                    amount = expense.currency_id._convert(amount, company_currency, expense.company_id, account_date)
                    amount_currency = tax['amount']

                if tax['tax_repartition_line_id']:
                    rep_ln = self.env['account.tax.repartition.line'].browse(tax['tax_repartition_line_id'])
                    base_amount = self.env['account.move']._get_base_amount_to_display(tax['base'], rep_ln)
                    base_amount = expense.currency_id._convert(base_amount, company_currency, expense.company_id,
                                                               account_date) if different_currency else base_amount
                else:
                    base_amount = None

                move_line_tax_values = {
                    'name': tax['name'],
                    'quantity': 1,
                    'debit': amount if amount > 0 else 0,
                    'credit': -amount if amount < 0 else 0,
                    'amount_currency': amount_currency if different_currency else 0.0,
                    'account_id': tax['account_id'] or move_line_src['account_id'],
                    'tax_repartition_line_id': tax['tax_repartition_line_id'],
                    'tag_ids': tax['tag_ids'],
                    'tax_base_amount': base_amount,
                    'expense_id': expense.id,
                    'partner_id': False,
                    'analytic_account_id': expense.analytic_account_id.id,
                    'analytic_tag_ids': [(6, 0, expense.analytic_tag_ids.ids)],
                    'currency_id': expense.currency_id.id if different_currency else False,
                }
                total_amount -= amount
                total_amount_currency -= move_line_tax_values['amount_currency'] or amount
                move_line_values.append(move_line_tax_values)

            # destination move line
            move_line_dst = {
                'name': expense.name,
                'debit': total_amount > 0 and total_amount,
                'credit': total_amount < 0 and -total_amount,
                'account_id': account_dst,
                'date_maturity': account_date,
                'amount_currency': total_amount_currency if different_currency else 0.0,
                'currency_id': expense.currency_id.id if different_currency else False,
                'expense_id': expense.id,
                'partner_id': partner_id.id if partner_id else False,
                'analytic_account_id': expense.analytic_account_id.id,
                'analytic_tag_ids': [(6, 0, expense.analytic_tag_ids.ids)],
            }
            move_line_values.append(move_line_dst)

            move_line_values_by_expense[expense.id] = move_line_values
        return move_line_values_by_expense

    def _prepare_move_values(self):
        """
        This function prepares move values related to an expense
        """
        self.ensure_one()
        journal = self.sheet_id.bank_journal_id if self.payment_mode == 'company_account' else self.sheet_id.journal_id
        account_date = self.sheet_id.accounting_date or self.date
        move_values = {
            'journal_id': journal.id,
            'company_id': self.sheet_id.company_id.id,
            'date': account_date,
            'analytic_account_id': self.analytic_account_id.id,
            'analytic_tag_ids': self.analytic_tag_ids.ids,
            'ref': self.sheet_id.name,
            # force the name to the default value, to avoid an eventual 'default_name' in the context
            # to set it to '' which cause no number to be given to the account.move when posted.
            'name': '/',
        }
        return move_values

    def _get_account_move_by_sheet(self):
        """ Return a mapping between the expense sheet of current expense and its account move
            :returns dict where key is a sheet id, and value is an account move record
        """
        move_grouped_by_sheet = {}
        for expense in self:
            # create the move that will contain the accounting entries
            if expense.sheet_id.id not in move_grouped_by_sheet:
                move_vals = expense._prepare_move_values()
                move = self.env['account.move'].with_context(default_journal_id=move_vals['journal_id']).create(move_vals)
                move_grouped_by_sheet[expense.sheet_id.id] = move
            else:
                move = move_grouped_by_sheet[expense.sheet_id.id]
        return move_grouped_by_sheet

    def action_move_create(self):
        '''
        main function that is called when trying to create the accounting entries related to an expense
        '''
        move_group_by_sheet = self._get_account_move_by_sheet()

        move_line_values_by_expense = self._get_account_move_line_values()

        move_to_keep_draft = self.env['account.move']

        company_payments = self.env['account.payment']

        for expense in self:
            company_currency = expense.company_id.currency_id
            different_currency = expense.currency_id != company_currency

            # get the account move of the related sheet
            move = move_group_by_sheet[expense.sheet_id.id]

            # get move line values
            move_line_values = move_line_values_by_expense.get(expense.id)
            move_line_dst = move_line_values[-1]
            total_amount = move_line_dst['debit'] or -move_line_dst['credit']
            total_amount_currency = move_line_dst['amount_currency'] #total_amount_company

            # create one more move line, a counterline for the total on payable account
            if expense.payment_mode == 'company_account':
                if not expense.sheet_id.bank_journal_id.default_credit_account_id:
                    raise UserError(_("No credit account found for the %s journal, please configure one.") % (
                        expense.sheet_id.bank_journal_id.name))
                journal = expense.sheet_id.bank_journal_id
                # create payment
                payment_methods = journal.outbound_payment_method_ids if total_amount < 0 else journal.inbound_payment_method_ids
                journal_currency = journal.currency_id or journal.company_id.currency_id
                partner_id = expense.employee_id.address_home_id.commercial_partner_id
                payment = self.env['account.payment'].create({
                    'payment_method_id': payment_methods and payment_methods[0].id or False,
                    'payment_type': 'outbound' if total_amount < 0 else 'inbound',
                    'partner_id': partner_id.id if partner_id else False,
                    'partner_type': 'supplier',
                    'journal_id': journal.id,
                    'payment_date': expense.date,
                    'state': 'draft',
                    'currency_id': expense.currency_id.id if different_currency else journal_currency.id,
                    'amount': abs(total_amount_currency) if different_currency else abs(total_amount),
                    'name': expense.name,
                })
                move_line_dst['payment_id'] = payment.id

            # link move lines to move, and move to expense sheet
            move.write({'line_ids': [(0, 0, line) for line in move_line_values]})
            expense.sheet_id.write({
                'account_move_id': move.id,
                'account_move_ids': [(4, move.id)]
            })

            if expense.payment_mode == 'company_account':
                company_payments |= payment
                if journal.post_at == 'bank_rec':
                    move_to_keep_draft |= move

                expense.sheet_id.paid_expense_sheets()

        company_payments.filtered(lambda x: x.journal_id.post_at == 'pay_val').write({'state': 'reconciled'})
        company_payments.filtered(lambda x: x.journal_id.post_at == 'bank_rec').write({'state': 'posted'})

        # post the moves
        for move in move_group_by_sheet.values():
            if move in move_to_keep_draft:
                continue
            move.post()

        return move_group_by_sheet

    # override expense credit account to take journal credit account
    def _get_expense_account_destination(self):
        self.ensure_one()
        result = super(HRExpense, self)._get_expense_account_destination()
        if self.sheet_id.journal_id.default_credit_account_id:
            result = self.sheet_id.journal_id.default_credit_account_id.id
        return result

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})
        return True

    def action_cancel(self):
        for expense in self:
            if expense.sheet_id and expense.sheet_id.state not in ('draft', 'cancel'):
                raise UserError(_("You can only cancel expenses when Expense Report is Draft."))
            if expense.expense_picking_id and expense.expense_picking_id.state == 'done':
                raise UserError(_("You cannot cancel expenses when Receive Order is Done."))
            else:
                expense.write({'state': 'cancel'})
                if expense.sheet_id:
                    expense_sheet = self.env['hr.expense.sheet'].browse(expense.sheet_id.id)
                    expense.sheet_id = False
                    if len(expense_sheet.expense_line_ids) <= 0:
                        expense_sheet.unlink()
                if expense.expense_picking_id:
                    expense.expense_picking_ids = [(4, expense.expense_picking_id.id)]
                    expense.expense_picking_id.state = 'cancel'
        return True

    def create_picking(self):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            if not line.expense_picking_id or line.expense_picking_id.state == 'cancel':
                if line.product_id.type in ['product', 'consu']:
                    pick = {
                        'picking_type_id': line.picking_type_id.id,
                        'partner_id': line.partner_id.id,
                        'origin': '(Expenses) of ' + line.name,
                        'location_dest_id': line.location_dest_id.id,
                        'analytic_account_id': line.analytic_account_id.id,
                        'analytic_tag_ids': line.analytic_tag_ids.ids,
                        'location_id': line.location_id.id
                    }
                    picking = self.env['stock.picking'].create(pick)
                    line.expense_picking_id = picking.id
                    line.expense_picking_ids = [(4, line.expense_picking_id.id)]
                    unit_amount = self._get_discounted_price_unit()
                    price_unit = unit_amount
                    template = {
                        'name': line.name or '',
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom_id.id,
                        'location_id': line.location_id.id,
                        'location_dest_id': line.location_dest_id.id,
                        'picking_id': picking.id,
                        'state': 'draft',
                        'company_id': line.project_id.company_id.id,
                        'price_unit': price_unit,
                        'picking_type_id': line.picking_type_id.id,
                        'route_ids': 1 and [
                            (6, 0, [x.id for x in self.env['stock.location.route'].search([('id', 'in', (2, 3))])])] or [],
                        'warehouse_id': line.picking_type_id.warehouse_id.id,
                    }
                    diff_quantity = line.quantity
                    tmp = template.copy()
                    tmp.update({
                        'product_uom_qty': diff_quantity,
                    })
                    template['product_uom_qty'] = diff_quantity
                    done += moves.create(template)
                    move_ids = done._action_confirm()
                    move_ids._action_assign()
                self.state = 'received'
            else:
                self.state = 'draft'

    def action_view_picking_delivery(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        all_ids = self.expense_picking_ids.ids

        def recursive_backorders(list_bo):
            mylist = []
            for item in list_bo:
                mylist.append(item.id)
                if item.backorder_ids:
                    mylist.extend(recursive_backorders(item.backorder_ids))
            return mylist

        if self.expense_picking_id.backorder_ids:
            recursive = recursive_backorders(self.wh_id)
            all_ids = self.expense_picking_ids.ids
            all_ids.extend(recursive)

        domain = [
            ('return_picking_of_picking_id', 'in', all_ids)
        ]
        wh_return_ids = self.env['stock.picking'].search(domain)
        all_ids.extend(wh_return_ids.ids)
        action['domain'] = [('id', 'in', all_ids)]

        return action

    def _create_sheet_from_expenses(self):
        for exp in self:
            if any((expense.product_type in ['product', 'consu']) and (
                    not expense.expense_picking_id or expense.expense_picking_id.state != 'done') for expense in exp):
                raise UserError(_("You cannot create report until you receive products!"))
            if any((expense.product_type in ['product', 'consu']) and (
                    not expense.expense_picking_id or expense.expense_picking_id.state != 'done') for expense in exp):
                raise UserError(_("You cannot create report until you receive products!"))
            if any(expense.state not in ('draft', 'received') or expense.sheet_id for expense in exp):
                raise UserError(_("You cannot create two reports containing the same line!"))
            if len(exp.mapped('employee_id')) != 1:
                raise UserError(_("You cannot report expenses for different employees in the same report."))
            if any(not expense.product_id for expense in exp):
                raise UserError(_("You can not create report without product."))
            if any(expense.company_id and len(expense.company_id) > 1 for expense in exp):
                raise UserError(_("You can not create report from different companies."))

        todo = self.filtered(lambda x: x.payment_mode == 'own_account') or self.filtered(
            lambda x: x.payment_mode == 'company_account')
        sheet = self.env['hr.expense.sheet'].create({
            'company_id': exp.company_id.id,
            'employee_id': exp.employee_id.id,
            'name': todo[0].name if len(todo) == 1 else '',
            'expense_line_ids': [(6, 0, todo.ids)]
        })
        self.write({
            'state': 'to_submit'
        })
        sheet._onchange_employee_id()
        return sheet

    def unlink(self):
        for expense in self:
            if expense.state not in ['draft']:
                raise UserError(_('You can delete a drafted expense.'))
        return super(HRExpense, self).unlink()
