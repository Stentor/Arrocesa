# -*- coding: utf-8 -*-
import logging

from openerp import (
    api,
    fields,
    models
)
from datetime import date

class PayFortnight(models.Model):
    _name = "hr.payfortnight"

    #employee_id = fields.Many2one('hr.employee', string="Empleado")
    name= fields.Char('Nombre')
    employee_id = fields.Many2one(string="Empleado", comodel_name='hr.employee')
    #diario_id = fields.Many2one('account.journal', string="Diario")
    diario_id = fields.Many2one(string="Diario", comodel_name='account.journal')
    amount = fields.Float('Monto')
    fecha_pago = fields.Date('Fecha Pago', default=date.today())
    periodo_desde = fields.Date('Periodo desde', default=date.today())
    periodo_hasta = fields.Date('Periodo hasta', default=date.today())
    #usuario
    
    # @api.model
    # def create(self, values):
    #     # Override the original create function for the res.partner model
    #     record = super(PayFortnight, self).create(values)
    #     #record.name = "PGQ/%s" % (self.env['ir.sequence'].next_by_code('PAGO15'), )
    #     return record

    #Ejemplo de funcion calculada en la vista
    #@api.depends('cargo_iess')
    #@api.onchange('cargo_iess')
    #@api.multi
    #def _get_dummy(self):
    #    for s in self:
    #        s.dummy = s.salario_ref / 12.0
            #s.salario_ref = s.cargo_iess.value

    
    