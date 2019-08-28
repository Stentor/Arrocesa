# -*- coding: utf-8 -*-

from odoo import fields,api,models,_
from datetime import date
from odoo.exceptions import ValidationError
import xlsxwriter
from io import BytesIO
import base64

class hrPayslipRun(models.Model):
    _inherit = "hr.payslip.run"
    _description = ""

    state = fields.Selection([
        ('draft', 'Draft'),
        ('close', 'Close'),
        ('paid', 'Pagado'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')
    amount =  fields.Float('Total', compute="total_payroll")
    journal_id = fields.Many2one('account.journal', 'Salary Journal', states={'draft': [('readonly', False)]}, readonly=True,
        required=True, default=lambda self: self.env['ir.default'].sudo().get("res.config.settings",'journal_payroll',))


    def print_xlsx_payroll(self):
        file_data =  BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        query_totales = """select sum(hpl.total), hpl.name, hpl."sequence" from hr_payslip_run hpr 
                                join hr_payslip hp on hp.payslip_run_id =hpr.id
                                join hr_payslip_line hpl on hpl.slip_id = hp.id
                                join hr_employee he on hp.employee_id = he.id
                                where hpl.appears_on_payslip """
        query = """select distinct(hpl.name), hpl."sequence" from hr_payslip_run hpr 
                            join hr_payslip hp on hp.payslip_run_id =hpr.id
                            join hr_payslip_line hpl on hpl.slip_id = hp.id
                            where hpr.id=%s and hpl.appears_on_payslip
                            order by hpl.sequence """ %(self.id)
        name = self.name
        self.xslx_body(workbook,query_totales,query,name,False)
        workbook.close()
        file_data.seek(0)
        attachment = self.env['ir.attachment'].create({
            'datas': base64.b64encode(file_data.getvalue()),
            'name': self.name,
            'datas_fname': self.name + '.xlsx',
        })
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url += "/web/content/%s?download=true" %(attachment.id)
        return{
        "type": "ir.actions.act_url",
        "url": url,
        "target": "new",
        }
    
    def xslx_body(self,workbook,query_totales,query,name,comision):
        bold = workbook.add_format({'bold':True,'border':1,'bg_color':'#067eb2'})
        bold.set_center_across()
        number = workbook.add_format({'num_format':'$#,##0.00','border':1})
        number2 = workbook.add_format({'num_format':'$#,##0.00','border':1,'bg_color':'#067eb8','bold':True})
        border = workbook.add_format({'border':1})
        condition = " and hpr.id=%s group by hpl.sequence, hpl.name" %(self.id)
        struct_id = False
        if comision:
            struct_id = self.env['res.config.settings'].sudo(1).search([], limit=1, order="id desc").struct_id
            if not struct_id:
                raise ValidationError(_('No ha registrado una estructura para comisiones en sus configuraciones.'))
            condition_2 =" and hp.struct_id=%s" %struct_id.id 
            condition = condition_2 + condition
        col = 2
        colspan = 0
        sheet = workbook.add_worksheet(name)
        sheet.write(1,4,name.upper())
        sheet.write(col,colspan,'Mes')
        sheet.write(col,colspan+1,self.date_start.month)
        sheet.write(col,colspan+2,'Periodo')
        sheet.write(col,colspan+3,self.date_start.year)
        col += 1
        sheet.write(col,colspan,'No.',bold)
        sheet.write(col,colspan+1,'Localidad',bold)
        sheet.write(col,colspan+2,'Area',bold)
        sheet.write(col,colspan+3,'Departamento',bold)
        sheet.write(col,colspan+4,'Empleado',bold)
        sheet.freeze_panes(col+1,colspan+5)
        sheet.write(col,colspan+5,'Cedula',bold)
        sheet.write(col,colspan+6,'Dias Trabajados',bold)
        sheet.write(col,colspan+7,'Sueldo',bold)
        self.env.cr.execute(query)
        inputs = self.env.cr.fetchall()
        cont = 7
        dtc = {}
        for line in inputs:
            cont+=1
            sheet.write(col,colspan+cont,line[0],bold)
            dtc['%s' %(line[0])] =colspan+cont
        address = ''
        no = 0
        col -=1
        lineas = sorted(self.slip_ids,key=lambda x: x.employee_id.work_location)
        for payslip in lineas:
            if struct_id == False or payslip.struct_id == struct_id:
                if address != payslip.employee_id.work_location:
                    col += 1
                    if address != '':
                        no = 0
                        sheet.write(col,colspan+4, 'TOTAL %s' % address,bold)
                        self.env.cr.execute(query_totales+ (" and he.work_location = '%s'" %(address)) + condition)
                        totals = self.env.cr.fetchall()
                        cont = 8
                        for total in totals:
                            while (cont < dtc[total[1]]):
                                sheet.write(col,cont,0.00,number2)
                                cont += 1
                            sheet.write(col,dtc[total[1]],abs(total[0]),number2)
                            cont += 1
                    address = payslip.employee_id.work_location
                    col += 1    
                    sheet.merge_range(col,0,col,3,address,bold)
                no += 1
                col += 1
                if payslip.contract_id.department_id.parent_id:
                    department = payslip.contract_id.department_id.parent_id.name
                else:
                    department = payslip.contract_id.department_id.name
                sheet.write(col,colspan,no,border)
                sheet.write(col,colspan+1,payslip.employee_id.work_location,border)
                sheet.write(col,colspan+2, department,border)
                sheet.write(col,colspan+3, payslip.contract_id.department_id.name,border)
                sheet.write(col,colspan+4, payslip.contract_id.employee_id.name,border)
                sheet.write(col,colspan+5, payslip.contract_id.employee_id.identification_id,border)
                for days in payslip.worked_days_line_ids:
                    if days.code == 'WORK100':
                        day = days.number_of_days + 30 - payslip.date_to.day
                sheet.write(col,colspan+6, day,border)
                sheet.write(col,colspan+7, payslip.contract_id.wage,number)
                cont = 8
                for lines in payslip.line_ids:
                    if lines.appears_on_payslip:
                        # if self.name == name:
                        #     while (cont < dtc[lines.name]):
                        #         sheet.write(col,cont,0.00,number)
                        #         cont += 1
                        #     sheet.write(col,dtc[lines.name],abs(float(lines.total)),number)
                        #     cont += 1
                        # else:
                            # if lines.category_id.code == 'APOR':
                        while (cont < dtc[lines.name]):
                            sheet.write(col,cont,0.00,number)
                            cont += 1
                        sheet.write(col,dtc[lines.name],abs(float(lines.total)),number)
                        cont += 1
                
        col+=1
        #address = payslip.employee_id.work_location
        sheet.write(col,colspan+4, 'TOTAL %s' % address,bold)
        self.env.cr.execute(query_totales+ (" and he.work_location = '%s'" %(address)) + condition)
        totals = self.env.cr.fetchall()
        cont = 8
        for total in totals:
            while (cont < dtc[total[1]]):
                sheet.write(col,cont,0.00,number2)
                cont += 1
            sheet.write(col,dtc[total[1]],abs(total[0]),number2)
            cont += 1
        col += 1
        self.env.cr.execute(query_totales + condition)
        totals = self.env.cr.fetchall()
        sheet.write(col,colspan+4, 'TOTAL GENERAL',bold)
        cont = 8
        for total in totals:
            while (cont < dtc[total[1]]):
                sheet.write(col,cont,0.00,number2)
                cont += 1
            sheet.write(col,dtc[total[1]],abs(total[0]),number2)
            cont += 1

    
    def print_xlsx_comision(self):
        file_data =  BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        query_totales = """select sum(hpl.total), hpl.name, hpl."sequence" from hr_payslip_run hpr 
                                join hr_payslip hp on hp.payslip_run_id =hpr.id
                                join hr_payslip_line hpl on hpl.slip_id = hp.id
                                join hr_employee he on hp.employee_id = he.id
                                where hpl.appears_on_payslip """
        query = """select distinct(hpl.name), hpl."sequence" from hr_payslip_run hpr 
                            join hr_payslip hp on hp.payslip_run_id =hpr.id
                            join hr_payslip_line hpl on hpl.slip_id = hp.id
                            where hpr.id=%s and hpl.appears_on_payslip
                            order by hpl.sequence """ %(self.id)
        name = 'Comisiones de '+ self.name
        self.xslx_body(workbook,query_totales,query,name,True)
        workbook.close()
        file_data.seek(0)
        attachment = self.env['ir.attachment'].create({
            'datas': base64.b64encode(file_data.getvalue()),
            'name': self.name,
            'datas_fname': 'Comisiones del'+self.name + '.xlsx',
        })
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url += "/web/content/%s?download=true" %(attachment.id)
        return{
        "type": "ir.actions.act_url",
        "url": url,
        "target": "new",
        }
    
    @api.depends('slip_ids')
    def total_payroll(self):
        for s in self:
            s.amount = sum([l.amount for l in s.slip_ids])

    @api.multi
    def action_paid(self):
        payment_ids = []
        payment_transfer_id = []
        # journal_id = self.env['account.journal'].search([('code','=','pgno')])
        journal_id = self.env['ir.default'].sudo().get("res.config.settings",'journal_payroll_pay',False,self.env.user.company_id.id)
        if not journal_id:
            raise ValidationError(_("Debe configurar un diario de pago de nomina en Configuraciones."))
        obj_payment = self.env['account.batch.payment.payroll']
        check = self.env.ref('l10n_ec_nomina.payment_method_check').id
        transfer = self.env.ref('l10n_ec_nomina.payment_method_transfer').id
        for payslip in self.slip_ids:
            for line in payslip.line_ids:
                if line.code == 'NET':
                    amount = line.total
            payslip.state = 'paid'
            if not payslip.employee_id.bank_account_id:
                payment_ids.append((0,0,
                    {
                        'partner_type':'supplier',
                        'partner_id':payslip.employee_id.address_home_id.id,
                        'employee_id':payslip.employee_id.id,
                        'amount': amount,
                        'payment_date': date.today(),
                        'communication':payslip.name,
                        'name':'Pago de %s' %(payslip.name),
                        'payment_type': 'outbound',
                        'journal_id':journal_id,
                        'payment_method_id': check,
                    }
                ))
            else:
                payment_transfer_id.append((0,0,
                    {
                        'partner_type':'supplier',
                        'partner_id':payslip.employee_id.address_home_id.id,
                        'employee_id':payslip.employee_id.id,
                        'amount': amount,
                        'payment_date': date.today(),
                        'communication':payslip.name,
                        'name':'Pago de %s' %(payslip.name),
                        'payment_type': 'outbound',
                        'journal_id':journal_id,
                        'payment_method_id': transfer,
                    }
                ))
        if payment_ids:
            payment_id = {
                'batch_type':'outbound',
                'type_pay':'monthly',
                'date': date.today(),
                'journal_id':journal_id,
                'name': self.name + ' en Cheque',
                'payment_method_id': check,
            }
            payment_id.update({'payment_ids': payment_ids})
            obj_payment.create(payment_id)
        if payment_transfer_id:
            payment_id = {
                'batch_type':'outbound',
                'type_pay':'monthly',
                'date': date.today(),
                'journal_id':journal_id,
                'name': self.name + ' Transferencia',
                'payment_method_id': transfer,
            }
            payment_id.update({'payment_ids': payment_transfer_id})
            obj_payment.create(payment_id)
        self.state = 'paid'

    @api.multi
    def close_payslip_run(self):
        for payslip in self.slip_ids:
            payslip.compute_sheet()
            payslip.action_payslip_done()
        super(hrPayslipRun, self).close_payslip_run()

    @api.multi
    def draft_payslip_run(self):
        for payslip in self.slip_ids:
            if payslip.move_id.state == 'posted' and not payslip.move_id.reverse_entry_id:
                raise ValidationError(_('No se pueden cambiar a borrador porque existen asientos Publicados'))
            payslip.move_id = ''            
            payslip.action_payslip_draft()
        super(hrPayslipRun, self).draft_payslip_run()


class hrPayslip(models.Model):
    _inherit = "hr.payslip"
    _description = ""

    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('paid', 'Pagado'),
        ('cancel', 'Rejected'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft',
        help="""* When the payslip is created the status is \'Draft\'
                \n* If the payslip is under verification, the status is \'Waiting\'.
                \n* If the payslip is confirmed then status is set to \'Done\'.
                \n* When user cancel payslip the status is \'Rejected\'.""")

    amount = fields.Float("Total", compute="total_payslip_line", store=True)

    @api.depends('line_ids')
    def total_payslip_line(self):
        for s in self:
            s.amount = sum([l.total for l in s.line_ids if l.code == 'NET'])

    @api.multi
    def send_mail(self):
        tmpl = self.env.ref('l10n_ec_nomina.email_template_report_payslip')
        ctx = self.env.context.copy()
        ctx.pop('default_type', False)
        tmpl.with_context(ctx).send_mail(self.id,)

class hrPayrollEmployees(models.TransientModel):
    _inherit =  'hr.payslip.employees'

    def compute_employee(self):
        employee_ids = []
        employee_active = []
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start','date_end','slip_ids'])
            from_date = run_data.get('date_start')
            end_date = run_data.get('date_end')
            slip_ids =run_data.get('slip_ids')
            payslip_ids = self.env['hr.payslip'].browse(slip_ids)
            [employee_active.append(line.employee_id.id) for line in payslip_ids]
            contract_ids = self.env['hr.contract'].search(['|',('date_end','>',end_date),('date_end','=',None),('date_start','<=',end_date),('state','not in',('draft','cancel'))])
            [employee_ids.append(l.employee_id.id) for l in contract_ids if (l.date_end == False or l.date_end >= from_date) and l.employee_id.id not in (employee_active) ]
            return [('id', 'in',employee_ids)]
        return []


    employee_ids = fields.Many2many('hr.employee', 'hr_employee_group_rel', 'payslip_id', 'employee_id', 'Employees', domain=compute_employee)
        