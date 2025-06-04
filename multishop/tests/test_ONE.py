from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestStockPicking(TransactionCase):

    def setUp(self):
        super().setUp()

        # Obtener un tipo de operación válido para el picking
        self.picking_type = self.env['stock.picking.type'].search([], limit=1)
        if not self.picking_type:
            self.picking_type = self.env['stock.picking.type'].create({
                'name': 'Test Picking Type',
                'code': 'internal',
                'sequence_code': 'TEST',
                'warehouse_id': self.env['stock.warehouse'].search([], limit=1).id,
            })

        # Crear ubicaciones para el stock.picking
        self.location_source = self.env['stock.location'].create({
            'name': 'Ubicación Origen Test',
            'usage': 'internal'
        })

        self.location_dest = self.env['stock.location'].create({
            'name': 'Ubicación Destino Test',
            'usage': 'internal'
        })

        # Crear un transportista con capacidad de carga de 50 kg
        self.partner = self.env['res.partner'].create({
            'name': 'Transportista Carlos',
            'is_dealer_user': True,
            'charge_capacity': 50.0,
        })

        # Crear un usuario vinculado al transportista
        self.user = self.env['res.users'].create({
            'name': 'Usuario Transportista',
            'partner_id': self.partner.id,
            'login': 'transportista',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
        })

        # Crear un stock.picking con ubicaciones definidas y picking_type_id
        self.picking = self.env['stock.picking'].create({
            'user_id': self.user.id,
            'weight': 40.0,
            'location_id': self.location_source.id,
            'location_dest_id': self.location_dest.id,
            'move_type': 'direct',
            'picking_type_id': self.picking_type.id,  # Agregado para evitar error
        })

    def test_transport_capacity_valid(self):
        """Prueba que el transportista puede manejar el peso permitido"""
        self.picking.write({'weight': 45.0})  # Aún dentro del límite
        try:
            self.picking._check_transport_capacity()  # No debería lanzar excepción
        except ValidationError:
            self.fail("Se lanzó ValidationError cuando no debería.")

    def test_transport_capacity_exceeded(self):
        """Prueba que el peso del envío no puede exceder la capacidad de carga"""
        with self.assertRaises(ValidationError):
            self.picking.write({'weight': 60.0})  # Esto activará la validación
