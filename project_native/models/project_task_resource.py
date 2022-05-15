# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
from lxml import etree

import datetime
from dateutil import tz
import pytz
import time
from string import Template
from datetime import datetime, timedelta
from odoo.exceptions import  Warning
from pdb import set_trace as bp

from itertools import groupby
from operator import itemgetter

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)  # Need for message in console.



class ProjectTaskNativeResource(models.Model):
    _name = 'project.task'
    _inherit = 'project.task'

    task_resource_ids = fields.One2many('project.task.resource.link', 'task_id', 'Resources')


class ProjectTaskResourceLink(models.Model):
    _name = 'project.task.resource.link'

    _order = 'date_start'


    name = fields.Char(compute='_compute_name_link', readonly=True, store=False)

    resource_id = fields.Many2one('resource.resource', 'Resource', ondelete='restrict')
    task_id = fields.Many2one('project.task', 'Task', ondelete='restrict', readonly=True,)
    load_factor = fields.Float("Load Factor", default=1.0)

    resource_type = fields.Selection(string='Type', related="resource_id.resource_type", readonly=True, store=True)
    date_start = fields.Datetime(related='task_id.date_start', string="Date Start",  store=True, readonly=True,)
    date_end = fields.Datetime(related='task_id.date_end', string="Date End",  store=True, readonly=True,)
    duration = fields.Integer(related='task_id.duration', string='Duration',  store=True, readonly=True,)
    project_id = fields.Many2one(related='task_id.project_id', string='Duration', store=True, readonly=True,)

    color_gantt_set = fields.Boolean("Set Color Task", default=False)
    color_gantt = fields.Char(
        string="Color Task Bar",
        help="Choose your color for Task Bar",
        default="rgba(170,170,13,0.53)"
    )

    load_control = fields.Boolean(name="Load Control", help="Allow Resource Load Control", default=True)


    @api.depends('task_id', 'load_factor', 'resource_id', 'resource_type')
    def _compute_name_link(self):
        for record in self:
            record.name = "{}-{} ({}) {}".format(record.project_id.name or "", record.task_id.name or "", record.resource_id.name, record.load_factor or "")


    def write(self, vals):

        result = super(ProjectTaskResourceLink, self).write(vals)
        if result:
            for rec in self:
                info_name = "res_{}".format(rec.id)
                info_task = self.env['project.task.info'].sudo().search([('name', '=', info_name)])
                if info_task:
                    info_task.sudo().write({"end": rec.resource_id.name})

        return result


    def unlink(self):
        res = super(ProjectTaskResourceLink, self).unlink()

        if res:
            self.env['project.task'].sudo()._task_info_remove(info_name="res_{}".format(self.id))

        return res

    @api.model
    def create(self, vals):

        new_id = super(ProjectTaskResourceLink, self).create(vals)

        if new_id:
            info_name = "res_{}".format(new_id.id)
            value = {}
            value["name"] = info_name
            value["end"] = new_id.resource_id.name
            value["show"] = True

            vals = {}
            vals["info_ids"] = [(0, 0, value)]
            new_id.task_id.write(vals)

        return new_id



    _sql_constraints = [
            ('project_task_resource_link_uniq', 'unique(task_id, resource_id)', 'Duplicate Resource.'),
        ]



