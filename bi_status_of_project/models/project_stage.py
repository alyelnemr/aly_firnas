# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class Stage(models.Model):
    _name = "project.stage"
    _description = 'Project Stage'
    _order = 'sequence, id'

    # def _get_default_project_ids(self):
    #     default_project_id = self.env.context.get('default_project_id')
    #     return [default_project_id] if default_project_id else None

    name = fields.Char(string='Stage Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    project_ids = fields.Many2many('project.project', 'project_project_type_rel', 'type_id', 'project_id',
                                   string='Projects')
    legend_blocked = fields.Char(
        'Red Kanban Label', default=lambda s: _('Blocked'), translate=True, required=True,
        help='Override the default value displayed for the blocked state for kanban selection, when the project or issue is in that stage.')
    legend_done = fields.Char(
        'Green Kanban Label', default=lambda s: _('Ready for Next Stage'), translate=True, required=True,
        help='Override the default value displayed for the done state for kanban selection, when the project or issue is in that stage.')
    legend_normal = fields.Char(
        'Grey Kanban Label', default=lambda s: _('In Progress'), translate=True, required=True,
        help='Override the default value displayed for the normal state for kanban selection, when the project or issue is in that stage.')
    mail_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain=[('model', '=', 'project.project')],
        help="If set an email will be sent to the customer when the project or issue reaches this step.")
    fold = fields.Boolean(string='Folded in Kanban',
                          help='This stage is folded in the kanban view when there are no records in that stage to display.')
    rating_template_id = fields.Many2one(
        'mail.template',
        string='Rating Email Template',
        domain=[('model', '=', 'project.project')],
        help="If set and if the project's rating configuration is 'Rating when changing stage', then an email will be sent to the customer when the project reaches this step.")
    auto_validation_kanban_state = fields.Boolean('Automatic kanban status', default=False,
                                                  help="Automatically modify the kanban state when the customer replies to the feedback for this stage.\n"
                                                       " * A good feedback from the customer will update the kanban state to 'ready for the new stage' (green bullet).\n"
                                                       " * A medium or a bad feedback will set the kanban state to 'blocked' (red bullet).\n")

    def unlink(self):
        stages = self
        default_project_id = self.env.context.get('default_project_id')
        if default_project_id:
            shared_stages = self.filtered(lambda x: len(x.project_ids) > 1 and default_project_id in x.project_ids.ids)
            projects = self.env['project.project'].with_context(active_test=False).search('stage_id', 'in', self.ids)
            if shared_stages and not projects:
                shared_stages.write({'project_ids': [(3, default_project_id)]})
                stages = self.filtered(lambda x: x not in shared_stages)
        return super(Stage, stages).unlink()
