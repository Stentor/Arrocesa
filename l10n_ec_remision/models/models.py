# -*- coding: utf-8 -*-

import os
import time
import logging
import itertools

from jinja2 import Environment, FileSystemLoader

from odoo import models, fields, api
from datetime import date, datetime

from odoo.exceptions import (
    Warning as UserError,
    ValidationError
)

from odoo.addons.l10n_ec_einvoice.models import utils
from odoo.addons.l10n_ec_einvoice.xades.sri import DocumentXML
from odoo.addons.l10n_ec_einvoice.xades.xades import Xades 

DATA_MODE = [
    ('invoice', 'Factura'),
    ('sale', 'Orden de venta'),
    ('move', 'Despacho/Transferencia')
]


class Transporter(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    is_transporter = fields.Boolean('Transportista', default=False)
    cont_especial = fields.Boolean('Codigo Contribuyente Especial')
    rise = fields.Boolean('RISE')



class GuiaRemision(models.Model):
    _name = 'account.guia.remision'
    _inherit = ['account.edocument', 'mail.thread', 'mail.activity.mixin']
    _logger = logging.getLogger(_name)

    name =  fields.Char('Numero', default="*")

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('valid', 'Validado'),
        ('sent', 'Enviado'),
        ('cancel', 'Anulado')
    ], string="Estado", default="draft", track_visibility="onchange")
    company_id = fields.Many2one('res.company', string="Compania", default=lambda self: self.env.user.company_id.id)
    transporter_id = fields.Many2one('res.partner', string="Transportista", domain=[('is_transporter', '=', True)] )
    auth_id = fields.Many2one('account.authorisation', 'Establecimiento')
    date = fields.Date("Fecha", default=date.today())
    line_ids = fields.One2many('account.guia.remision.line', inverse_name = 'guia_id', domain="[('state','=','done')]")
    placa = fields.Char('Placa')
    date_start = fields.Date('Fecha inicio')
    date_end = fields.Date('Fecha fin')

    

    def get_access_key(self, name):
       # if name == 'account.guia.remision':
        auth = self.auth_id ##self.company_id.partner_id.get_authorisation('out_invoice')
        # ld = self.date_invoice.split('-')
        numero = getattr(self, 'name')
        doc_date=self.date_start

        # ld.reverse()
        fecha = '{0:%d%m%Y}'.format(doc_date)
        tcomp = utils.tipoDocumento[auth.type_id.code]
        ruc = self.company_id.partner_id.identifier
        codigo_numero = self.get_code()
        tipo_emision = self.company_id.emission_code
        access_key = (
            [fecha, tcomp, ruc],
            [numero, codigo_numero, tipo_emision]
            )
        return access_key

    def validate(self):
            self.name="%s%s%09s"%(self.auth_id.serie_entidad,self.auth_id.serie_emision,self.auth_id.sequence_id.next_by_id())
            for line in self.line_ids:
                if line.invoice_id:
                    line.invoice_id.guia_ids = [(4,self.id)]
            return self.write({ 'state': 'valid'})
    

    def cancel(self):
        return self.write({ 'state': 'cancel'})


    def get_auth(self, document):
        return document.auth_id


    def render_document(self, document, access_key, emission_code):
        tmpl_path = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(tmpl_path))
        ewithdrawing_tmpl = env.get_template('xml_guia.xml')
        data = {}
        data.update(self._info_tributaria(document, access_key, emission_code))
        data.update(self._info_guia())
        data.update(self._info_destinatarios())
        edocument = ewithdrawing_tmpl.render(data)
        self._logger.debug(edocument)
        return edocument, data


    def _info_guia(self):
    
        data = {
            'dirEstablecimiento': " ".join((self.company_id.partner_id.street, self.company_id.partner_id.street2)),
            'dirPartida': " ".join((self.company_id.partner_id.street, self.company_id.partner_id.street2)),
            'razonSocialTransportista': self.transporter_id.name,
            'tipoIdentificacionTransportista': utils.tipoIdentificacion[self.transporter_id.type_identifier],
            'rucTransportista': self.transporter_id.identifier,
            'obligadoContabilidad': 'SI',
            'contribuyenteEspecial': self.transporter_id.cont_especial or None,
            'fechaIniTransporte': "{0:%d/%m/%Y}".format(self.date_start),
            'fechaFinTransporte': "{0:%d/%m/%Y}".format(self.date_end),
            'placa': self.placa
        }
        if self.transporter_id.rise:
            data.update({
                'rise': 'Contribuyente Regimen Simplificado RISE'
            })

        return data

    def _info_destinatarios(self):

        dests = []
        for line in self.line_ids:
            data = {
                'identificacionDestinatario' : line.partner_id.identifier,
                'razonSocialDestinatario' : line.partner_id.name,
                'dirDestinatario' : line.partner_id.street,
                'motivoTraslado' : line.motivo,
                #'codEstabDestino' : ,
                'ruta' : line.route_id.name,
            }
            if line.dau:
                data.update({
                    'docAduaneroUnico': line.dau
                })
            if line.invoice_id:
                data.update({
                    'invoice_id': line.invoice_id.id,
                    'codDocSustento': line.invoice_id.auth_inv_id.type_id.code,
                    'numDocSustento' : '-'.join((line.invoice_id.invoice_number[:3],line.invoice_id.invoice_number[3:6],line.invoice_id.invoice_number[6:])),
                    'numAutDocSustento' : line.invoice_id.numero_autorizacion or line.invoice_id.auth_number,
                    'fechaEmisionDocSustento' : "{0:%d/%m/%Y}".format(line.invoice_id.date_invoice),
                })
            

            details = []
            for move in line.picking_id.move_ids_without_package:
                for l in move.move_line_ids:
                    d = {
                        'codigoInterno': l.product_id.name[:25],
					    'codigoAdicional': l.product_id.barcode,
					    'descripcion': l.product_id.description,
					    'cantidad': l.qty_done
                    }

                    if l.product_id.tracking == 'serial':
                        d.update({
                            'serial': l.lot_id.name,
                        })
                    if l.product_id.tracking == 'lot':
                        d.update({
                            'lot': l.lot_id.name
                        })

                    details.append(d)

            data.update({
                'details': details
            })

            dests.append(data)
        return {
            'destinatarios': dests
        }

    def render_authorized_document(self, autorizacion, ):
        print(autorizacion)
        tmpl_path = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(tmpl_path))
        edocument_tmpl = env.get_template('authorized_withdrawing.xml')
        auth_xml = {
            'estado': autorizacion.estado,
            'numeroAutorizacion': autorizacion.numeroAutorizacion,
            'ambiente': self.company_id.env_service,
            'fechaAutorizacion': "{0:%d/%m/%Y %H:%M:%S}".format(datetime.now()), 
            'comprobante': autorizacion.comprobante
        }
        auth_withdrawing = edocument_tmpl.render(auth_xml)
        return auth_withdrawing

    @api.multi
    def action_generate_document(self):
        """
        """
        for obj in self:
            obj.check_date(obj.date_start)
            obj.check_before_sent()
            access_key, emission_code = obj._get_codes('account.guia.remision')
            ewithdrawing, data = obj.render_document(obj, access_key, emission_code)
            obj._logger.debug(ewithdrawing)
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
            auth_document = obj.render_authorized_document(auth)
            auth.numeroAutorizacion = data['claveAcceso']
            obj.update_document(auth, [access_key, emission_code])
            attach = obj.add_attachment(auth_document, auth)
            obj.send_document(
                attachments=[a.id for a in attach],
                tmpl='l10n_ec_remision.email_template_eremision'
            )
            return obj.write({'state': 'sent'})



