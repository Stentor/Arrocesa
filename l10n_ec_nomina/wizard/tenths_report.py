# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import date
import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

class tenths_reports(models.Model):
    _name = "report.tenths"
    _description = " This object is for print the thirteenth and fourteenth salary"

    def _calcule_period(self):
        year = date.today().year 
        result = []
        for line in range(5):
            result.append((year,year))
            year -= 1
        return result

    name = fields.Selection([('ProvDec13','Décimo Tercero'),
                            ('ProvDec14','Décimo Cuarto'),
                            ('utilies','Utilidades')], string="Provision", default="ProvDec13")
    period = fields.Selection(_calcule_period, string="Periodo")
    region_id = fields.Selection([('cost','Costa'),
                                ('sierra','Sierra'),
                                ('amazon','Oriente'),
                                ('island','Galapagos')],string="Region",default="cost")
    date_from = fields.Date('Fecha Inicio', compute="_compute_date_range")
    date_to = fields.Date('Fecha Fin', compute="_compute_date_range")
    pay_id = fields.Boolean('Realizar Pago', default=False)
    state = fields.Selection([('draft','Borrador'),('done','Realizado')],'Estado',default='draft')

    @api.depends('name','region_id','period')
    def _compute_date_range(self):
        if self.period:
            date_c = date(int(self.period)+1,2,28)
            period_prev = int(self.period)-1
            period_next = int(self.period)+1
            period = int(self.period)
            if self.name == 'ProvDec13':
                self.date_from = date(period_prev,12,1)
                self.date_to = date(period,11,30)
            elif self.name == 'utilies':
                self.date_from = date(period,1,1)
                self.date_to = date(period,12,31)
            elif self.region_id in ('cost','island'):
                self.date_from = date(period,3,1)
                date_end = date_c.replace(day=1)+relativedelta(months=1)+datetime.timedelta(days=-1)
                self.date_to = date_end
            else:
                self.date_from = date(period,8,1)
                self.date_to = date(period_next,7,31)

    @api.model
    def range_month(self):
        if self.name == 'ProvDec13':
            return [12,1,2,3,4,5,6,7,8,9,10,11]
        elif self.name == 'utilies':
            return [1,2,3,4,5,6,7,8,9,10,11,12]
        elif self.region_id in ('cost','island'):
            return [3,4,5,6,7,8,9,10,11,12,1,2]
        else:
            return [8,9,10,11,12,1,2,3,4,5,6,7]

    @api.multi
    def payslip_in_period(self,date_from,employee,name=""):
        obj_paylip = self.env['hr.payslip']
        payslip = obj_paylip.search([('date_from','<=',date_from),
                                    ('date_to','>=',date_from),
                                    ('employee_id','=',employee.id),
                                    ('state','=','paid')])
        value = 0.00
        if not name:
            name = self.name
        for line in payslip.line_ids:
            if line.code in name:
                value = line.total
                break
        return value

    @api.multi
    def period_range(self,year,month):
        date_from = date(int(year),int(month),1)
        return date_from
    
    @api.model
    def contract_active(self):
        obj_contract = self.env['hr.contract']
        contract_ids = obj_contract.search([('state','=','open')])
        return contract_ids

    @api.multi
    def print_tenth(self):
        self.state = 'done'
        self.generate_paid()
        if self.name == 'utilies':
            return self.env.ref('l10n_ec_nomina.report_utilies').report_action(self)
        return self.env.ref('l10n_ec_nomina.report_tenths').report_action(self)
    
    @api.model
    def month_in_letter(self):
        result = [
            'ENERO',
            'FEBRERO',
            'MARZO',
            'ABRIL',
            'MAYO',
            'JUNIO',
            'JULIO',
            'AGOSTO',
            'SEPTIEMBRE',
            'OCTUBRE',
            'NOVIEMBRE',
            'DICIEMBRE'
        ]
        return result

    @api.multi
    def total_tenths(self, employee, name=""):
        if not name:
            name = self.name
        month_ids = self.range_month()
        year = int(self.period)
        value = 0.00
        for month in month_ids:
            if name == 'ProvDec13' and str(month) == '12':
                date = self.period_range(str(year - 1),month)
            elif name == 'ProvDec14' and int(month) < 3 and self.region_id in ('cost','island'):
                date = self.period_range(str(year + 1),month)
            elif name == 'ProvDec14' and int(month) < 7 and self.region_id in ('sierra','amazon'):
                date = self.period_range(str(year + 1),month)
            else:
                date = self.period_range(str(year),month)
            value += self.payslip_in_period(date,employee,name)

        return round(value,2)
    
    @api.multi
    def family_count(self,employee):
        count = 0
        for line in employee.fam_ids:
            count += 1
        return count   

    @api.multi
    def generate_paid(self):
        if self.pay_id:
            if self.name == 'ProvDec13':
                journal_id = self.env['ir.default'].sudo().get("res.config.settings",'journal_xiii',False,self.env.user.company_id.id)
            else:
                journal_id = self.env['ir.default'].sudo().get("res.config.settings",'journal_xiv',False,self.env.user.company_id.id)
            # rule_id = self.env['hr.salary.rule'].search([('code','=',self.name)])
            # journal_id = self.env['account.journal'].search([('code','=',code)])
            check = self.env.ref('l10n_ec_nomina.payment_method_check').id
            transfer = self.env.ref('l10n_ec_nomina.payment_method_transfer').id
            payment_ids = []
            payment_transfer_id = []
            lines=[]
            name = {
                'ProvDec13':' Pago Decimo Tercer Sueldo ',
                'ProvDec14':' Pago Decimo Cuarto Sueldo ',
                'utilies':' Pago de Utilidades ',
            }
            if not journal_id:
                raise ValidationError(_("Debe configurar el diario de %s en Configuraciones." % name[self.name]))
            obj_payment = self.env['account.batch.payment.payroll']
            for contract in self.contract_active():
                for line in contract.struct_id.rule_ids:
                    if line.code in self.name:
                        rule_id = line
                amount = self.total_tenths(contract.employee_id)
                if amount > 0: 
                    if not contract.employee_id.bank_account_id:
                        payment_ids.append((0,0,
                            {
                                'partner_type':'supplier',
                                'partner_id':contract.employee_id.address_home_id.id,
                                'employee_id':contract.employee_id.id,
                                'amount': amount,
                                'payment_date': date.today(),
                                'communication':name[self.name] + contract.employee_id.name,
                                'name':name[self.name] + contract.employee_id.name,
                                'payment_type': 'outbound',
                                'journal_id':journal_id,
                                'payment_method_id': check,
                            }
                        ))
                    else:
                        payment_transfer_id.append((0,0,
                            {
                                'partner_type':'supplier',
                                'partner_id':contract.employee_id.address_home_id.id,
                                'employee_id':contract.employee_id.id,
                                'amount': amount,
                                'payment_date': date.today(),
                                'communication':name[self.name] + contract.employee_id.name,
                                'name':name[self.name] + contract.employee_id.name,
                                'payment_type': 'outbound',
                                'journal_id':journal_id,
                                'payment_method_id': transfer,
                            }
                        ))
                    lines.append((0, 0,
                    {
                        
                        'ref': name[self.name] + str(self.period),
                        'account_id': rule_id.account_credit.id,
                        'credit': amount,
                        'debit': 0.0
                    }))
                            
                    lines.append((0,0,
                        {
                            
                            'ref': name[self.name] + str(self.period),
                            'account_id': rule_id.account_debit.id,
                            'credit': 0.0,
                            'debit': amount,
                        }))
            if payment_ids:
                payment_id = {
                    'batch_type':'outbound',
                    'date': date.today(),
                    'journal_id':journal_id,
                    'name': name[self.name] + str(self.period),
                    'payment_method_id': check,
                }
                payment_id.update({'payment_ids': payment_ids})
                obj_payment.create(payment_id)
            if payment_transfer_id:
                payment_id = {
                    'batch_type':'outbound',
                    'date': date.today(),
                    'journal_id':journal_id,
                    'name': name[self.name] + str(self.period),
                    'payment_method_id': transfer,
                }
                payment_id.update({'payment_ids': payment_transfer_id})
                obj_payment.create(payment_id)
                
            acc_move_obj = self.env['account.move']
            move_data = {
                    'journal_id': journal_id,
                    'date': date.today(),
                        
                    }
            move_data.update({'line_ids': lines})
            acc_move_obj.create(move_data)
            self.env.cr.commit()
