from odoo import api, fields, models, exceptions

COLOR_RANGE = [('0','brak'), ('1', 'czerwony'), ('2', 'pomarańczowy'), ('3', 'żółty'), ('4', 'błękit'), ('5','ciemny fiolet'),
               ('6', 'różowy'), ('7', 'morski'), ('8', 'granatowy'), ('9', 'Fuksja'), ('10','Zielony'), ('11', 'Purpurowy')]


class User_Color(models.Model):
    _inherit = 'res.users'

    user_color_id = fields.Selection(COLOR_RANGE, string="Kolor użytkownika", required=True)

    @api.onchange('user_color_id')
    def onchange_user_color_id(self):
        copycat = self.env['res.users'].search([('user_color_id', '=', self.user_color_id)])
        if copycat:
            raise exceptions.Warning('Ten kolor został już wybrany przez innego użytkownika.')
