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
        default=lambda self: self.env.uid)
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

    def write(self, vals):
        for record in self:
            if any(key in vals for key in ['date_start', 'date_stop']):
                affected = record._get_conflicting_deliveries()
                if affected:
                    record._notify_admin_about_conflict(affected)
        return super().write(vals)

    def unlink(self):
        for record in self:
            name = record.name
            user = record.user_id
            date_start = record.date_start
            date_stop = record.date_stop

            deliveries = self.env['stock.picking'].search([
                ('user_id', '=', user.id),
                ('scheduled_date', '>=', date_start),
                ('scheduled_date', '<=', date_stop)
            ])
            if deliveries:
                admin_group = self.env.ref('base.group_system')
                admins = self.env['res.users'].search([('groups_id', 'in', [admin_group.id])])
                res_model = self.env['ir.model'].sudo().search([('model', '=', 'stock.picking')], limit=1)
                if not res_model:
                    continue

                for delivery in deliveries:
                    for admin in admins:
                        self.env['mail.activity'].sudo().create({
                            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                            'res_model_id': res_model.id,
                            'res_id': delivery.id,
                            'user_id': admin.id,
                            'summary': _('Verificar entrega tras eliminación de disponibilidad'),
                            'note': _(
                                f"""El transportista {user.name} eliminó una disponibilidad que coincidía con la entrega '{delivery.name}'.\n\nRango eliminado: {name}"""
                            ),
                            'date_deadline': fields.Date.today(),
                        })
        return super().unlink()

    def _get_conflicting_deliveries(self):
        picking = self.env['stock.picking']
        conflicting = picking.search([
            ('user_id', '=', self.user_id.id),
            ('scheduled_date', '>=', self.date_start),
            ('scheduled_date', '<=', self.date_stop)
        ])
        return conflicting

    def _notify_admin_about_conflict(self, deliveries):
        admin_group = self.env.ref('base.group_system')
        admins = self.env['res.users'].search([('groups_id', 'in', [admin_group.id])])
        res_model = self.env['ir.model'].sudo().search([('model', '=', 'stock.picking')], limit=1)
        if not res_model:
            return

        for delivery in deliveries:
            for admin in admins:
                self.env['mail.activity'].sudo().create({
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'res_model_id': res_model.id,
                    'res_id': delivery.id,
                    'user_id': admin.id,
                    'summary': _('Verificar entrega tras modificación de disponibilidad'),
                    'note': _(
                        f"""El transportista {self.user_id.name} modificó una disponibilidad que coincide con la entrega '{delivery.name}'.\n\nRango afectado: {self.name}"""
                    ),
                    'date_deadline': fields.Date.today(),
                })
