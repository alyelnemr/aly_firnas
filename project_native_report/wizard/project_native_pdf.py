
from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class ProjectNativeReport(models.TransientModel):
    _name = "project.native.report"

    project_id = fields.Many2one('project.project', 'Project', readonly=True)
    name = fields.Char(string='Name', default='PDF Report', readonly=True)

    def print_pdf(self):

        return self.env.ref('project_native_report.action_report_project_native_gantt').report_action([self.project_id.id])



