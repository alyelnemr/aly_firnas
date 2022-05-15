# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
import math

_logger = logging.getLogger(__name__) # Need for message in console.


class MrpWorkcenterProductivity(models.Model):
    _name = "mrp.workcenter.productivity"
    _inherit = ['mrp.workcenter.productivity']

    #Sorting
    sorting_seq = fields.Integer(string='Sorting Seq.')
    sorting_level = fields.Integer('Sorting Level', default=0)
    sorting_level_seq = fields.Integer('Sorting Level Seq.', default=0)

    #Gantt
    on_gantt = fields.Boolean("Gantt Line Name", default=False)

    duration_gantt = fields.Integer(
        'Gantt Duration', compute='_float_time_convert',
        readonly=True, store=True)

    @api.depends('duration')
    def _float_time_convert(self):
        for record in self:
            val_m = int(math.floor(record.duration)*60)
            val_s = int(round((record.duration % 1) * 60))
            record.duration_gantt = val_m + val_s



    @api.model
    def childs_get(self, ids_field_name, ids, fields):

        test = "OK"
        return test



