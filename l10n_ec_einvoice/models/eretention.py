# -*- coding: utf-8 -*-

import os
import time
import logging
import itertools

from jinja2 import Environment, FileSystemLoader

from openerp import models, api
from openerp.exceptions import Warning as UserError

from datetime import datetime

from . import utils
from ..xades.sri import DocumentXML
from ..xades.xades import Xades

def fix_date(fecha):
    d = '{0:%d/%m/%Y}'.format(fecha)
    return d

class AccountWithdrawing(models.Model):

    _name = 'account.retention'
    _inherit = ['account.retention', 'account.edocument']
    _logger = logging.getLogger(_name)

    def get_secuencial(self):
        return getattr(self, 'name')[6:15]

    def _info_withdrawing(self, withdrawing):
        """
        """

        
        # generar infoTributaria
        company = withdrawing.company_id
        partner = withdrawing.invoice_id.partner_id
        infoCompRetencion = {
            'fechaEmision': fix_date(withdrawing.date),  # noqa
            'dirEstablecimiento': company.street,
            'obligadoContabilidad': 'SI',
            'tipoIdentificacionSujetoRetenido': utils.tipoIdentificacion[partner.type_identifier],  # noqa
            'razonSocialSujetoRetenido': partner.name,
            'identificacionSujetoRetenido': partner.identifier,
            'periodoFiscal': '{0:%m/%Y}'.format(withdrawing.date),
            }
        if company.company_registry:
            infoCompRetencion.update({'contribuyenteEspecial': company.company_registry})  # noqa
        return infoCompRetencion

    def _impuestos(self, retention):
        """
        """
        def get_original_tax_percent(linea):
            if linea.group_id.code in ['ret_vat_b', 'ret_vat_srv']:
                return linea.tax_id.percent_report
            return linea.tax_id.amount

        def get_base_line(linea):
            if linea.group_id.code in ['ret_vat_b', 'ret_vat_srv']:
                return linea.base*12.0/100.0
            return linea.base

        def get_codigo_retencion(linea):
            if linea.group_id.code in ['ret_vat_b', 'ret_vat_srv']:
                return utils.tabla21[str(get_original_tax_percent(linea))]
            #else:
            code = linea.code
            return code

        impuestos = []
        for line in retention.tax_ids:
            impuesto = {
                'codigo': utils.tabla20[line.group_id.code],
                'codigoRetencion': get_codigo_retencion(line),
                'baseImponible': '%.2f' % (get_base_line(line)),
                'porcentajeRetener': str(abs(float(get_original_tax_percent(line)))),
                'valorRetenido': '%.2f' % (abs(line.amount)),
                'codDocSustento': retention.invoice_id.sustento_id.code,
                'numDocSustento': retention.invoice_id.invoice_number,
                'fechaEmisionDocSustento': fix_date(retention.invoice_id.date_invoice)  # noqa
            }
            impuestos.append(impuesto)
        return {'impuestos': impuestos}

    def render_document(self, document, access_key, emission_code):
        tmpl_path = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(tmpl_path))
        ewithdrawing_tmpl = env.get_template('ewithdrawing.xml')
        data = {}
        data.update(self._info_tributaria(document, access_key, emission_code))
        data.update(self._info_withdrawing(document))
        data.update(self._impuestos(document))
        edocument = ewithdrawing_tmpl.render(data)
        self._logger.debug(edocument)
        return edocument, data

    def render_authorized_document(self, autorizacion, doc, xml):
        print(autorizacion)
        tmpl_path = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(tmpl_path))
        edocument_tmpl = env.get_template('authorized_withdrawing.xml')
        auth_xml = {
            'estado': autorizacion.estado,
            'numeroAutorizacion': doc['claveAcceso'],
            'ambiente': self.company_id.env_service,
            'fechaAutorizacion': "{0:%d/%m/%Y %H:%M:%S}".format(datetime.now()), 
            'comprobante': xml
        }
        auth_withdrawing = edocument_tmpl.render(auth_xml)
        return auth_withdrawing

    @api.multi
    def action_generate_document(self):
        """
        """
        for obj in self:
            self.check_date(obj.date)
            self.check_before_sent()
            access_key, emission_code = self._get_codes('account.retention')
            ewithdrawing, data = self.render_document(obj, access_key, emission_code)
            self._logger.debug(ewithdrawing)
            inv_xml = DocumentXML(ewithdrawing, 'withdrawing')
            inv_xml.validate_xml()
            xades = Xades()
            file_pk12 = obj.company_id.electronic_signature
            password = obj.company_id.password_electronic_signature
            signed_document = xades.sign(ewithdrawing, file_pk12, password)
            ok, errores = inv_xml.send_receipt(signed_document)
            if not ok:
                raise UserError(errores)
            auth, m = inv_xml.request_authorization(access_key)
            if not auth:
                msg = ' '.join(list(itertools.chain(*m)))
                raise UserError(msg)
            auth_document = self.render_authorized_document(auth, data, ewithdrawing)
            auth.numeroAutorizacion = data['claveAcceso']
            self.update_document(auth, [access_key, emission_code])
            attach = self.add_attachment(auth_document, auth)
            self.send_document(
                attachments=[a.id for a in attach],
                tmpl='l10n_ec_einvoice.email_template_eretention'
            )
            return True

    @api.multi
    def print_retention(self):
        """
        Método para imprimir reporte de retencion
        """
        return self.env.ref('l10n_ec_einvoice.account_retenciones').report_action(self)

    @api.multi
    def retention_print(self):
        """
        Método para imprimir reporte de retencion
        """
        return self.env.ref('l10n_ec_einvoice.account_retenciones').report_action(self)



class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_generate_eretention(self):
        for obj in self:
            if not obj.journal_id.auth_ret_id.is_electronic:
                return True
            obj.retention_id.action_generate_document()

    @api.multi
    def action_retention_create(self):
        super(AccountInvoice, self).action_retention_create()
        for obj in self:
            if obj.type in ['in_invoice', 'liq_purchase']:
                self.action_generate_eretention()
