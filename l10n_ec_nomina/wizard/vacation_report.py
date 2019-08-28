# -*- coding:utf-8 -*-

from odoo import api, models, fields,_
from datetime import date
import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning, ValidationError
class reportVacation(models.Model):
    _name = 'report.liq_vacation'
    _description = 'Reporte de liquidacion de vacaciones'

    def compute_employee(self):
        employee = 0
        employee_ids = []
        day = []
        contract_ids = self.env['hr.contract'].search(['|',('date_end','=',None),('date_start','<',date.today()),('state','not in',('draft','cancel'))], order="employee_id,date_start asc")
        for contract in contract_ids:
            if employee != contract.employee_id.id:
                employee = contract.employee_id.id
                year = 0
            else:
                if (contract.date_start - date_end).days > 1:
                    year = 0
            if contract.date_end:
                date_end = contract.date_end
            else:
                date_end = date.today()
            year += (date_end - contract.date_start).days
            day.append(year)
            if year >= 365:
                employee_ids.append(contract.employee_id.id)
        return [('id','in',employee_ids)]

    name = fields.Many2one('hr.employee',string='Empleado', domain=compute_employee, required=True)
    date_start = fields.Date('Fecha Inicio', required=True)
    date_end = fields.Date('Fecha Corte', required=True, default = date.today())
    contract_id = fields.Many2one('hr.contract',string='Contrato')
    pay_id = fields.Boolean('Realizar Pago', default=False)
    state = fields.Selection([('draft','Borrador'),('done','Realizado')],'Estado',default='draft')


    @api.onchange('date_start','name','date_end')
    def onchange_date_start(self):
        if self.name and self.date_start:
            obj_contract = self.env['hr.contract']
            contract = obj_contract.search([('employee_id','=',self.name.id),('active','=',True)])
            if contract:
                self.contract_id = contract.id
                self.date_start = str(self.date_start.year) + str(contract.date_start)[4:10]
                date_end = date(self.date_start.year+1,contract.date_start.month,contract.date_start.day)
                if date.today() < date_end:
                    self.date_end = date.today()
                else:
                    self.date_end = date_end


    @api.multi
    def calcule_total_vacation(self,payslip_id):
        amount = 0 
        for payslip in payslip_id:
            if payslip.date_to >= self.date_start and payslip.date_from <= self.date_end and payslip.state == 'paid':
                for line in payslip.line_ids:
                    if line.code in 'Vaca':
                        amount += line.amount
        return amount

    @api.multi
    def print_liquidation(self):
        self.state = 'done'
        self.generate_paid()
        return self.env.ref('l10n_ec_nomina.hr_vacations_report').report_action(self)

    @api.multi
    def calcule_days(self):
        if self.date_start.month <= self.date_end.month:
            year = str(self.date_end.year)
        else:
            year = str(self.date_end.year - 1)

        date_init = date(int(year),self.date_start.month,self.date_start.day)
        date_end = self.date_end
        days = int((date_end - date_init).days * (15/365))
        return days

    @api.multi
    def generate_paid(self):
        if self.pay_id:
            payment_ids = []
            obj_payment = self.env['account.batch.payment.payroll']
            rule_id = self.env['hr.salary.rule'].search([('code','=','Vaca')])
            amount = 0.00
            # journal_id = self.env['account.journal'].search([('code','=','vctn')])
            journal_id = self.env['ir.default'].sudo().get("res.config.settings",'journal_vacation',False,self.env.user.company_id.id)
            if not journal_id:
                raise ValidationError(_("Debe configurar un diario de pago de vacaciones en Configuraciones."))
            for payroll in self.name.slip_ids:
                if payroll.date_to >= self.date_start and payroll.date_from <= self.date_end and payroll.state == 'paid':
                    amount += self.calcule_total_vacation(payroll)
            if not self.name.bank_account_id:
                journal = self.env.ref('l10n_ec_nomina.payment_method_check').id
            else:
                journal = self.env.ref('l10n_ec_nomina.payment_method_transfer').id
            payment_ids.append((0,0,
                    {
                        'partner_type':'supplier',
                        'partner_id':self.name.address_home_id.id,
                        'employee_id':self.name.id,
                        'amount': amount,
                        'payment_date': date.today(),
                        'communication':'Pago de Vacaciones ' + self.name.name,
                        'name':'Pago de Vacaciones ' + self.name.name,
                        'payment_type': 'outbound',
                        'journal_id':journal_id,
                        'payment_method_id': journal,
                    }
                ))
            payment_id = {
                    'batch_type':'outbound',
                    'date': date.today(),
                    'journal_id':journal_id,
                    'name': 'Pago de Vacaciones ' + self.name.name,
                    'payment_method_id': journal,
                }
            payment_id.update({'payment_ids': payment_ids})
            obj_payment.create(payment_id)
            lines =[]
            lines.append((0, 0,
                {
                    
                    'ref': 'Liquidacion de vacaciones ' + self.name.name,
                    'account_id': rule_id.account_credit.id,
                    # 'partner_id': self.name.address_home_id.id,
                    'credit': amount,
                    'debit': 0.0
                }))
                    
            lines.append((0,0,
                {
                    
                    'ref': 'Liquidacion de vacaciones ' + self.name.name,
                    'account_id': journal_id.default_debit_account_id.id,
                    # 'partner_id': rule_id.account_debit.id,
                    'credit': 0.0,
                    'debit': amount,
                }))
            acc_move_obj = self.env['account.move']
            move_data = {
                    'journal_id': journal_id,
                    'date': date.today(),
                        
                    }
            move_data.update({'line_ids': lines})
            acc_move_obj.create(move_data)
            self.env.cr.commit()


