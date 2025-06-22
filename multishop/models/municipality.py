from odoo import models, fields


class Municipality(models.Model):
    _name = 'res.municipality'
    _description = 'Municipality'

    name = fields.Char(string='Municipio', required=True)
    postal_code = fields.Char(string='CP', required=True)

