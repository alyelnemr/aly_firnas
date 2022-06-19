# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    def _set_default_standard_payment(self):
        return self.env['ir.config_parameter'].sudo().get_param('aly_so_payment_schedule')

    def _set_default_terms_conditions(self):
        return self.env['ir.config_parameter'].sudo().get_param('aly_so_terms_condition')

    project_name = fields.Char(string="Customer's Project Name / Proposal Title")
    document_name = fields.Char(string="Proposal Subject")
    file_name = fields.Char(string="Document/File  Name (Footer)")
    standard_payment_schedule = fields.Html(string="Standard Payment Schedule", default=_set_default_standard_payment)
    terms_and_conditions = fields.Html(string="Terms And Conditions", default=_set_default_terms_conditions)

    serial_num = fields.Char(string="Serial Number")
    project_number = fields.Char(string="Project Number", store=True)
    type_custom = fields.Char(string="Type")
    country = fields.Many2many('res.country', string='Country')
    start_date = fields.Date(string="Start Date")
    sub_date = fields.Datetime(string="Submission Deadline")
    sub_type = fields.Many2one('project.submission', string="Submission Type")
    # source = fields.Many2one('project.source', string="Source", store=True)
    fund = fields.Many2one('project.fund', string="Funding")
    partnership_model = fields.Many2one('project.partnership', string="Partnership Model")
    partner = fields.Many2many('res.partner', string="Partner") #, related='opportunity_id.partner'
    client_name = fields.Many2many('client.name', string="Client")
    rfp_ref_number = fields.Char(string='RfP Ref. Number')
    proposals_engineer_id = fields.Many2one('res.users', string='Proposals Engineer')
