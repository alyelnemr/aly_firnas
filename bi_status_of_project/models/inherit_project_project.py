# -*- coding: utf-8 -*-
from odoo import api, fields, models

from odoo import SUPERUSER_ID


class ProjectProjectInherit(models.Model):
    _name = "project.project"
    _inherit = 'project.project'

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        project_id = self.env.context.get('default_project_id')
        if not project_id:
            return False
        return self.stage_find(project_id, [('fold', '=', False)])

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Important'),
    ], default='0', index=True, string="Priority")
    sequence = fields.Integer(string='Sequence', index=True, default=10,
                              help="Gives the sequence order when displaying a list of projects.")
    stage_id = fields.Many2one('project.stage', string='Stage', ondelete='restrict', tracking=True, index=True,
                               group_expand='_read_group_stage_ids', copy=True)
    tag_ids = fields.Many2many('project.tag', string='Tags')
    name = fields.Char(string='Title', tracking=True, required=True, index=True)
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Important'),
    ], default='0', index=True, string="Priority")
    kanban_state = fields.Selection([
        ('normal', 'Grey'),
        ('done', 'Green'),
        ('blocked', 'Red')], string='Kanban State',
        copy=False, default='normal', required=True)
    # kanban_state_label = fields.Char(compute='_compute_kanban_state_label', string='Kanban State Label', tracking=True)
    legend_normal = fields.Char(related='stage_id.legend_normal', string='Kanban Ongoing Explanation', readonly=True,
                                related_sudo=False)
    legend_blocked = fields.Char(related='stage_id.legend_blocked', string='Kanban Blocked Explanation', readonly=True,
                                 related_sudo=False)
    legend_done = fields.Char(related='stage_id.legend_done', string='Kanban Valid Explanation', readonly=True,
                              related_sudo=False)

    # @api.depends('stage_id', 'kanban_state')
    # def _compute_kanban_state_label(self):
    #     for project in self:
    #         if project.kanban_state == 'normal':
    #             project.kanban_state_label = project.legend_normal
    #         elif project.kanban_state == 'blocked':
    #             project.kanban_state_label = project.legend_blocked
    #         else:
    #             project.kanban_state_label = project.legend_done

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        search_domain = [('id', 'in', stages.ids)]
        # if 'default_project_id' in self.env.context:
        #     search_domain = ['|', ('project_ids', '=', self.env.context['default_project_id'])] + search_domain

        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)


class ProjectTag(models.Model):
    """ Tags of projects """
    _name = "project.tag"
    _description = "Project Tag"

    name = fields.Char('Tag Name', required=True)
    color = fields.Integer(string='Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists!"),
    ]
