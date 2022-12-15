# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import re
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    expense_approve = fields.Boolean("Expense Approve", default=False)
    is_user_to_approve = fields.Boolean("Purchase Approve", default=False)

# to fix missing record for mrp module installation
# first insert record in res users using screen for user named: "default"
# insert into ir_model_data (noupdate,"name","module",model,res_id) values (true,'default_user','base','res.users',110);

    def _check_password_rules(self, password):
        self.ensure_one()
        if not password:
            return True
        company_id = self.company_id
        password_regex = [
            '^',
            '(?=.*?[a-z]){' + str(1) + ',}',
            '(?=.*?[A-Z]){' + str(1) + ',}',
            '(?=.*?\\d){' + str(1) + ',}',
            r'(?=.*?[\W_]){' + str(1) + ',}',
            '.{%d,}$' % int(6),
        ]
        if not re.search(''.join(password_regex), password):
            raise ValidationError(self.password_match_message())
        return True

    def write(self, vals):
        is_complex = self.env['ir.config_parameter'].sudo().get_param('aly_complex_password') or False
        if vals.get('password') and is_complex:
            self._check_password_rules(vals['password'])
        return super(ResUsers, self).write(vals)

    def password_match_message(self):
        self.ensure_one()
        company_id = self.company_id
        message = []
        message.append('\n* ' + 'Lowercase letter (At least ' + str(1) + ' character)')
        message.append('\n* ' + 'Uppercase letter (At least ' + str(1) + ' character)')
        message.append('\n* ' + 'Numeric digit (At least ' + str(1) + ' character)')
        message.append('\n* ' + 'Special character (At least ' + str(1) + ' character)')
        message = [_('Must contain the following:')] + message
        message = ['Password must be %d characters or more.' %6] + message
        return '\r'.join(message)
