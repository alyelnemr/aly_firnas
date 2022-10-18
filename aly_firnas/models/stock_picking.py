# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    is_origin_so = fields.Boolean(copy=False)
    return_picking_of_picking_id = fields.Many2one(comodel_name='stock.picking', string='Return of',
                                                   help='This picking a return picking of')
    required_analytic_account_and_tags = fields.Boolean(string='Required Analytic Account And Tags',
                                                        compute='_compute_required_analytic_account_and_tags')

    @api.depends('picking_type_id.code')
    def _compute_required_analytic_account_and_tags(self):
        for record in self:
            if record.picking_type_id.code not in ('internal', 'mrp_operation'):
                record.required_analytic_account_and_tags = True
            else:
                record.required_analytic_account_and_tags = False

    def action_get_account_moves(self):
        self.ensure_one()
        action_data = self.env.ref('account.action_move_journal_line').read()[0]
        action_data['domain'] = [('id', 'in', self.move_ids_without_package.account_move_ids.ids)]
        return action_data

    @api.model
    def create(self, vals):
        if vals.get('origin'):
            order = []
            if vals.get('origin')[0] == 'S':
                order = self.env['sale.order'].sudo().search([('name', '=', vals.get('origin'))])
            elif vals.get('origin')[0] == 'P':
                order = self.env['purchase.order'].sudo().search([('name', '=', vals.get('origin'))])

            if order:
                if order.analytic_account_id:
                    vals['analytic_account_id'] = order.analytic_account_id.ids[0] if order.analytic_account_id.ids else order.analytic_account_id.id

                if order.analytic_tag_ids:
                    vals['analytic_tag_ids'] = order.analytic_tag_ids.ids

                vals['is_origin_so'] = True

        res = super(StockPicking, self).create(vals)
        return res
