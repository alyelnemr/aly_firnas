# -*- coding: utf-8 -*-
import datetime

from odoo import api, fields, models


class DuplicateSalesOrderWizard(models.TransientModel):
    _name = 'duplicate.sale.order.wizard'

    wizard_opportunity_id = fields.Many2one('crm.lead', string='Opportunity')

    def duplicate_sale_order(self):
        active_ids = self._context.get('active_ids')
        sale_order_obj = self.env['sale.order']
        for active_id in active_ids:
            sale_obj = sale_order_obj.browse(active_id)
            warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', self.wizard_opportunity_id.company_id.id)], limit=1)

            lines_option = sale_obj.sale_order_option_ids.mapped('line_id')
            lines_additional = sale_obj.sale_order_additional_ids.mapped('line_id')
            order_lines = sale_obj.order_line.filtered(lambda l: not l.is_downpayment and l not in lines_option and l not in lines_additional)
            order_lines = order_lines.filtered(lambda line: not line.parent_order_line)
            order_line_to_copy = [(0, 0, line.copy_data()[0]) for line in order_lines]

            vals = {
                'opportunity_id': self.wizard_opportunity_id.id,
                'partner_id': self.wizard_opportunity_id.partner_id.id,
                'partner_invoice_id': self.wizard_opportunity_id.partner_id.id,
                'partner_shipping_id': self.wizard_opportunity_id.partner_id.id,
                'partner_contact': self.wizard_opportunity_id.partner_contact.id,
                'analytic_account_id': self.wizard_opportunity_id.analytic_account_id.id,
                'analytic_tag_ids': self.wizard_opportunity_id.analytic_tag_ids_for_analytic_account.ids,
                'company_id': self.wizard_opportunity_id.company_id.id,
                'user_id': self.wizard_opportunity_id.user_id.id,
                'warehouse_id': warehouse_id.id,
                'date_order': datetime.datetime.now(),
                'payment_term_id': False,
                'project_name': self.wizard_opportunity_id.project_name,
                'client_name_id': self.wizard_opportunity_id.end_client.ids,
                'fund': self.wizard_opportunity_id.fund.id,
                'partnership_model': self.wizard_opportunity_id.partnership_model.id,
                'sub_type': self.wizard_opportunity_id.sub_type.id,
                'actual_sub_date': self.wizard_opportunity_id.actual_sub_date,
                'sub_date': self.wizard_opportunity_id.sub_date,
                'start_date': self.wizard_opportunity_id.start_date,
                'source_id': self.wizard_opportunity_id.source_id.id,
                'currency_id': self.wizard_opportunity_id.currency_id.id,
                'country': self.wizard_opportunity_id.country.ids,
                'partner': self.wizard_opportunity_id.partner.ids,
                'project_name': self.wizard_opportunity_id.project_name,
                'forecast': self.wizard_opportunity_id.forecast,
                'project_number': self.wizard_opportunity_id.project_num,
                'document_name': self.wizard_opportunity_id.proposal_subject,
                'file_name': self.wizard_opportunity_id.document_file_name,
                'proposals_engineer_id': self.wizard_opportunity_id.proposals_engineer_id.id,
                'type_custom': self.wizard_opportunity_id.type_custom.id,
                'type_custom_ids': self.wizard_opportunity_id.type_custom_ids.ids,
                'internal_opportunity_name': self.wizard_opportunity_id.internal_opportunity_name,
                'rfp_ref_number': self.wizard_opportunity_id.rfp_ref_number,
                'subcontractor_supplier_ids': self.wizard_opportunity_id.subcontractor_supplier_ids.ids,
                'proposal_reviewer_ids': self.wizard_opportunity_id.proposal_reviewer_ids.ids,
                'latest_proposal_submission_date': self.wizard_opportunity_id.latest_proposal_submission_date,
                'result_date': self.wizard_opportunity_id.result_date,
                'contract_signature_date': self.wizard_opportunity_id.contract_signature_date,
                'initial_contact_date': self.wizard_opportunity_id.initial_contact_date,
                'order_line': order_line_to_copy
            }
            sale_copy = sale_obj.with_context(ignore=True).copy(default=vals)
            for line in sale_copy.order_line:
                line.analytic_account_id = sale_copy.analytic_account_id.id
                line.analytic_tag_ids = sale_copy.analytic_tag_ids.ids
            sale_copy.sale_order_option_ids.filtered(lambda l: l.is_button_clicked).write({'is_button_clicked': False})
            sale_copy.sale_order_additional_ids.filtered(lambda l: l.is_button_clicked).write({'is_button_clicked': False})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': sale_copy.id,
            'view_mode': 'form',
        }
