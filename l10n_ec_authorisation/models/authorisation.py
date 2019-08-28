# -*- coding: utf-8 -*-
# © <2016> <Cristian Salamea>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from datetime import datetime, date

from odoo import api, fields, models
from odoo.exceptions import (
    ValidationError,
    Warning as UserError
)


class AccountAtsDoc(models.Model):
    _name = 'account.ats.doc'
    _description = 'Tipos Comprobantes Autorizados'

    code = fields.Char('Código', size=2, required=True)
    name = fields.Char('Tipo Comprobante', size=64, required=True)


class AccountAtsSustento(models.Model):
    _name = 'account.ats.sustento'
    _description = 'Sustento del Comprobante'

    @api.multi
    @api.depends('code', 'type')
    def name_get(self):
        res = []
        for record in self:
            name = '%s - %s' % (record.code, record.type)
            res.append((record.id, name))
        return res

    _rec_name = 'type'

    code = fields.Char('Código', size=2, required=True)
    type = fields.Char('Tipo de Sustento', size=128, required=True)


class AccountAuthorisation(models.Model):

    _name = 'account.authorisation'
    _order = 'expiration_date desc'
    _rec_name = 'display_name'

    @api.depends('type_id', 'num_start', 'num_end', 'is_electronic', 'serie_emision', 'serie_entidad')
    @api.multi
    def _display_name(self):
        for s in self:
            name = u'[%s-%s del %s al %s] %s' % (
                s.serie_entidad,
                s.serie_emision,
                s.num_start,
                s.num_end or 'EL',
                s.type_id.name
            )
            s.display_name = name

    @api.one
    @api.depends('expiration_date', 'is_electronic')
    def _compute_active(self):
        """
        Check the due_date to give the value active field
        """
        if self.is_electronic:
            self.active = True
            return
        if not self.expiration_date:
            return
        now = date.today()
        due_date = self.expiration_date #datetime.strptime(self.expiration_date, '%Y-%m-%d')
        self.active = now < due_date

    def _get_type(self):
        return self._context.get('type', 'in_invoice')  # pylint: disable=E1101

    def _get_in_type(self):
        return self._context.get('in_type', 'externo')

    def _get_type_code(self):
        code = self._context.get('default_type_code', None)
        if code:
            type_obj=self.env['account.ats.doc']
            return type_obj.search([('code', '=', code)], limit=1)
        return None

    def _get_partner(self):
        partner = self.env.user.company_id.partner_id
        if self._context.get('partner_id'):
            partner = self._context.get('partner_id')
        return partner

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, values):
        res = self.search([('partner_id', '=', values['partner_id']),
                           ('type_id', '=', values['type_id']),
                           ('serie_entidad', '=', values['serie_entidad']),
                           ('serie_emision', '=', values['serie_emision']),
                           ('active', '=', True),
                           ('is_electronic', '=', values['is_electronic'])
                           ])
                           
        if res:
            MSG = u'Ya existe una autorización activa para %s' % self.type_id.name  # noqa
            raise ValidationError(MSG)

        partner_id = self.env.user.company_id.partner_id.id
        if values['partner_id'] == partner_id:
            typ = self.env['account.ats.doc'].browse(values['type_id'])
            name_type = '{0}_{1}_{2}_{3}'.format(values['name'] or 'electronic', values['type_id'], values['serie_entidad'], values['serie_emision'])
            sequence_data = {
                'code': typ.code == '07' and 'account.retention' or 'account.invoice',  # noqa
                'name': name_type,
                'padding': 9,
                'number_next': values['num_start'],
                }
            seq = self.env['ir.sequence'].create(sequence_data)
            values.update({'sequence_id': seq.id})
        return super(AccountAuthorisation, self).create(values)

    @api.multi
    def unlink(self):
        inv = self.env['account.invoice']
        res = inv.search([('auth_inv_id', '=', self.id)])
        if res:
            raise UserError(
                'Esta autorización esta relacionada a un documento.'
            )
        return super(AccountAuthorisation, self).unlink()

    name = fields.Char('Num. de Autorización', size=128)
    display_name = fields.Char('Display name', compute="_display_name", store=True)
    serie_entidad = fields.Char('Serie Entidad', size=3, required=True)
    serie_emision = fields.Char('Serie Emision', size=3, required=True)
    num_start = fields.Integer('Desde', default=1)
    num_end = fields.Integer('Hasta')
    is_electronic = fields.Boolean('Documento Electrónico ?')
    electronic_installed = fields.Boolean('Module electronico instalado', compute="_get_electronic_invoice")
    expiration_date = fields.Date('Fecha de Vencimiento')
    active = fields.Boolean(
        compute='_compute_active',
        string='Activo',
        store=True,
        default=True
        )
    in_type = fields.Selection(
        [('interno', 'Internas'),
         ('externo', 'Externas')],
        string='Tipo Interno',
        readonly=True,
        change_default=True,
        default=_get_in_type
        )
    type_id = fields.Many2one(
        'account.ats.doc',
        'Tipo de Comprobante',
        required=True,
        default=_get_type_code
        )
    partner_id = fields.Many2one(
        'res.partner',
        'Empresa',
        required=True,
        default=_get_partner
        )
    sequence_id = fields.Many2one(
        'ir.sequence',
        'Secuencia',
        help='Secuencia Alfanumerica para el documento, se debe registrar cuando pertenece a la compañia',  # noqa
        ondelete='cascade'
        )

    _sql_constraints = [
        ('number_unique',
         'unique(partner_id,expiration_date,type_id,is_electronic)',
         u'La relación de autorización, serie entidad, serie emisor y tipo, debe ser única.'),  # noqa
        ]

    def is_valid_number(self, number):
        """
        Metodo que verifica si @number esta en el rango
        de [@num_start,@num_end]
        """
        if self.is_electronic and self.num_start <= number :
            return True
        if self.num_start <= number <= self.num_end:
            return True
        return False


    @api.onchange('name','is_electronic')
    def onchange_name(self):
        if self.name:
            if not self.is_electronic and len(self.name) != 10:
                raise UserError('La numeración ingresada no coincide con el formato del SRI de 10 digitos.')
            elif self.is_electronic and len(self.name) != 37:
                raise UserError('La numeración ingresada no coincide con el formato del SRI de 37 digitos.')

    @api.depends('active', 'is_electronic', 'name')
    @api.multi
    def _get_electronic_invoice(self):
        module_obj = self.env['ir.module.module']
        m = module_obj.search([('name', '=', 'l10n_ec_einvoice')])
        for s in self:
            s.electronic_installed = len(m)>0


