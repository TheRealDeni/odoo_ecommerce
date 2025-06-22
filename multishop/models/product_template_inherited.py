from odoo import models, api, fields, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        product = super().create(vals)
        # Solo si el creador pertenece al grupo de proveedores
        if self.env.user.has_group('multishop.suppliers'):
            admin_group = self.env.ref('base.group_system')
            admin_users = admin_group.users
            activity_type = self.env.ref('mail.mail_activity_data_todo')
            # Obtener ID del modelo 'product.template' con sudo
            res_model = self.env['ir.model'].sudo().search([('model', '=', 'product.template')], limit=1)
            if not res_model:
                return product
            for admin in admin_users:
                self.env['mail.activity'].sudo().create({
                    'activity_type_id': activity_type.id,
                    'res_model_id': res_model.id,
                    'res_id': product.id,
                    'user_id': admin.id,
                    'summary': _('Revisión de producto nuevo con vista a ser aceptado y publicado'),
                    'note': _('El proveedor %s ha creado el producto "%s".') % (
                        self.env.user.name,
                        product.name
                    ),
                    'date_deadline': fields.Date.today(),
                })
        return product


