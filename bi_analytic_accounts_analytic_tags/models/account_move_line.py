# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class InheritAccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True,
                                          required=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', required=True)

    is_origin_so = fields.Boolean(copy=False)

    @api.onchange('product_id')
    def get_analytic_default(self):
        for rec in self:
            if not rec.analytic_account_id and rec.move_id.analytic_account_id:
                rec.analytic_account_id = rec.move_id.analytic_account_id.id
            if not rec.analytic_tag_ids and rec.move_id.analytic_tag_ids:
                rec.analytic_tag_ids = rec.move_id.analytic_tag_ids.ids

    @api.model_create_multi
    def create(self, vals):
        lines = super(InheritAccountMoveLine, self).create(vals)
        for line in lines:
            if line.move_id.invoice_line_ids:
                analytic_account_id = line.move_id.invoice_line_ids[0].analytic_account_id
                analytic_tag_ids = line.move_id.invoice_line_ids[0].analytic_tag_ids

                if analytic_account_id:
                    line.analytic_account_id = analytic_account_id.id if not line.analytic_account_id else line.analytic_account_id

                if analytic_tag_ids:
                    line.analytic_tag_ids = analytic_tag_ids.ids if not line.analytic_tag_ids else line.analytic_tag_ids

        return lines

    # def write(self, vals):
    #     for line in self:
    #         if 'analytic_account_id' in vals:
    #             for item in line.move_id.invoice_line_ids:
    #                 item.analytic_account_id = vals['analytic_account_id']
    #         if 'analytic_tag_ids' in vals:
    #             for item in line.move_id.invoice_line_ids:
    #                 item.analytic_tag_ids = vals['analytic_tag_ids']
    #     lines = super(InheritAccountMoveLine, self).write(vals)
    #     return lines
