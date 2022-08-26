# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero


class HRExpense(models.Model):
    _inherit = 'hr.expense'

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

    @api.depends('quantity', 'unit_amount', 'tax_ids', 'currency_id')
    def _compute_amount(self):
        for expense in self:
            expense.untaxed_amount = expense.unit_amount * expense.quantity
            taxes = expense.tax_ids.compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id,
                                                expense.employee_id.user_id.partner_id)
            expense.total_amount = taxes.get('total_included')

    @api.onchange('project_id')
    def _set_project_data(self):
        for expense in self:
            analytic_tag_ids = []
            if expense.project_id:
                expense.company_id = expense.project_id.company_id.id
                expense.analytic_account_id = expense.project_id.analytic_account_id.id
                expense.employee_id = self.env.user.employee_id.id
            if expense.analytic_account_id:
                analytic_tag_ids = expense.analytic_account_id.analytic_tag_ids
            if expense.employee_id:
                analytic_tag_ids += expense.employee_id.analytic_tag_ids
            expense.analytic_tag_ids = analytic_tag_ids

    @api.onchange('company_id')
    def _set_current_user(self):
        for expense in self:
            analytic_tag_ids = []
            if self.env.user.employee_id:
                expense.employee_id = self.env.user.employee_id.id
            if expense.analytic_account_id:
                analytic_tag_ids = expense.analytic_account_id.analytic_tag_ids
            if expense.employee_id:
                analytic_tag_ids += expense.employee_id.analytic_tag_ids
            expense.analytic_tag_ids = analytic_tag_ids

    @api.onchange('analytic_account_id')
    def _set_analytic_account_data(self):
        for expense in self:
            analytic_tag_ids = []
            if expense.analytic_account_id:
                analytic_tag_ids = expense.analytic_account_id.analytic_tag_ids
            if expense.employee_id:
                analytic_tag_ids += expense.employee_id.analytic_tag_ids
            expense.analytic_tag_ids = analytic_tag_ids

    @api.model
    def _default_company_id(self):
        if self.project_id:
            return self.project_id.company_id
        return self.env.user.company_id

    def _compute_picking_count(self):
        if self.expense_picking_id:
            picking_type_ids = self.env['stock.picking'].browse(self.expense_picking_id.id)
            if picking_type_ids:
                self.picking_count = len(picking_type_ids)
            else:
                self.picking_count = 0
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

    is_same_currency = fields.Boolean("Is Same Currency as Company Currency", compute='_change_currency')
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', required=True,
                                      default=_default_picking_receive,
                                      help="This will determine picking type of incoming shipment")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True,
                                  readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]},
                                  default=lambda self: self.env.user.employee_id, check_company=False)
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, change_default=True,
                                 tracking=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    vendor_contact_id = fields.Many2one('res.partner', string='Vendor Contacts', required=False,
                                     domain="[('parent_id', '=', partner_id)]")
    project_id = fields.Many2one('project.project', 'Project', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]}, default=_default_company_id)
    expense_picking_id = fields.Many2one('stock.picking', string="Picking ID")
    picking_count = fields.Integer(string="Count", compute='_compute_picking_count', store=False)
    payment_mode = fields.Selection([
        ("own_account", "Employee (to reimburse)"),
        ("company_account", "Company")
    ], default='company_account', readonly=True, string="Paid By")
    attachment_document = fields.Binary(string='Attachment', required=False)
    journal_id = fields.Many2one('account.journal', string='Expense Journal',
                                 states={'done': [('readonly', True)], 'post': [('readonly', True)]}, check_company=True,
                                 domain="[('type', '=', 'purchase'), ('company_id', '=', company_id)]",
                                 default=_default_journal_id, help="The journal used when the expense is done.")
    bank_journal_id = fields.Many2one('account.journal', string='Bank Journal',
                                      states={'done': [('readonly', True)], 'post': [('readonly', True)]}, check_company=True,
                                      domain="[('type', 'in', ['cash', 'bank']), ('company_id', '=', company_id)]",
                                      default=_default_bank_journal_id,
                                      help="The payment method used when the expense is paid by the company.")

    def action_sheet_move_create(self):
        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids') \
            .filtered(lambda r: not float_is_zero(r.total_amount,
                                                  precision_rounding=(r.currency_id or self.env.company.currency_id).rounding))
        res = expense_line_ids.action_move_create()

        if not self.accounting_date:
            self.accounting_date = self.account_move_id.date

        if self.payment_mode == 'own_account' and expense_line_ids:
            self.write({'state': 'post'})
        else:
            self.write({'state': 'done'})
        self.activity_update()
        return res

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
            taxes = expense.tax_ids.with_context(round=True).compute_all(expense.unit_amount, expense.currency_id,
                                                                         expense.quantity, expense.product_id)
            total_amount = 0.0
            total_amount_currency = 0.0
            partner_id = expense.employee_id.address_home_id.commercial_partner_id.id

            # source move line
            amount = taxes['total_excluded']
            amount_currency = False
            if different_currency:
                amount = expense.total_amount_company # get the value entered from the screen instead of converting currencies, as request from Eng. Mostafa El Bedawy
                # amount = expense.currency_id._convert(amount, company_currency, expense.company_id, account_date)
                amount_currency = taxes['total_excluded']
            move_line_src = {
                'name': move_line_name,
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
                'partner_id': partner_id,
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
                    'partner_id': partner_id,
                    'currency_id': expense.currency_id.id if different_currency else False,
                    'analytic_account_id': expense.analytic_account_id.id if tax['analytic'] else False,
                    'analytic_tag_ids': [(6, 0, expense.analytic_tag_ids.ids)] if tax['analytic'] else False,
                }
                total_amount -= amount
                total_amount_currency -= move_line_tax_values['amount_currency'] or amount
                move_line_values.append(move_line_tax_values)

            # destination move line
            move_line_dst = {
                'name': move_line_name,
                'debit': total_amount > 0 and total_amount,
                'credit': total_amount < 0 and -total_amount,
                'account_id': account_dst,
                'date_maturity': account_date,
                'amount_currency': total_amount_currency if different_currency else 0.0,
                'currency_id': expense.currency_id.id if different_currency else False,
                'expense_id': expense.id,
                'partner_id': partner_id,
            }
            move_line_values.append(move_line_dst)

            move_line_values_by_expense[expense.id] = move_line_values
        return move_line_values_by_expense

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
                payment = self.env['account.payment'].create({
                    'payment_method_id': payment_methods and payment_methods[0].id or False,
                    'payment_type': 'outbound' if total_amount < 0 else 'inbound',
                    'partner_id': expense.employee_id.address_home_id.commercial_partner_id.id,
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
            expense.sheet_id.write({'account_move_id': move.id})

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

    @api.model
    def create(self, vals):
        res = super(HRExpense, self).create(vals)
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in res:
            if line.product_id.type in ['product', 'consu']:
                pick = {
                    'picking_type_id': line.picking_type_id.id,
                    'partner_id': line.partner_id.id,
                    'origin': '(Expenses) of ' + line.name,
                    'location_dest_id': self.picking_type_id.default_location_dest_id.id,
                    'location_id': self.partner_id.property_stock_supplier.id
                }
                picking = self.env['stock.picking'].create(pick)
                line.expense_picking_id = picking.id
                price_unit = line.unit_amount
                template = {
                    'name': line.name or '',
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'location_id': line.partner_id.property_stock_supplier.id,
                    'location_dest_id': line.picking_type_id.default_location_dest_id.id,
                    'picking_id': picking.id,
                    'state': 'draft',
                    'company_id': line.company_id.id,
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
        return res

    def write(self, vals):
        res = super(HRExpense, self).write(vals)
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            if line.product_id.type in ['product', 'consu'] and not line.expense_picking_id:
                pick = {
                    'picking_type_id': line.picking_type_id.id,
                    'partner_id': line.partner_id.id,
                    'origin': 'Expense of ' + line.name,
                    'location_dest_id': self.picking_type_id.default_location_dest_id.id,
                    'location_id': self.partner_id.property_stock_supplier.id
                }
                picking = self.env['stock.picking'].create(pick)
                line.expense_picking_id = picking.id
                price_unit = line.unit_amount
                template = {
                    'name': line.name or '',
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'location_id': line.partner_id.property_stock_supplier.id,
                    'location_dest_id': line.picking_type_id.default_location_dest_id.id,
                    'picking_id': picking.id,
                    'state': 'draft',
                    'company_id': line.company_id.id,
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
        return res

    def action_view_picking_delivery(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        pickings = self.env['stock.picking'].browse(self.expense_picking_id.id)
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings[0].id
        return action
