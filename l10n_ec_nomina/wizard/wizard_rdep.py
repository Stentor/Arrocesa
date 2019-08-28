# -*- coding: utf-8 -*-

import base64
import io
import os
import logging
from itertools import groupby
from operator import itemgetter

from lxml import etree
from lxml.etree import DocumentInvalid
from jinja2 import Environment, FileSystemLoader

from odoo import fields, models, api
from odoo.exceptions import ValidationError

from odoo.addons.l10n_ec_withholding.wizard.utils import convertir_fecha, get_date_value

tpIdEmployee = {
    'cedula': 'C',
    'pasaporte': 'P',
    'ruc':'C',
    }

tpCodRule = {
    'ingresos': ['BASIC','Bonif','Alim','Comi','HorExt','HorSupl','Movil'],
    'sobresueldo': ['Bonif','Alim','Comi','HorExt','HorSupl','Movil'],
}

afirmations = {
    True: '02',
    False: '01',
}

confirmation = {
    True: 'SI',
    False: 'NO',
}


class AccountRdep(dict):
    """
    representacion del RDEP
    >>> rdep.campo = 'valor'
    >>> rdep['campo']
    'valor'
    """

    def __getattr__(self, item):
        try:
            return self.__getitem__(item)
        except KeyError:
            raise AttributeError(item)

    def __setattr__(self, item, value):
        if item in self.__dict__:
            dict.__setattr__(self, item, value)
        else:
            self.__setitem__(item, value)


