# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import re
from odoo.exceptions import ValidationError

try:
    import zxcvbn

    zxcvbn.feedback._ = _
except ImportError:
    er = 'Could not import zxcvbn. Please make sure this library is available in your environment.'


class ResUsers(models.Model):
    _inherit = 'res.users'

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

        estimation = self.get_estimation(password)
        if estimation["score"] < company_id.password_estimate:
            raise ValidationError(estimation["feedback"]["warning"])

        return True

    def write(self, vals):
        if vals.get('password'):
            self._check_password_rules(vals['password'])
        return super(ResUsers, self).write(vals)

    @api.model
    def get_estimation(self, password):
        return zxcvbn.zxcvbn(password)

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
