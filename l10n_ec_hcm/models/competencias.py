# -*- coding: utf-8 -*-

from odoo import models, fields, api
from openerp.exceptions import Warning as UserError

class hcm_competencias(models.Model):
    _name = 'hcm.competencias'

    codigo = fields.Char('Código', default = False)
    nombre = fields.Char('Nombre', default = False)
    descripcion = fields.Char('Descripción', default = False)
    nivel1 = fields.Char('nivel1', default = False)
    nivel2 = fields.Char('nivel2', default = False)
    nivel3 = fields.Char('nivel3', default = False)
    nivel4 = fields.Char('nivel4', default = False)
    nivel5 = fields.Char('nivel5', default = False)
    nivel6 = fields.Char('nivel6', default = False)
    

    # @api.depends('value')
    # def _value_pc(self):
    #     self.value2 = float(self.value) / 100