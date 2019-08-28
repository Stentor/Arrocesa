# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from ast import literal_eval

        
class ResConfigSettings(models.TransientModel):
    _name = 'res.config.settings'
    _inherit = 'res.config.settings'

    modificable_uom = fields.Many2one('uom.uom',string="UdM Modificable")
    
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.default'].sudo()
        modificable_uom = ICPSudo.get("res.config.settings",'modificable_uom',)
        
        res.update(
            modificable_uom = modificable_uom,
            )
        return res


    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.default'].sudo()
        ICPSudo.set("res.config.settings",'modificable_uom',self.modificable_uom.id)
        
        