class ResPartner(models.Model):
    _inherit = 'res.partner'

    authorisation_ids = fields.One2many(
        'account.authorisation',
        'partner_id',
        'Autorizaciones'
        )

    @api.multi
    def get_authorisation(self, type_document):
        map_type = {
            'out_invoice': '18',
            'in_invoice': '01',
            'out_refund': '04',
            'in_refund': '05',
            'liq_purchase': '03',
            'ret_in_invoice': '07',
        }
        code = map_type[type_document]
        for a in self.authorisation_ids:
            if a.active and a.type_id.code == code:
                return a
        return False


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    auth_out_invoice_id = fields.Many2one(
        'account.authorisation',
        'Secuencia Facturas'
    )
    auth_out_refund_id = fields.Many2one(
        'account.authorisation',
        'Secuencia Notas de Credito'
    )
    auth_retention_id = fields.Many2one(
        'account.authorisation',
        'Para Retenciones'
    )
    auth_out_debit_id = fields.Many2one(
        'account.authorisation',
        'Para Notas de debito'
    )
    auth_out_liq_purchase_id = fields.Many2one(
        'account.authorisation',
        'Para Liquidacion de compras'
    )


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    _DOCUMENTOS_EMISION = ['out_invoice', 'liq_purchase', 'out_refund']

    @api.onchange('journal_id', 'auth_inv_id')
    def _onchange_journal_id(self):
        super(AccountInvoice, self)._onchange_journal_id()
        if self.journal_id and self.type in self._DOCUMENTOS_EMISION:
            if self.type == 'out_invoice':
                self.auth_inv_id = self.journal_id.auth_out_invoice_id
            elif self.type == 'out_refund':
                self.auth_inv_id = self.journal_id.auth_out_refund_id
            elif self.type == 'liq_purchase':
                self.auth_inv_id = self.journal_id.auth_out_liq_purchase_id.id
            self.auth_number = not self.auth_inv_id.is_electronic and self.auth_inv_id.name  # noqa
            number = '{0}'.format(
                str(self.auth_inv_id.sequence_id.number_next_actual).zfill(9)
            )
            self.reference = number

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        """
        Redefinicion de metodo para obtener:
        numero de autorizacion
        numero de documento
        El campo auth_inv_id representa la autorizacion para
        emitir el documento.
        """
        super(AccountInvoice, self)._onchange_partner_id()
        if self.type not in self._DOCUMENTOS_EMISION:
            self.auth_inv_id = self.partner_id.get_authorisation(self.type)

    @api.one
    @api.depends(
        'state',
        'reference'
    )
    def _compute_invoice_number(self):
        """
        Calcula el numero de factura segun el
        establecimiento seleccionado
        """
        if self.reference and self.state!='draft':
            self.invoice_number = '{0}{1}{2}'.format(
                self.auth_inv_id.serie_entidad,
                self.auth_inv_id.serie_emision,
                self.reference
            )
        else:
            self.invoice_number = '*'

    invoice_number = fields.Char(
        compute='_compute_invoice_number',
        string='Nro. Documento',
        store=True,
        readonly=True,
        copy=False
    )
    internal_inv_number = fields.Char('Numero Interno', copy=False)
    auth_inv_id = fields.Many2one(
        'account.authorisation',
        string='Establecimiento',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Autorizacion para documento',
        copy=False
    )
    is_electronic = fields.Boolean('Es Electronico', default=True)
    auth_number = fields.Char('Autorización')
    sustento_id = fields.Many2one(
        'account.ats.sustento',
        string='Sustento del Comprobante'
    )

   # _sql_constraints = [
   #     (
   #         'unique_invoice_number',
   #         'unique(reference,type,partner_id,state)',
   #         u'El número de factura es único.'
   #     )
   # ]

    @api.constrains('reference', 'type', 'partner_id', 'state')
    @api.one
    def check_invoice_number(self):
        invoice_obj=self.env['account.invoice']
        if self.state != 'draft':
            existing = invoice_obj.search([
                    ('type', '=', self.type),
                    ('reference', '=', self.reference),
                    ('partner_id', '=', self.partner_id.id),
                    ('invoice_number', '=', self.invoice_number),
                    ('id', '!=', self.id)
               ])
            if len(existing):
                raise ValidationError('El numero de factura debe ser unico.')


    @api.onchange('auth_inv_id')
    def _onchange_auth(self):
        if self.auth_inv_id and not self.auth_inv_id.is_electronic:
            self.auth_number = self.auth_inv_id.name
            self.is_electronic = False
        elif self.auth_inv_id and self.auth_inv_id.is_electronic:
            self.is_electronic = True

    @api.onchange('reference')
    def _onchange_ref(self):
        # TODO: agregar validacion numerica a reference
        if self.reference:
            self.reference = self.reference.zfill(9)
            if not self.auth_inv_id.is_valid_number(int(self.reference)):
                return {
                    'value': {
                        'reference': ''
                    },
                    'warning': {
                        'title': 'Error',
                        'message': u'Número no coincide con la autorización ingresada.'  # noqa
                    }
                }

    @api.constrains('auth_number')
    def check_reference(self):
        """
        Metodo que verifica la longitud de la autorizacion
        10: documento fisico
        35: factura electronica modo online
        49: factura electronica modo offline
        """
        if self.type not in ['in_invoice', 'liq_purchase']:
            return
        if self.auth_number and len(self.auth_number) not in [10, 35, 49]:
            raise UserError(
                u'Debe ingresar 10, 35 o 49 dígitos según el documento.'
            )

    @api.multi
    def action_number(self):
        # TODO: ver donde incluir el metodo de numeracion
        #self.ensure_one()
        if self.type not in ['out_invoice', 'liq_purchase', 'out_refund']:
            return
        number = self.internal_inv_number
        if not self.auth_inv_id:
            # asegura la autorizacion en el objeto
            self._onchange_journal_id()
            self._onchange_partner_id()
        if not number:
            sequence = self.auth_inv_id.sequence_id
            number = sequence.next_by_id()
        self.write({'reference': number, 'internal_inv_number': number})

    @api.multi
    def action_invoice_open(self):
        # lots of duplicate calls to action_invoice_open,
        # so we remove those already open
        # redefined for numbering document
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: inv.state not in ['proforma2', 'draft']):  # noqa
            raise UserError(_("Invoice must be in draft or Pro-forma state in order to validate it."))  # noqa
        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create()
        to_open_invoices.action_number()
        return to_open_invoices.invoice_validate()

    def _get_seq_number_next_stuff(self):
        self.ensure_one()
        journal_sequence = self.journal_id.sequence_id
        if self.journal_id.refund_sequence:
            domain = [('type', '=', self.type)]
            journal_sequence = self.type in ['in_refund', 'out_refund'] and self.journal_id.refund_sequence_id or self.journal_id.sequence_id
        elif self.type in ['in_invoice', 'in_refund']:
            domain = [('type', 'in', ['in_invoice', 'in_refund'])]
        elif self.type == 'liq_purchase':
            domain = [('type', '=', 'liq_purchase')]
            journal_sequence = self.type in ['liq_purchase'] and self.journal_id.auth_out_liq_purchase_id.sequence_id or self.journal_id.sequence_id
        else:
            domain = [('type', 'in', ['out_invoice', 'out_refund'])]
        if self.id:
            domain += [('id', '<>', self.id)]
        domain += [('journal_id', '=', self.journal_id.id), ('state', 'not in', ['draft', 'cancel'])]
        return journal_sequence, domain
