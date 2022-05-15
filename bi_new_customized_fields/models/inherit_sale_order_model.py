# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    def _set_default_standard_payment(self):
        return """<p style="font-size: 15px;">Payments are presented as a percentage of the contract value for these services. They are divided into the following payments:</p><ul style="font-size: 15px;"><li style="font-size: 15px;">80% advance payment.</li><li style="font-size: 15px;">20% upon commissioning.</li></ul><p style="font-size: 15px;">Maintenance visits (Corrective and preventive): to be paid 100% within 15 days of issuance of the report. Data Collection and monitoring: to be paid 100% quarterly in advance.</p>"""

    def _set_default_terms_conditions(self):
        return """<ul style="font-size: 15px;"><li style="font-size: 15px;">All prices are in EUR.</li><li style="font-size: 15px;">The proposal is exclusive of VAT.</li><li style="font-size: 15px;">The offer is valid for 30 days.</li></ul><br/>"""

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
