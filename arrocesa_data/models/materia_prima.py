from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date

class MateriaPrimaPurchase(models.Model):
    _name = 'arrocesa.materia.prima.purchase'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    product_id = fields.Many2one('product.template', string='Producto')
    balance_id = fields.Many2one('arrocesa_balanzas.weighting', string='Analisis')
    pact_price = fields.Float('Precio Pactado')
    uom_id = fields.Many2one('uom.uom', 'Unidad real')
    uom_mod_id = fields.Many2one('uom.uom', 'Unidad Modificable')
    qty = fields.Float('Cantidad')
    partner_id = fields.Many2one('res.partner', 'Proveedor')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Realizada')
    ], default='draft', string='Estado',track_visibility="onchange")

    @api.multi
    def make_purchase(self):
        for s in self:
            coeff = s.pact_price / s.product_id.price_magap
            s.uom_mod_id.write({
                'factor': coeff * s.uom_id.factor
            })

            data = {
                    'partner_id': s.partner_id.id,
                    'name': s.env['ir.sequence'].next_by_code('purchase.order'),
                    'order_line': [(0,0,{
                        'name': s.product_id.name,
                        'date_planned': date.today(),
                        'product_id': s.product_id.id,
                        'product_qty': s.qty*coeff,
                        'product_uom': s.uom_mod_id.id,
                        'price_unit': s.product_id.price_magap
                    })]
                }
           
            s.write({
                'state': 'done'
            })
            purchase=s.env['purchase.order'].create(
                data
            )
            purchase.button_confirm()

        self.env.cr.commit()



class MateriaPrima(models.Model):
    _inherit = 'product.template'

    price_magap = fields.Float('Precio Magap')
    is_prime_material = fields.Boolean('Materia Prima')