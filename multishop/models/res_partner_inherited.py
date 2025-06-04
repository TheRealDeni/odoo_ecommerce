from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    charge_capacity = fields.Float()
    municipality_ids = fields.Many2many(
        comodel_name='res.municipality',
        relation='partner_municipality_rel',
        column1='partner_id',
        column2='municipality_id'
    )
    is_dealer_user = fields.Boolean(string="Es Dealer", compute="_compute_is_dealer_user", default=False, store=False)

    @api.depends('user_ids.groups_id')
    def _compute_is_dealer_user(self):
        """Determina si el contacto pertenece al grupo Dealers."""
        dealer_group = self.env.ref('multishop.dealers', raise_if_not_found=False)
        for partner in self:
            partner.is_dealer_user = any(user for user in partner.user_ids if dealer_group in user.groups_id)
