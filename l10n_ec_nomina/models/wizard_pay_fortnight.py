# -*- coding: utf-8 -*-
import logging

from openerp import (
    api,
    fields,
    models
)
from odoo import _

from odoo.exceptions import (
    Warning as UserError,
    ValidationError
)
from datetime import date, datetime, time, timedelta
from odoo import _

type_doc = {
    'week': 'Semanal',
    'fortnight': 'Quincenal',
}

class WizardPayFortnight(models.TransientModel):
    _name = "hr.wizard.pay"

    
    diario_id = fields.Many2one(string="Diario", comodel_name='account.journal')
    periodo_desde = fields.Date('Periodo desde', default=date.today().replace(day=1))
    periodo_hasta = fields.Date('Periodo hasta', default=date.today())
    name = fields.Char('name')
    sequence_id = fields.Many2one('ir.sequence', string="Secuencia")
    payment_type = fields.Selection([('week','Semanal'),('fortnight','Quincena')],'Tipo',default='fortnight')
    state = fields.Selection([
         ('init', 'Inicio'),
         ('success', 'Exito')
    ], string='Estado', default='init')

    @api.onchange('diario_id')
    def journal_compute(self):
        ICPSudo = self.env['ir.default'].sudo()
        journal_fortnight = ICPSudo.get("res.config.settings",'journal_fortnight',False,self.env.user.company_id.id)
        self.diario_id = journal_fortnight

    @api.onchange('periodo_desde')
    def onchnge_periodo(self):
        if self.periodo_desde:
            self.periodo_hasta = self.periodo_desde + timedelta(days=14)

    def gen_pay(self):
        ids = self.env.context.get('active_ids', []) or [] #obtiene los ids de los objetos seleccionados
        employee_ids = self.env['hr.employee'].browse(ids) #arreglo que trae los ids seleccionados 
        pay_obj = self.env['hr.payfortnight'] #refrencia tabla de pagos quincenales donde se va a grabar
        payment_id = []
        payment_ids = []
        journal_pay = self.env['ir.default'].sudo().get("res.config.settings",'journal_fortnight_pay',)
        if not journal_pay:
            raise ValidationError(_("Debe configurar un diario de pago de quincena en Configuraciones."))
        obj_payment = self.env['account.batch.payment.payroll']
        payment_transfer_id = []
        check = self.env.ref('l10n_ec_nomina.payment_method_check').id
        transfer = self.env.ref('l10n_ec_nomina.payment_method_transfer').id   

        #referencia a los modelos del asiento donde se va a grabar
        acc_move_obj = self.env['account.move']
        acc_move_line_obj = self.env['account.move.line']

        #se crea el objeto que contiene los campos a grabar en la account_move
        move_data = {
                #'ref': 'Pago quincena correspondiente al periodo desde %s hasta %s' % (str(self.periodo_desde), str(self.periodo_hasta)),
                'journal_id': self.diario_id.id,
                'date': datetime.now(),
                    
                }
        lines=[]


        for e in employee_ids:
        
            amount = e.porcentaje_sueldo * e.contract_id.wage / 100.0
            pay_obj.sudo().create({
                'employee_id': e.id,
                'amount': amount,
                'diario_id': self.diario_id.id,
                'periodo_desde':self.periodo_desde,
                'periodo_hasta': self.periodo_hasta,
                'name': 'Pago %s correspondiente al periodo desde %s hasta %s' % (type_doc[self.payment_type],str(self.periodo_desde), str(self.periodo_hasta)),
                })
            
           
        
            #se crea un objeto tipo tupla para obtener los campos de la account_move_line
            # los argumentos 0,0 los pide ODOO.
            lines.append((0, 0,
                {
                    
                    'ref': 'Pago %s correspondiente al periodo desde %s hasta %s' % (type_doc[self.payment_type],str(self.periodo_desde), str(self.periodo_hasta)),
                    'account_id': self.diario_id.default_credit_account_id.id,
                    'credit': amount,
                    'debit': 0.0
                }))
                    
            lines.append((0,0,
                {
                    
                    'ref': 'Pago %s correspondiente al periodo desde %s hasta %s' % (type_doc[self.payment_type],str(self.periodo_desde), str(self.periodo_hasta)),
                    'account_id': self.diario_id.default_debit_account_id.id,
                    'credit': 0.0,
                    'debit': amount,
                })
            )
            if not e.bank_account_id:
                payment_ids.append((0,0,
                    {
                        'partner_type':'supplier',
                        'partner_id':e.address_home_id.id,
                        'employee_id':e.id,
                        'amount': amount,
                        'payment_date': date.today(),
                        'communication':'Pago %s de %s' %(type_doc[self.payment_type],e.name),
                        'name':'Pago %s de %s' %(type_doc[self.payment_type],e.name),
                        'payment_type': 'outbound',
                        'journal_id':journal_pay,
                        'payment_method_id': check,
                    }
                ))
            else:
                payment_transfer_id.append((0,0,
                    {
                        'partner_type':'supplier',
                        'partner_id':e.address_home_id.id,
                        'employee_id':e.id,
                        'amount': amount,
                        'payment_date': date.today(),
                        'communication':'Pago %s de %s' %(type_doc[self.payment_type],e.name),
                        'name':'Pago %s de %s' %(type_doc[self.payment_type],e.name),
                        'payment_type': 'outbound',
                        'journal_id':journal_pay,
                        'payment_method_id': transfer,
                    }
                ))
    
        move_data.update({'line_ids': lines})#hace un solo objeto que contiene la move y sus lineas
        move = acc_move_obj.create(move_data)# se manda a grabar el objeto move_data
        #move.post() # Para que el asiento quede Conciliado(Publicado).
        if payment_ids:
            payment_id = {
                'batch_type':'outbound',
                'type_pay':'fortnight',
                'date': date.today(),
                'journal_id':journal_pay,
                'name': 'Pago de Quincena',
                'payment_method_id': check,
            }
            payment_id.update({'payment_ids': payment_ids})
            obj_payment.create(payment_id)
        if payment_transfer_id:
            payment_id = {
                'batch_type':'outbound',
                'type_pay':'fortnight',
                'date': date.today(),
                'journal_id':journal_pay,
                'name': 'Pago de Quincena',
                'payment_method_id': transfer,
            }
            payment_id.update({'payment_ids': payment_transfer_id})
            obj_payment.create(payment_id)


        self.env.cr.commit()
        self.state='success'

        return {
             'type': 'ir.actions.act_window',
             'res_model': 'hr.wizard.pay',
             'view_mode': ' form',
             'view_type': ' form',
             'res_id': self.id,
             'views': [(False, 'form')],
             'target': 'new',
         }
        #raise UserError('Nombres %s' %(names, ))
    

    