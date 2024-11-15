# -*- coding: utf-8 -*-

from collections import defaultdict
from odoo import api, fields, models
from odoo.tools import float_compare, float_round, float_is_zero, OrderedSet


class StockMove(models.Model):
    _inherit = "stock.move"

    lot_description = fields.Char(string='Lot Description')
    lot_ref = fields.Char(string='Lot Internal Reference')
    is_bonus_item = fields.Boolean(string='Is Bonus')

    def _prepare_procurement_values(self):
        res = super()._prepare_procurement_values()
        res.update({
            "account_analytic_id": self.group_id.sale_id.analytic_account_id.id,
            "analytic_tag_ids": self.group_id.sale_id.analytic_tag_ids.ids,
            "is_origin_so": True,
        })
        return res

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id,
                                       credit_account_id, description):
        res = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value,
                                                                    debit_account_id,
                                                                    credit_account_id, description)

        if self.picking_id.analytic_account_id:
            res['debit_line_vals']['analytic_account_id'] = self.picking_id.analytic_account_id.id
            res['credit_line_vals']['analytic_account_id'] = self.picking_id.analytic_account_id.id

        if self.picking_id.analytic_tag_ids:
            res['debit_line_vals']['analytic_tag_ids'] = self.picking_id.analytic_tag_ids.ids
            res['credit_line_vals']['analytic_tag_ids'] = self.picking_id.analytic_tag_ids.ids

        return res

    @api.model
    def create(self, vals):
        if vals.get('name', False):
            vals['description_picking'] = vals['name']

        res = super(StockMove, self).create(vals)
        return res

    def _get_price_unit(self):
        """Get correct price with discount replacing current price_unit
        value before calling super and restoring it later for assuring
        maximum inheritability.

        HACK: This is needed while https://github.com/odoo/odoo/pull/29983
        is not merged.
        """
        price_unit = False
        po_line = self.purchase_line_id.sudo()
        if po_line and self.product_id == po_line.product_id:
            price = po_line._get_discounted_price_unit()
            if price != po_line.price_unit:
                # Only change value if it's different
                price_unit = po_line.price_unit
                po_line.sudo().price_unit = price
        res = super()._get_price_unit()
        if price_unit:
            po_line.sudo().price_unit = price_unit
        return res

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        self.ensure_one()
        AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)

        move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
        if move_lines:
            date = self._context.get('force_period_date', fields.Date.context_today(self))
            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'analytic_account_id': self.picking_id.analytic_account_id.id,
                'analytic_tag_ids': self.picking_id.analytic_tag_ids.ids,
                'ref': description,
                'stock_move_id': self.id,
                'stock_valuation_layer_ids': [(6, None, [svl_id])],
                'type': 'entry',
            })
            new_account_move.post()

    def _generate_serial_move_line_commands(self, lot_names, origin_move_line=None):
        """Return a list of commands to update the move lines (write on
        existing ones or create new ones).
        Called when user want to create and assign multiple serial numbers in
        one time (using the button/wizard or copy-paste a list in the field).

        :param lot_names: A list containing all serial number to assign.
        :type lot_names: list
        :param origin_move_line: A move line to duplicate the value from, default to None
        :type origin_move_line: record of :class:`stock.move.line`
        :return: A list of commands to create/update :class:`stock.move.line`
        :rtype: list
        """
        self.ensure_one()

        # Select the right move lines depending of the picking type configuration.
        move_lines = self.env['stock.move.line']
        if self.picking_type_id.show_reserved:
            move_lines = self.move_line_ids.filtered(lambda ml: not ml.lot_id and not ml.lot_name)
        else:
            move_lines = self.move_line_nosuggest_ids.filtered(lambda ml: not ml.lot_id and not ml.lot_name)

        if origin_move_line:
            location_dest = origin_move_line.location_dest_id
        else:
            location_dest = self.location_dest_id._get_putaway_strategy(self.product_id)
        move_line_vals = {
            'picking_id': self.picking_id.id,
            'location_dest_id': location_dest.id or self.location_dest_id.id,
            'location_id': self.location_id.id,
            'lot_description': self.description_picking.replace("<p>", "").replace("</p>", ""),
            'product_id': self.product_id.id,
            'product_uom_id': self.product_id.uom_id.id,
            'qty_done': 1,
        }
        if origin_move_line:
            # `owner_id` and `package_id` are taken only in the case we create
            # new move lines from an existing move line. Also, updates the
            # `qty_done` because it could be usefull for products tracked by lot.
            move_line_vals.update({
                'owner_id': origin_move_line.owner_id.id,
                'package_id': origin_move_line.package_id.id,
                'qty_done': origin_move_line.qty_done or 1,
            })

        move_lines_commands = []
        for lot_name in lot_names:
            # We write the lot name on an existing move line (if we have still one)...
            if move_lines:
                move_lines_commands.append((1, move_lines[0].id, {
                    'lot_name': lot_name,
                    'qty_done': 1,
                }))
                move_lines = move_lines[1:]
            # ... or create a new move line with the serial name.
            else:
                move_line_cmd = dict(move_line_vals, lot_name=lot_name)
                move_lines_commands.append((0, 0, move_line_cmd))
        return move_lines_commands

    def product_price_update_before_done(self, forced_qty=None):
        tmpl_dict = defaultdict(lambda: 0.0)
        # adapt standard price on incomming moves if the product cost_method is 'average'
        std_price_update = {}
        for move in self.filtered(lambda move: move._is_in() and move.with_context(
                force_company=move.company_id.id).product_id.cost_method == 'average'):
            if not move.is_bonus_item:
                product_tot_qty_available = move.product_id.sudo().with_context(force_company=move.company_id.id).quantity_svl + \
                                            tmpl_dict[move.product_id.id]
                rounding = move.product_id.uom_id.rounding

                valued_move_lines = move._get_in_move_lines()
                qty_done = 0
                for valued_move_line in valued_move_lines:
                    qty_done += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done,
                                                                                  move.product_id.uom_id)

                qty = forced_qty or qty_done
                if float_is_zero(product_tot_qty_available, precision_rounding=rounding):
                    new_std_price = move._get_price_unit()
                elif float_is_zero(product_tot_qty_available + move.product_qty, precision_rounding=rounding) or \
                        float_is_zero(product_tot_qty_available + qty, precision_rounding=rounding):
                    new_std_price = move._get_price_unit()
                else:
                    # Get the standard price
                    amount_unit = std_price_update.get((move.company_id.id, move.product_id.id)) or move.product_id.with_context(
                        force_company=move.company_id.id).standard_price
                    new_std_price = ((amount_unit * product_tot_qty_available) + (move._get_price_unit() * qty)) / (
                            product_tot_qty_available + qty)

                tmpl_dict[move.product_id.id] += qty_done
                # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
                move.product_id.with_context(force_company=move.company_id.id).sudo().write({'standard_price': new_std_price})
                std_price_update[move.company_id.id, move.product_id.id] = new_std_price