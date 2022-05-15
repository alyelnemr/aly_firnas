from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

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
