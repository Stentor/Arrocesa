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

from openerp import fields, models, api

from datetime import date
from dateutil.relativedelta import relativedelta


class WizardDinardap(models.TransientModel):

    _name = 'wizard.dinardap'
    _description = 'Reporte Dinardap'
    __logger = logging.getLogger(_name)

    @api.multi
    def _get_company(self):
        return self.env.user.company_id.id

    fcname = fields.Char('Nombre de Archivo', size=50, readonly=True)

    period_start = fields.Date('Inicio de periodo')
    period_end = fields.Date('Fecha de corte')
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
    
    data = fields.Binary('Archivo XML')

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


    def act_cancel(self):
        return {'type': 'ir.actions.act_window_close'}


    
    #@api.multi
    def act_export_dinardap(self):
        lines = self._get_lines({})
        self.__logger.debug(lines)

        buf = io.StringIO()
        buf.write('\r\n'.join(['|'.join(line) for line in lines]))
        out = base64.encodestring(buf.getvalue().encode('utf-8')).decode()
        logging.error(out)
        buf.close()
        print("dinardap")
        name = "%s%s.txt" % (
            self.company_id.partner_id.identifier,
            '{0:%d%m%Y}'.format(date.today())
        )
        data2save = {
            'state': 'export',
            'data': out,
            'fcname': name
        }
        self.write(data2save)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.dinardap',
            'view_mode': ' form',
            'view_type': ' form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',

        }

    def _get_lines(self, options, line_id=None):
        lines = []

        partners = self.env['res.partner'].search([('customer','=', True)])

        for partner in partners:
            amls = partner.unreconciled_aml_ids.filtered(lambda l: l.company_id == self.env.user.company_id).filtered(lambda l: l.date <= self.period_end).sorted(key=lambda x: x.invoice_id.id)
            data = groupby(amls, lambda x: x.invoice_id.id)
            for id, aml in data:
                aml=list(aml)
                due_1_30, due_31_60, due_61_90, due_91_180, due_181_360, due_360 = self.past_due_segmented(aml)
                upcoming_1_30, upcoming_31_60, upcoming_61_90, upcoming_91_180, upcoming_181_360, upcoming_360 = self.upcoming_due_segmented(aml)
                if aml[0].invoice_id.payment_term_id and (aml[0].invoice_id.payment_term_id.report_dinardap == True):
                    lines.append([
                        self.company_id.dinardap_id or '1234',
                        '{0:%d/%m/%Y}'.format(self.period_end + relativedelta(day=31)),
                        aml[0].invoice_id.partner_id.dinardap_id_type,
                        aml[0].invoice_id.partner_id.identifier,
                        aml[0].invoice_id.partner_id.name,
                        aml[0].invoice_id.partner_id.dinardap_class or '',
                        aml[0].invoice_id.partner_id.dinardap_province.code,
                        aml[0].invoice_id.partner_id.dinardap_canton.code,
                        aml[0].invoice_id.partner_id.dinardap_parroquia.code,
                        aml[0].invoice_id.partner_id.dinardap_sexo or '',
                        aml[0].invoice_id.partner_id.dinardap_civil_state or '',
                        aml[0].invoice_id.partner_id.dinardap_origin or '',
                        aml[0].invoice_id.invoice_number,
                        '{:.2f}'.format(aml[0].invoice_id.amount_total),
                        '{:.2f}'.format(aml[0].invoice_id.residual),
                        '{0:%d/%m/%Y}'.format(aml[0].invoice_id.date_invoice),
                        '{0:%d/%m/%Y}'.format(max((a.date_maturity for a in aml))),
                        '{0:%d/%m/%Y}'.format(min((a.date_maturity for a in aml))),
                        str((max((a.date_maturity for a in aml)) - aml[0].invoice_id.date_invoice).days),
                        '30',
                        str(self.past_due_days(aml)),
                        '{:.2f}'.format(self.past_due_amount(aml)),
                        '0.00',
                        '{:.2f}'.format(upcoming_1_30),
                        '{:.2f}'.format(upcoming_31_60),
                        '{:.2f}'.format(upcoming_61_90),
                        '{:.2f}'.format(upcoming_91_180),
                        '{:.2f}'.format(upcoming_181_360),
                        '{:.2f}'.format(upcoming_360),
                        '{:.2f}'.format(due_1_30),
                        '{:.2f}'.format(due_31_60),
                        '{:.2f}'.format(due_61_90),
                        '{:.2f}'.format(due_91_180),
                        '{:.2f}'.format(due_181_360),
                        '{:.2f}'.format(due_360),
                        '0.00',
                        '0.00',
                        '{:.2f}'.format(self.latest_payment_amount(aml[0].invoice_id)),
                        self.latest_payment_date(aml[0].invoice_id),
                        self.latest_payment_method(aml[0].invoice_id)                        
                    ])
        return lines


    def past_due_days(self,aml):
        result = (self.period_end - max((a.date_maturity for a in aml))).days
        if result > 0:
            return result
        return 0

    def past_due_amount(self,aml):
        result = sum(( a.balance for a in aml if a.date_maturity<= self.period_end))
        if result > 0:
            return result
        return 0

    def past_due_segmented(self, aml):
        today = self.period_end
        due_1_30 = sum(( a.balance for a in aml if 0<=(today - a.date_maturity).days <=30))
        due_31_60 = sum(( a.balance for a in aml if 31<=(today - a.date_maturity).days <=60))
        due_61_90 = sum(( a.balance for a in aml if 61<=(today - a.date_maturity).days <=90))
        due_91_180 = sum(( a.balance for a in aml if 91<=(today - a.date_maturity).days <=180))
        due_181_360 = sum(( a.balance for a in aml if 181<=(today - a.date_maturity).days <=360))
        due_360 = sum(( a.balance for a in aml if 361<=(today - a.date_maturity).days ))

        return (due_1_30, due_31_60, due_61_90, due_91_180, due_181_360, due_360)

    def upcoming_due_segmented(self, aml):
        today = self.period_end
        due_1_30 = sum(( a.balance for a in aml if 0<=(a.date_maturity - today).days <=30))
        due_31_60 = sum(( a.balance for a in aml if 31<=(a.date_maturity - today).days <=60))
        due_61_90 = sum(( a.balance for a in aml if 61<=(a.date_maturity - today).days <=90))
        due_91_180 = sum(( a.balance for a in aml if 91<=(a.date_maturity - today).days <=180))
        due_181_360 = sum(( a.balance for a in aml if 181<=(a.date_maturity - today).days <=360))
        due_360 = sum(( a.balance for a in aml if 361<=(a.date_maturity - today).days ))

        return (due_1_30, due_31_60, due_61_90, due_91_180, due_181_360, due_360)

    def latest_payment_amount(self, invoice):
        payments = invoice.payment_ids.sorted(key="payment_date")
        if len(payments)>0:
            return payments[:-1].amount
        return 0
    
    def latest_payment_date(self, invoice):
        payments = invoice.payment_ids.sorted(key="payment_date")
        if len(payments)>0 and isinstance(payments[:-1].payment_date, date):
            return '{0:%d/%m/%Y}'.format(payments[:-1].payment_date)
        return '00/00/0000'

    def latest_payment_method(self, invoice):
        payments = invoice.payment_ids.sorted(key="payment_date")
        if len(payments)>0:
            return payments[:-1].dinardap_pay_method or 'E'
        return 'E'