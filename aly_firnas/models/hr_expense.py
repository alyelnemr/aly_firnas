# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HRExpense(models.Model):
    _inherit = 'hr.expense'

    @api.model
    def _default_employee_id(self):
        return self.env.user.employee_id

    @api.model
    def _get_employee_id_domain(self):
        res = [('id', '=', 0)]  # Nothing accepted by domain, by default
        if self.user_has_groups('hr_expense.group_hr_expense_user') or self.user_has_groups('account.group_account_user'):
            res = "['|', ('company_id', '=', False), ('company_id', '=', [c.id for c in self.env.user.company_ids])]"  # Then, domain accepts everything
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
            if expense.project_id:
                expense.company_id = expense.project_id.company_id.id
                expense.analytic_account_id = expense.project_id.analytic_account_id.id

    @api.onchange('analytic_account_id')
    def _set_analytic_account_data(self):
        for expense in self:
            if expense.analytic_account_id:
                analytic_tag_ids = expense.analytic_account_id.analytic_tag_ids
                if expense.employee_id:
                    analytic_tag_ids += expense.employee_id.analytic_tag_ids
                expense.analytic_tag_ids = analytic_tag_ids

    @api.model
    def _default_company_id(self):
        return self.project_id.company_id

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

    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', required=True,
                                      default=_default_picking_receive,
                                      help="This will determine picking type of incoming shipment")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]}, default=_default_employee_id,
                                  check_company=False)
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, change_default=True,
                                 tracking=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    vendor_contact = fields.Many2one('res.partner', string='Vendor Contacts', required=False,
                                     domain="[('parent_id', '=', partner_id)]")
    user_to_approve_id = fields.Many2one('res.users', 'User To Approve', readonly=True, copy=False, states={'draft': [('readonly', False)]},
                              tracking=True)
    project_id = fields.Many2one('project.project', 'Project', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]}, default=_default_company_id)
    expense_picking_id = fields.Many2one('stock.picking', string="Picking ID")
    picking_count = fields.Integer(string="Count", compute='_compute_picking_count', store=False)

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
