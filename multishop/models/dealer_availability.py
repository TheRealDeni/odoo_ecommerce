from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
from datetime import datetime


class DealerAvailability(models.Model):
    _name = 'dealer.availability'
    _description = 'Disponibilidad del Transportista'

    user_id = fields.Many2one(
        'res.users',
        string='Transportista',
        required=True,
        default=lambda self: self.env.uid
    )
    date_start = fields.Datetime(string="Desde", required=True)
    date_stop = fields.Datetime(string="Hasta", required=True)
    name = fields.Char(string="Descripción", required=False)

    status = fields.Selection([
        ('available', 'Disponible'),
        ('busy', 'Ocupado'),
    ], string="Estado", required=True, default='available')

    @api.constrains('date_start', 'date_stop')
    def _check_date_logic(self):
        for record in self:
            if record.date_start and record.date_stop:
                if record.date_start > record.date_stop:
                    raise ValidationError(_("La fecha de inicio no puede ser posterior a la fecha de fin."))
                if record.date_start < fields.Datetime.now():
                    raise ValidationError(_("La fecha de inicio no puede ser anterior a la fecha actual."))

    @api.onchange('date_start', 'date_stop', 'status')
    def _onchange_name(self):
        for record in self:
            if record.date_start and record.date_stop and record.status:
                if record.status == 'busy':
                    estado = 'Ocupado'
                else:
                    estado = 'Disponible'

                # Convertir a la zona horaria del usuario
                date_start_local = fields.Datetime.context_timestamp(record, record.date_start)
                date_stop_local = fields.Datetime.context_timestamp(record, record.date_stop)

                # Formatear
                date_start_str = date_start_local.strftime('%Y-%m-%d %H:%M')
                date_stop_str = date_stop_local.strftime('%Y-%m-%d %H:%M')

                record.name = f"{estado}: desde {date_start_str} hasta {date_stop_str}"