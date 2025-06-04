from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestStockPicking(TransactionCase):

    def setUp(self):
        super().setUp()

        # Crear un tipo de operación válido para el picking
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
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })

        # Crear municipios y asociar al transportista
        self.municipality = self.env['res.municipality'].create({
            'name': 'Municipio Test',
            'postal_code': '12345',
        })
        self.partner.write({'municipality_ids': [(4, self.municipality.id)]})

        # Crear los zip prefix necesarios
        self.zip_prefix = self.env['delivery.zip.prefix'].create({
            'name': '12345',
        })

        # Crear un carrier y asociar el zip prefix
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Carrier Test',
            'product_id': self.env['product.product'].create({
                'name': 'Producto Test',
                'type': 'service',
                'sale_ok': False,
            }).id,
        })

        # Asocia el zip prefix con el carrier
        self.carrier.write({'zip_prefix_ids': [(4, self.zip_prefix.id)]})

        # Crear un stock.picking con ubicaciones definidas, picking_type_id y el carrier
        self.picking = self.env['stock.picking'].create({
            'user_id': self.user.id,  # Asociar al transportista
            'carrier_id': self.carrier.id,  # Asociar el carrier
            'location_id': self.location_source.id,
            'location_dest_id': self.location_dest.id,
            'move_type': 'direct',
            'picking_type_id': self.picking_type.id,  # Agregar el tipo de picking
        })

    def test_transport_zones_valid(self):
        """Prueba que el transportista tiene cobertura en la zona del método de envío"""
        try:
            self.picking._check_transport_zones()  # No debería lanzar excepción
        except ValidationError:
            self.fail("Se lanzó ValidationError cuando no debería. El transportista tiene cobertura en la zona.")

    def test_transport_zones_invalid(self):
        """Prueba que el transportista no tiene cobertura en la zona del método de envío"""
        # Cambiar la zona del transportista para que no coincida
        self.municipality.write({'postal_code': '54321'})  # Cambiar la zona del transportista

        with self.assertRaises(ValidationError):
            self.picking._check_transport_zones()  # Debería lanzar una excepción
