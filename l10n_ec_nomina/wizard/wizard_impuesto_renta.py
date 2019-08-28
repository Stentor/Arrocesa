# -*- coding: utf-8 -*-
import logging

from openerp import (
    api,
    fields,
    models
)

from odoo.exceptions import (
    Warning as UserError,
    ValidationError
)
from datetime import date, datetime, time

class WizardImpuestoRenta(models.TransientModel):
    _name = "hr.wizard.impuesto.renta"

    name = fields.Many2one(string="Empleado", comodel_name='hr.employee')
    fecha = fields.Date('Fecha Entrega', default=date.today())
    anio= fields.Char('Ejercicio Fiscal')

    util = fields.Float('PARTICIPACIÓN UTILIDADES (305)')
    ing_grav_otroempl = fields.Float('INGRESOS GRAV.CON OTROS EMPLEADORES (307)')
    otros_ing = fields.Float('OTROS ING. QUE NO CONSTITUYEN RENTA GRAVADA (317)')
    apor_iess = fields.Float('APOR. IESS OTROS EMPLEADORES (353)')
    imp_ret_asum = fields.Float('IMP. RET. Y ASUM. x OTROS EMPLEADORES (403)')
    exo_discapacidad = fields.Float('(-) EXONERACIÓN POR DISCAPACIDAD (371)')
    exo_ter_edad = fields.Float('(-) EXONERACIÓN POR TERCERA EDAD (373)')
    imp_asum_estempl = fields.Float('IMP. A LA RENTA ASUMIDO POR ESTE EMPLEADOR (381-405)')
    

    @api.multi
    def print_107(self):
        return self.env.ref('l10n_ec_nomina.report_impuesto_renta').report_action(self)

    # Función para obtener la suma de los pagos por salarios en un rango de fechas
    def calcule_sayings(self, salaryrulecode):
        
        if not isinstance(salaryrulecode, list):
            salaryrulecode = [salaryrulecode]
        
        obj_payslip = self.env['hr.payslip']
        value = 0.00
        
        date_init = str(self.anio) + '-01-01'
        date_end = str(self.anio) + '-12-31'

        payslip_ids = obj_payslip.search([('employee_id','=',self.name.id),
                                        ('date_from','>=',date_init),
                                        ('date_to','<=',date_end),
                                        ('state','=','paid')])
        for payslip in payslip_ids:
            for lines in payslip.line_ids:
                if lines.code in salaryrulecode:
                    value += lines.total
        
        if value < 0:
            value = value * -1

        return value

    # Función para obtener los valores de los gastos personales en un rango de fechas
    def calcule_personal_expenses(self):
        obj_expenses = self.env['hr.employee.gastos']
              
        expenses_id = obj_expenses.search([('employee_id','=',self.name.id),
                                        ('fiscal_year','>=',self.anio)])
        if len(expenses_id)>0:
            expenses_id=expenses_id[0]
            
            result = {
            'vivienda': expenses_id.gasto_vivienda,
            'salud': expenses_id.gasto_salud,
            'educacion': expenses_id.gasto_educacion,
            'alimentacion': expenses_id.gasto_alimentacion,
            'vestimenta': expenses_id.gasto_vestimenta
        } 
        else:
            #raise ValidationError('No existe datos de gastos personales para el empleado seleccionado')
          
            result = {
                'vivienda': 0.00,
                'salud': 0.00,
                'educacion': 0.00,
                'alimentacion': 0.00,
                'vestimenta': 0.00
            }                
        
        
        return result

    def tax_code(self):
        gastos = self.calcule_personal_expenses()
        val301 = self.calcule_sayings('BASIC')
        val303 = self.calcule_sayings(['Comi','Bonif','HorExt','HorSupl','Movil'])
        val305 = self.util
        val307 = self.ing_grav_otroempl
        val311 = self.calcule_sayings(['ProvDec13','Dec13Men'])
        val313 = self.calcule_sayings(['ProvDec14','Dec14Men'])
        val315 = self.calcule_sayings(['FonResvM','FonResv']) 
        val317 = self.otros_ing   
        val351 = self.calcule_sayings('ApIESSPer')
        val353 = self.apor_iess
        val361 = gastos['vivienda']
        val363 = gastos['salud']
        val365 = gastos['educacion']
        val367 = gastos['alimentacion']
        val369 = gastos['vestimenta']
        val371 = self.exo_discapacidad
        val373 = self.exo_ter_edad
        val381_405 = self.imp_asum_estempl
        val401 = self.check_tax((val301+val303)-(val361+val363+val365+val367+val369+val351))
        val403 = self.imp_ret_asum
        val407 = self.calcule_sayings('ImpRent')
        
        
        result = {
            '301': val301,
            '303': val303,
            '305': val305,
            '307': val307,
            '311': val311,
            '313': val313,
            '315': val315,
            '317': val317,
            '351': val351,
            '353': val353,
            '361': val361,
            '363': val363,
            '365': val365,
            '367': val367,
            '369': val369,
            '371': val371,
            '373': val373,
            '381-405': val381_405,
            '399': val303+val301+val305+val307-val351-val353-val361-val363-val365-val367-val369-val371-val373+val381_405,
            '401': val401,
            '403': val403,
            '407': val407,
            '349': val303+val301+val305+val381_405

        }

        for k,v in result.items():
            result[k] = '{:.2f}'.format(v)

        return result



    # Función para obtener el monto real de impuesto a la renta
    def check_tax(self, valor):
        obj_expenses = self.env['hr.impuesto.renta']
              
        expenses_id = obj_expenses.search([('frac_bas','<=',valor),('exceso_hasta','>=',valor)])
        
        #new_base = expenses_id.imp_frac_bas
        #new_base = ((valor - expenses_id.frac_bas) * (expenses_id.porc_imp_frac_exc / 100) - expenses_id.imp_frac_bas
        new_base = valor - expenses_id.frac_bas
        new_base = (new_base * (expenses_id.porc_imp_frac_exc / 100)) + expenses_id.imp_frac_bas


        return new_base



