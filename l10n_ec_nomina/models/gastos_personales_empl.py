# -*- coding: utf-8 -*-
###################################################################################
#    Definicion del Modelo de los Gastos Personales
#
###################################################################################

from datetime import date, datetime, timedelta
import logging

from openerp import (
    api,
    fields,
    models
)


class GastosPersonales(models.Model):

    _name = 'hr.employee.gastos'
    _description = 'Gastos personales del Empleado'

    employee_id = fields.Many2one(string="Empleado", comodel_name='hr.employee')

    fecha_submission = fields.Date('Fecha', default=date.today())
    #fiscal_year = fields.Char('Ejercicio Fiscal', compute="_get_dates")
    fiscal_year = fields.Char('Ejercicio Fiscal')
    dia_sub = fields.Char('Dia', compute="_get_dates")
    ciudad = fields.Char('Ciudad')
    identification_id = fields.Char('Nº identificación')
    name = fields.Char('Apellidos y Nombres')
    #ruc_empleador = fields.Char('RUC', default='0993143790001')
    company_id = fields.Many2one(string="Empleador", comodel_name='res.company')

    tot_ing_gravados = fields.Float('(+) TOTAL INGRESOS GRAVADOS CON ESTE EMPLEADOR (con el empleador que más ingresos perciba)')
    tot_ing_gravados_other = fields.Float('(+) TOTAL INGRESOS CON OTROS EMPLEADORES (en caso de haberlos)')
    tot_ing_proyectados = fields.Float('(=) TOTAL INGRESOS PROYECTADOS', compute="_get_totals")

    gasto_vivienda = fields.Float('(+) GASTOS DE VIVIENDA') 
    gasto_educacion = fields.Float('(+) GASTOS DE EDUCACIÓN, ARTE Y CULTURA')
    gasto_salud = fields.Float('(+) GASTOS DE SALUD')
    gasto_vestimenta = fields.Float('(+) GASTOS DE VESTIMENTA')
    gasto_alimentacion = fields.Float('(+) GASTOS DE ALIMENTACIÓN')
    tot_gasto_proyectados = fields.Float('(=) TOTAL GASTOS PROYECTADOS ', compute="_get_totals")
    impuesto_a_pagar = fields.Float('VALOR IMPUESTO A LA RENTA', compute="_get_impuesto")
    
    # Funcion para calcular los totales
    @api.depends('tot_ing_gravados',
                 'tot_ing_gravados_other',
                 'gasto_vivienda','gasto_educacion',
                 'gasto_salud',
                 'gasto_vestimenta',
                 'gasto_alimentacion')
    @api.multi
    def _get_totals(self):
        for s in self:
            s.tot_ing_proyectados = s.tot_ing_gravados + s.tot_ing_gravados_other
            s.tot_gasto_proyectados = s.gasto_vivienda + s.gasto_educacion + s.gasto_salud + s.gasto_vestimenta + s.gasto_alimentacion
        

    # Funcion para cargar los campos de fecha formateado
    @api.depends('fecha_submission')
    @api.multi
    def _get_dates(self):
        for s in self:
            s.fiscal_year = '{0:%Y}'.format(s.fecha_submission)
            s.dia_sub = '{0:%d}'.format(s.fecha_submission)


    @api.one
    def _get_impuesto(self):
        pass
        sueldo = 3500.0
        limit = self.env['hr.impuesto.renta'].search([
            ('frac_bas', '>=', sueldo),
            ('exceso_hasta', '<', sueldo)
        ])[0]
        
        self.impuesto_a_pagar = limit.porc_imp_frac_exc*sueldo / 12.0 

