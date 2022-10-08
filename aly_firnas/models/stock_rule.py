# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _prepare_purchase_order_line(
            self, product_id, product_qty, product_uom, company_id, values, po
    ):
        res = super()._prepare_purchase_order_line(
            product_id, product_qty, product_uom, company_id, values, po
        )
        res.update({
            "account_analytic_id": values.get("account_analytic_id", False),
            "analytic_tag_ids": values.get("analytic_tag_ids", False),
            "is_origin_so": values.get("is_origin_so", False),
        })
        po.is_origin_so= values.get("is_origin_so", False)
        if po.is_origin_so:
            po.analytic_account_id=values['group_id'].sale_id.analytic_account_id.id 
            po.analytic_tag_ids=values['group_id'].sale_id.analytic_tag_ids.ids
        return res

    def _make_po_get_domain(self, company_id, values, partner):
        res = super()._make_po_get_domain(company_id, values, partner)
        res += (
            (
                "order_line.account_analytic_id",
                "=",
                values.get("account_analytic_id", False),
            ),
        )
        return res
