# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.float_utils import float_is_zero


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _order = 'create_date DESC'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    is_origin_so = fields.Boolean(copy=False)
    return_picking_of_picking_id = fields.Many2one(comodel_name='stock.picking', string='Return of',
                                                   help='This picking a return picking of')
    required_analytic_account_and_tags = fields.Boolean(string='Required Analytic Account And Tags',
                                                        compute='_compute_required_analytic_account_and_tags')
    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location",
        default=lambda self: self.env['stock.picking.type'].browse(
            self._context.get('default_picking_type_id')).default_location_dest_id,
        check_company=True, readonly=False, required=True,
        states={'draft': [('readonly', False)]})
    reject_url = fields.Char('Reject URL')
    approve_url = fields.Char('Approve URL')
    user_to_approve_url = fields.Integer('User ID to Approve')

    def write(self, vals):
        # set partner as a follower and unfollow old partner
        if vals.get('partner_id'):
            for picking in self:
                if picking.location_id.usage == 'supplier' or picking.location_dest_id.usage == 'customer':
                    if picking.partner_id:
                        picking.message_unsubscribe(picking.partner_id.ids)
                    picking.message_subscribe([vals.get('partner_id')])
        res = super(models.Model, self).write(vals)
        # Change locations of moves if those of the picking change
        after_vals = {}
        if vals.get('location_id'):
            after_vals['location_id'] = vals['location_id']
        if vals.get('location_dest_id'):
            after_vals['location_dest_id'] = vals['location_dest_id']
        if 'partner_id' in vals:
            after_vals['partner_id'] = vals['partner_id']
        if after_vals:
            self.mapped('move_lines').filtered(lambda move: not move.scrapped).write(after_vals)
        if vals.get('move_lines'):
            # Do not run autoconfirm if any of the moves has an initial demand. If an initial demand
            # is present in any of the moves, it means the picking was created through the "planned
            # transfer" mechanism.
            pickings_to_not_autoconfirm = self.env['stock.picking']
            for picking in self:
                if picking.state != 'draft':
                    continue
                for move in picking.move_lines:
                    if not float_is_zero(move.product_uom_qty, precision_rounding=move.product_uom.rounding):
                        pickings_to_not_autoconfirm |= picking
                        break
            (self - pickings_to_not_autoconfirm)._autoconfirm_picking()
        return res

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