class WizardRdep(models.TransientModel):

    _name = 'wizard.rdep'
    _description = 'Retenciones en la Fuente Bajo Relacion de Depencia'
    __logger = logging.getLogger(_name)

    @api.multi
    def _get_period(self):
        return None

    @api.multi
    def _get_company(self):
        return self.env.user.company_id.id

    def act_cancel(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def read_employee(self, period):
        sql = """select distinct(employee_id) from hr_payslip
                where
                date_from >= '%s-01-01' and date_to <= '%s-12-31' 
                and company_id = %s""" %(period,period,self.company_id.id)
        self.env.cr.execute(sql)
        sql_data = self.env.cr.fetchall()
        employee =[]
        for line in sql_data:
            employee.append(line)
        employee_ids = self.env['hr.employee'].search([('id','in',employee)])
        return employee_ids

    @api.multi
    def calcule_rule(self,rule,employee):
        obj_payslip = self.env['hr.payslip']
        payslip_ids = obj_payslip.search([('date_from','>=',str(self.period_id) + '-01-01'),
                                        ('date_to','<=',str(self.period_id) + '-12-31'),
                                        ('employee_id','=',employee),
                                        ('state','=','paid')])
        amount = 0.00
        for payslip in payslip_ids:
            for lines in payslip.line_ids:
                if lines.code in rule:
                    amount += lines.amount
        return round(amount,2)

    @api.multi
    def calcule_expenses(self,employee):
        obj_expenses = self.env['hr.employee.gastos']
        expenses_id = obj_expenses.search([('fiscal_year','=',str(self.period_id)),('employee_id','=',employee)])
        return expenses_id

    @api.multi
    def check_tax(self, valor):
        obj_expenses = self.env['hr.impuesto.renta']
        expenses_id = obj_expenses.search([('frac_bas','<=',valor),('exceso_hasta','>=',valor)])
        new_base = valor - expenses_id.frac_bas
        new_base = (new_base * (expenses_id.porc_imp_frac_exc / 100)) + expenses_id.imp_frac_bas
        return new_base
    
    def read_form_107(self,employee):
        obj_imp = self.env['hr.wizard.impuesto.renta']
        imp_id = obj_imp.search([('name','=',employee.id),('anio','=',self.period_id)],order="id desc", limit=1)
        return imp_id

    
    def _get_employee(self):
        employee_ids = self.read_employee(self.period_id)
        data = []
        for employee in employee_ids:
            imp =  self.read_form_107(employee)
            expense = self.calcule_expenses(employee.id)
            ci = '999'
            identification = 'N'
            if employee.apply_agreement:
                ci = employee.partner_id.identifier
                identification = tpIdEmployee[employee.partner_id.type_identifier]
            data.append({
                'benGalpg': confirmation[employee.galapagos_beneficiary],
                'enfcatastro': confirmation[employee.catastrophic_disease],
                'tipIdRet': tpIdEmployee[employee.address_id.type_identifier],
                'idRet': employee.identification_id,
                'apellidoTrab': employee.lastname,
                'nombreTrab':  employee.firstname,
                'estab': self.num_estab_ruc,
                'residenciaTrab': '01',
                'paisResidencia': '593',
                'aplicaConvenio': confirmation[employee.apply_agreement],
                'tipoTrabajDiscap': afirmations[employee.discapacitado],
                'porcentajeDiscap': int(employee.porc_discapacidad),
                'tipIdDiscap': identification,
                'idDiscap': ci,
                'suelSal':'%.2f' % self.calcule_rule('BASIC',employee.id),
                'sobSuelComRemu':'%.2f' % self.calcule_rule(tpCodRule['sobresueldo'],employee.id),
                'partUtil': imp.util or '0.00',
                'intGrabGen': imp.ing_grav_otroempl or '0.00',
                'impRentEmpl':'%.2f' % abs(self.calcule_rule('ImpRent',employee.id)),#verificar
                'decimTer':'%.2f' % self.calcule_rule('ProvDec13',employee.id),
                'decimCuar':'%.2f' % self.calcule_rule('ProvDec14',employee.id),
                'fondoReserva':'%.2f' % self.calcule_rule('FonResv',employee.id),
                'salarioDigno':'0.00',#cambiar
                'otrosIngRenGrav': imp.otros_ing or '0.00',
                'ingGravConEsteEmpl':'%.2f' % self.calcule_rule(tpCodRule['ingresos'],employee.id),
                'sisSalNet':1,
                'apoPerIess':'%.2f' % (self.calcule_rule('ApIESSPer',employee.id)*-1),
                'aporPerIessConOtrosEmpls': imp.apor_iess or '0.00',
                'deducVivienda':'%.2f' % expense.gasto_vivienda,
                'deducSalud':'%.2f' % expense.gasto_salud,
                'deducEducartcult':'%.2f' % expense.gasto_educacion,
                'deducAliement':'%.2f' % expense.gasto_alimentacion,
                'deducVestim':'%.2f' % expense.gasto_vestimenta,
                'exoDiscap': imp.exo_discapacidad or '0.00',
                'exoTerEd': imp.exo_ter_edad or '0.00',
                'basImp':'%.2f' % (self.calcule_rule('NET',employee.id) - self.calcule_rule('ApIESSPer',employee.id)),
                'impRentCaus':'%.2f' % self.check_tax(self.calcule_rule('BASIC',employee.id) + self.calcule_rule(tpCodRule['sobresueldo'],employee.id) +
                self.calcule_rule('ApIESSPer',employee.id) - expense.gasto_vivienda - expense.gasto_salud - 
                expense.gasto_educacion - expense.gasto_alimentacion - expense.gasto_vestimenta), 
                'valRetAsuOtrosEmpls': imp.imp_ret_asum or '0.00',
                'valImpAsuEsteEmpl': imp.imp_asum_estempl or '0.00',
                'valRet': '%.2f' % abs(self.calcule_rule('ImpRent',employee.id)),
            })
        return data



    @api.multi
    def render_xml(self, rdep):
        tmpl_path = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(tmpl_path))
        rdep_tmpl = env.get_template('rdep.xml')
        return rdep_tmpl.render(rdep)

    @api.multi
    def validate_document(self, rdep, error_log=False):
        file_path = os.path.join(os.path.dirname(__file__), 'XSD/rdep.xsd')
        schema_file = open(file_path)
        xmlschema_doc = etree.parse(schema_file)
        xmlschema = etree.XMLSchema(xmlschema_doc)
        root = etree.fromstring(rdep.encode())
        ok = True
        if not self.no_validate:
            try:
                xmlschema.assertValid(root)
            except DocumentInvalid:
                ok = False
        return ok, xmlschema

    @api.multi
    def act_export_rdep(self):
        rdep = AccountRdep()
        period = self.period_id
        ruc = self.company_id.partner_id.identifier
        rdep.employees = self._get_employee()
        rdep_rendered = self.render_xml(rdep)
        ok, schema = self.validate_document(rdep_rendered)
        buf = io.StringIO()
        buf.write(rdep_rendered)
        out = base64.encodestring(buf.getvalue().encode('utf-8')).decode()
        logging.error(out)
        buf.close()
        buf_erro = io.StringIO()
        for err in schema.error_log:
            buf_erro.write(err.message+'\n')
        out_erro = base64.encodestring(buf_erro.getvalue().encode())
        buf_erro.close()
        name = "%s%s.XML" % (
            "RDEP",
            period
        )
        data2save = {
            'state': ok and 'export' or 'export_error',
            'data': out,
            'fcname': name
        }
        if not ok:
            data2save.update({
                'error_data': out_erro,
                'fcname_errores': 'ERRORES.txt'
            })
        self.write(data2save)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.rdep',
            'view_mode': ' form',
            'view_type': ' form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    fcname = fields.Char('Nombre de Archivo', size=50, readonly=True)
    fcname_errores = fields.Char('Archivo Errores', size=50, readonly=True)
    period_id = fields.Char('Periodo',size=4)
    # period_start = fields.Date('Inicio de periodo')
    # period_end = fields.Date('Fin de periodo')
    company_id = fields.Many2one(
        'res.company',
        'Compania',
        default=_get_company
    )
    num_estab_ruc = fields.Char(
        'Num. de Establecimientos',
        size=3,
        required=True,
        default='001'
    )
    # pay_limit = fields.Float('Limite de Pago', default=1000)
    data = fields.Binary('Archivo XML')
    error_data = fields.Binary('Archivo de Errores')
    no_validate = fields.Boolean('No Validar')
    state = fields.Selection(
        (
            ('choose', 'Elegir'),
            ('export', 'Generado'),
            ('export_error', 'Error')
        ),
        string='Estado',
        default='choose'
    )
