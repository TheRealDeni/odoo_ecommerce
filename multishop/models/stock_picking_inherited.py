from odoo import _, models, fields, api
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_dealer_user = fields.Boolean(default=False, store=False, compute='_compute_is_dealer_user')

    @api.depends()
    def _compute_is_dealer_user(self):
        for record in self:
            record.is_dealer_user = self.env.user.has_group('multishop.dealers')

    @api.constrains('user_id', 'weight')
    def _check_transport_capacity(self):
        """Valida que el peso del envío no exceda la capacidad de carga del transportista."""
        for picking in self:
            if picking.user_id and picking.weight:
                # Obtener la capacidad de carga del transportista asignado
                charge_capacity = picking.user_id.partner_id.charge_capacity
                if charge_capacity and picking.weight > charge_capacity:
                    raise ValidationError(_(
                        "El peso del envío ({:.2f}) excede la capacidad de carga del transportista ({:.2f})."
                    ).format(picking.weight, charge_capacity))

    @api.constrains('user_id', 'carrier_id')
    def _check_transport_zones(self):
        """Valida que el transportista asignado tenga cobertura en las zonas del método de envío."""
        for picking in self:
            if picking.user_id and picking.carrier_id:
                # Obtener códigos postales del transportista
                covered_zips = picking.user_id.partner_id.municipality_ids.mapped('postal_code')
                # Obtener códigos postales del método de envío
                carrier_zips = picking.carrier_id.zip_prefix_ids.mapped('name')
                # Validar intersección
                if not set(covered_zips) & set(carrier_zips):
                    raise ValidationError(_(
                        "El transportista seleccionado no tiene cobertura en las zonas permitidas por el método de envío."
                    ))

    @api.constrains('user_id', 'scheduled_date')
    def _check_dealer_availability_range(self):
        """Valida que la fecha programada esté dentro de un intervalo de disponibilidad del transportista."""
        for picking in self:
            if picking.user_id and picking.scheduled_date:
                availabilities = self.env['dealer.availability'].search([
                    ('user_id', '=', picking.user_id.id)
                ])
                # Comprobar si existe al menos un intervalo válido
                if not any(
                        availability.date_start <= picking.scheduled_date <= availability.date_stop
                        for availability in availabilities
                ):
                    raise ValidationError(_(
                        "La fecha programada del envío (%s) no coincide con ninguna disponibilidad del transportista seleccionado."
                    ) % picking.scheduled_date.strftime('%Y-%m-%d %H:%M:%S'))
