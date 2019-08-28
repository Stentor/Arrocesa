from odoo import api, fields, models, _
from odoo.addons.uom.models.uom_uom import UoM as UoMBase 
from odoo.exceptions import UserError

class UoM(models.Model):
    _inherit = 'uom.uom'

    def write(self, values):
        res = self.env['res.config.settings'].sudo(1).search([], limit=1, order="id desc")
        mod_uom = res.modificable_uom.id

        # Users can not update the factor if open stock moves are based on it, unless the unit is modificable (MAGAP)
        if 'factor' in values or 'factor_inv' in values or 'category_id' in values:
            changed = self.filtered(
                lambda u: any(u[f] != values[f] if f in values else False
                              for f in {'factor', 'factor_inv'})) + self.filtered(
                lambda u: any(u[f].id != int(values[f]) if f in values else False
                              for f in {'category_id'}))
            if changed and self.id != mod_uom:
                stock_move_lines = self.env['stock.move.line'].search_count([
                    ('product_uom_id.category_id', 'in', changed.mapped('category_id.id')),
                    ('state', '!=', 'cancel'),
                ])

                if stock_move_lines:
                    raise UserError(_(
                        "You cannot change the ratio of this unit of mesure as some"
                        " products with this UoM have already been moved or are "
                        "currently reserved."
                    ))

        # Doing the same thing as the base UoM
        if 'factor_inv' in values:
            factor_inv = values.pop('factor_inv')
            values['factor'] = factor_inv and (1.0 / factor_inv) or 0.0

        # As we completely skip the inheritance tree and call the original write
        return UoMBase.write(self, values)