class liquidationSettlement(models.Model):
    _name = 'report.liq_settlement'
    _description = 'Reporte de liquidacion de finiquito'

    name = fields.Many2one('hr.employee', string='Empleado', required=True)
    date_start = fields.Date('Fecha de Ingreso')
    date_end = fields.Date('Fecha de Salida')
    contract_id = fields.Many2one('hr.contract', string='Contrato')
    settlement_id = fields.Many2one('hr.settlement.type',string='Motivo')
    payslip_id = fields.Many2one('hr.payslip',string='Rol de Pago')
    amount = fields.Float('Indemnizacion')
    region_id = fields.Selection([('cost','Costa'),
                                ('sierra','Sierra'),
                                ('amazon','Oriente'),
                                ('island','Galapagos')],string="Region",default="cost")
    pay_id = fields.Boolean('Realizar Pago', default=False)
    state = fields.Selection([('draft','Borrador'),('done','Realizado')],'Estado',default='draft')

    @api.onchange('name')
    def _onchange_settlement(self):
        if self.name:
            obj_contract = self.env['hr.contract']
            contract = obj_contract.search([('employee_id','=',self.name.id),('state','!=','draft')], order='id asc', limit=1)
            if  contract:
                self.date_start = contract.date_start
            end_contract = obj_contract.search([('employee_id','=',self.name.id),('state','!=','draft')], order='id desc', limit=1)
            if end_contract:
                self.contract_id = end_contract.id
                if end_contract.date_end:
                    self.date_end = end_contract.date_end
                else:
                    self.date_end = date.today()
                    self.contract_id.date_end = date.today() 

    @api.multi
    def print_settlement(self):
        obj_payslip = self.env['hr.payslip']
        date_c = self.date_end
        date_end = date_c.replace(day=1)+relativedelta(months=1)+datetime.timedelta(days=-1)
        date_init = date_c.replace(day=1)
        payslip = obj_payslip.search([('employee_id','=',self.name.id),('date_from','=',date_init),
                ('date_to','=',date_end),('state','=','paid')])#a la espera de verificacion de estado de creacion
        if not payslip:
            self.contract_id.date_end = date_c
            payslip = self.create_payslip_employee(date_init,date_end,self.date_end)
        payslip.compute_sheet()
        self.payslip_id = payslip.id
        data = self.calcule_total_expenses()
        self.state = 'done'
        self.generate_paid()
        self.contract_id.state = 'close'
        return self.env.ref('l10n_ec_nomina.report_hr_settlemet').report_action(self)

    @api.multi
    def create_payslip_employee(self,d1,d2,d3):
        obj_payslip = self.env['hr.payslip']
        if d2.day == '31' and d3.day != '31':
            day = d3.day + 1
        else:
            day = d3.day
        dct = {
            'employee_id': self.name.id,
            'contract_id': self.contract_id.id,
            'date_from': d1,
            'date_to': d2,
            'state': 'paid',#hay que verificar en que estado se queda y si es que hay que eliminarlo
            'name': 'Nomina de finiquito de %s' %(self.name.name),
            'struct_id': self.contract_id.struct_id.id,
            'worked_days_line_ids':[(0,0,{
                'name':'Dias de trabajo pagados al 100%',
                'code':'WORK100',
                'number_of_days': day,
                'number_of_hours': day * 8,
                'contract_id':self.contract_id.id,
            })],
            'input_line_ids':[(0,0,{
                'name':'Indemnizacion de mutuo acuerdo',
                'amount': self.amount,
                'code':'Bonif',
                'contract_id': self.contract_id.id,
            })],
        }
        payslip = obj_payslip.create(dct)
        #payslip.onchange_employee()
        return payslip
    

    @api.multi
    def calcule_total_expenses(self):
        return sum([l.total for l in self.payslip_id.line_ids if l.category_id.name == 'Descuentos'])

    @api.multi
    def calcule_XIV_date(self):
        anio = int(self.date_end.strftime('%Y'))
        if self.region_id in ('cost','island'):
            if self.date_end.month > 2:
                date_init = date(anio,3,1)
                date_end = self.date_end.replace(day=1)+relativedelta(months=1)+datetime.timedelta(days=-1)
            else:
                
                date_init = date(anio-1,3,1)
                if anio%4 == 0 and anio%100 != 0 or anio%400 == 0:
                    date_end = date(anio,2,29)
                else:
                    date_end = date(anio,2,28)
        else:
            if self.date_end.month > 6:
                date_init = date(anio,7,1)
                date_end = date(anio+1,6,30)
            else:
                date_init = date(anio-1,7,1)
                date_end = date(anio,6,30)

        return date_init,date_end

    @api.multi
    def calcule_XIII_date(self):
        if self.date_end.month == 12 :
            anio = self.date_end.strftime('%Y')
            date_init = date(anio,12,1)
            date_end = date(anio,12,31)
        else:
            anio = int(self.date_end.strftime('%Y'))
            date_init = date(anio-1,12,1)
            date_end = self.date_end.replace(day=1)+relativedelta(months=1)+datetime.timedelta(days=-1)
        return date_init,date_end


    @api.multi
    def calcule_sayings(self, provision):
        obj_payslip = self.env['hr.payslip']
        value = 0.00
        if provision == 'ProvDec13':
            date_init,date_end = self.calcule_XIII_date()
        elif provision == 'ProvDec14':
            date_init,date_end = self.calcule_XIV_date()
        else:
            if self.date_start.month <= self.date_end.month:
                year = self.date_end.year
            else:
                year = self.date_end.year - 1

            date_init = date(year,self.date_start.month,1)
            date_end = self.date_end.replace(day=1)+relativedelta(months=1)+datetime.timedelta(days=-1)

        payslip_ids = obj_payslip.search([('employee_id','=',self.name.id),
                                        ('date_from','>=',date_init),
                                        ('date_to','<=',date_end),
                                        ('state','=','paid')])
        for payslip in payslip_ids:
            value += sum([line.total for line in payslip.line_ids if line.code in provision])
        return value

    @api.multi
    def diff_year(self):
        return int((self.date_end - self.date_start).days/365.2425)

    @api.multi
    def calcule_total_income(self):
        amount = sum([l.total for l in self.payslip_id.line_ids if l.category_id.code in ('APOR','NOAPOR')])
        amount += self.amount
        if self.settlement_id.code.upper() == 'INTEMPESTIVO':
            amount += (self.diff_year() * self.contract_id.wage)
        amount += (self.diff_year() * self.contract_id.wage * 0.25)
        amount += self.calcule_sayings('ProvDec13')
        amount += self.calcule_sayings('ProvDec14')
        amount += self.calcule_sayings('Vaca')
        return amount


    @api.multi
    def generate_paid(self):
        if self.pay_id:
            payment_ids = []
            obj_payment = self.env['account.batch.payment.payroll']
            # journal_id = self.env['account.journal'].search([('code','=','fnqt')])
            journal_id = self.env['ir.default'].sudo().get("res.config.settings",'journal_settlement',False,self.env.user.company_id.id)
            if not journal_id:
                raise ValidationError(_("Debe configurar un diario de liquidacion de fiquinito en Configuraciones."))
            amount = 0.00
            total = self.calcule_total_income() - self.calcule_total_expenses()
            if not self.name.bank_account_id:
                journal = self.env.ref('l10n_ec_nomina.payment_method_check').id
            else:
                journal = self.env.ref('l10n_ec_nomina.payment_method_transfer').id
            payment_ids.append((0,0,
                    {
                        'partner_type':'supplier',
                        'partner_id':self.name.address_home_id.id,
                        'employee_id':self.name.id,
                        'amount': total,
                        'payment_date': date.today(),
                        'communication':'Pago de Liquidacion de Finiquito ' + self.name.name,
                        'name':'Pago de Liquidacion de Finiquito ' + self.name.name,
                        'payment_type': 'outbound',
                        'journal_id':journal_id,
                        'payment_method_id': journal,
                    }
                ))
            payment_id = {
                    'batch_type':'outbound',
                    'date': date.today(),
                    'journal_id':journal_id,
                    'name': 'Pago de Liquidacion de Finiquito ' + self.name.name,
                    'payment_method_id': journal,
                }
            payment_id.update({'payment_ids': payment_ids})
            obj_payment.create(payment_id)

            lines = []
            for payslip in self.payslip_id.line_ids:
                if payslip.category_id.code in ('APOR','NOAPOR'):
                    rule_id = self.env['hr.salary.rule'].search([('code','=',payslip.code)])
                    if payslip.total != 0:
                        lines.append((0,0,
                            {
                                'ref': 'Liquidacion de Finiquito ' + self.name.name,
                                'account_id': rule_id.account_debit.id,
                                'credit': 0.0,
                                'debit': payslip.total,
                            }))
            amount = self.calcule_sayings('ProvDec13')
            contract_id = self.env['hr.contract'].search([('employee_id','=',self.name.id),('state','=','open')])
            if amount:
                rule_id = ''
                for line in contract_id.struct_id.rule_ids:
                    if line.code in 'ProvDec13':
                        rule_id = line
                        break
                if not rule_id:
                    for line in contract_id.struct_id.parent_id.rule_ids:
                        if line.code in 'ProvDec13':
                            rule_id = line
                            break
                
                lines.append((0,0,
                        {
                            
                            'ref': 'Liquidacion de Finiquito ' + self.name.name,
                            'account_id': rule_id.account_debit.id,
                            'credit': 0.0,
                            'debit': amount,
                        }))
            amount = self.calcule_sayings('ProvDec14')
            if amount:
                rule_id = ''
                for line in contract_id.struct_id.rule_ids:
                    if line.code in 'ProvDec14':
                        rule_id = line
                        break
                if not rule_id:
                    for line in contract_id.struct_id.parent_id.rule_ids:
                        if line.code in 'ProvDec14':
                            rule_id = line
                            break
                lines.append((0,0,
                        {
                            
                            'ref': 'Liquidacion de Finiquito ' + self.name.name,
                            'account_id': rule_id.account_debit.id,
                            'credit': 0.0,
                            'debit': amount,
                        }))
            amount = self.calcule_sayings('Vaca')
            if amount:
                rule_id = ''
                for line in contract_id.struct_id.rule_ids:
                    if line.code in 'Vaca':
                        rule_id = line
                        break

                if not rule_id:
                    for line in contract_id.struct_id.parent_id.rule_ids:
                        if line.code in 'Vaca':
                            rule_id = line
                            break
                lines.append((0,0,
                        {
                            
                            'ref': 'Liquidacion de Finiquito ' + self.name.name,
                            'account_id': rule_id.account_debit.id,
                            'credit': 0.0,
                            'debit': amount,
                        }))
            if self.settlement_id.code.upper() == 'INTEMPESTIVO':
                amount = (self.diff_year() * self.contract_id.wage)
                rule_id = ''
                for line in contract_id.struct_id.rule_ids:
                    if line.code in 'Bonif':
                        rule_id = line
                        break
                if not rule_id:
                    for line in contract_id.struct_id.parent_id.rule_ids:
                        if line.code in 'Bonif':
                            rule_id = line
                            break
                lines.append((0,0,
                        {
                            
                            'ref': 'Liquidacion de Finiquito ' + self.name.name,
                            'account_id': rule_id.account_debit.id,
                            'credit': 0.0,
                            'debit': amount,
                        }))
            amount = (self.diff_year() * self.contract_id.wage * 0.25)
            if amount:
                rule_id = ''
                for line in contract_id.struct_id.rule_ids:
                    if line.code in 'Bonif':
                        rule_id = line
                        break
                if not rule_id:
                    for line in contract_id.struct_id.parent_id.rule_ids:
                        if line.code in 'Bonif':
                            rule_id = line
                            break
                lines.append((0,0,
                        {
                            
                            'ref': 'Liquidacion de Finiquito ' + self.name.name,
                            'account_id': rule_id.account_debit.id,
                            'credit': 0.0,
                            'debit': amount,
                        }))
            
            for payslip in self.payslip_id.line_ids:
                if payslip.category_id.name == 'Descuentos':
                    rule_id = self.env['hr.salary.rule'].search([('code','=',payslip.code)])
                    if payslip.total != 0:
                        lines.append((0, 0,
                        {
                            
                            'ref': 'Liquidacion de Finiquito ' + self.name.name,
                            'account_id': rule_id.account_credit.id,
                            'credit': payslip.total,
                            'debit': 0.0
                        }))
            rule_id = ''
            for line in contract_id.struct_id.rule_ids:
                    if line.code in 'BASIC':
                        rule_id = line
                        break
            if not rule_id:
                for line in contract_id.struct_id.parent_id.rule_ids:
                    if line.code in 'ProvDec14':
                        rule_id = line
                        break
            lines.append((0,0,
                        { 
                        'ref': 'Liquidacion de Finiquito ' + self.name.name,
                        'account_id': rule_id.account_credit.id,
                        'credit': total,
                        'debit': 0.0,
                        }))
            acc_move_obj = self.env['account.move']
            move_data = {
                    'journal_id': journal_id,
                    'date': date.today(),
                        
                    }
            move_data.update({'line_ids': lines})
            acc_move_obj.create(move_data)
                    
            self.env.cr.commit()