class GuiaRemisionLine(models.Model):
    _name = 'account.guia.remision.line'

    guia_id = fields.Many2one('account.guia.remision', string = 'Guia de remision')
    picking_id = fields.Many2one('stock.picking', 'Despacho')
    partner_id = fields.Many2one('res.partner', related='picking_id.partner_id', readonly=True)
    invoice_id = fields.Many2one('account.invoice', string="Factura", compute='find_rel_invoice', store=True)
    dau = fields.Char('DAU')
    route_id = fields.Many2one('remision.route', string="Ruta")
    motivo = fields.Char('Motivo')

    @api.depends('picking_id')
    @api.multi
    def find_rel_invoice(self):
        invoice_obj = self.env['account.invoice']
        for s in self:
            if s.picking_id and s.picking_id.sale_id:
                ref = s.picking_id.sale_id.name   
                invoice_ids = invoice_obj.search([('origin','=', ref)])  
                for line in invoice_ids:
                    if line.journal_id and line.journal_id.auth_out_invoice_id and line.journal_id.auth_out_invoice_id.is_electronic and line.numero_autorizacion:
                        s.invoice_id = line[0]
                        break
                    elif line.journal_id and line.journal_id.auth_out_invoice_id and not line.journal_id.auth_out_invoice_id.is_electronic and line.auth_number:
                        s.invoice_id = line[0]
                        break

class GuiaRoute(models.Model):
    _name = 'remision.route'

    name=fields.Char('Ruta', length=300)

class Invoice(models.Model):
    _name="account.invoice"
    _inherit="account.invoice"

    guia_ids = fields.Many2many('account.guia.remision', string='Guias de remision')
