#-*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from datetime import date
import base64
from itertools import groupby
import io
import os
import logging
from jinja2 import Environment, FileSystemLoader

type_account = {
    'ahorros': 'CTA AHO',
    'corriente': 'CTA CTE',
}

type_doc = {
    'week': 'CANC SEMANA CUADRILLA',
    'fortnight': 'I QUINC',
    'monthly': 'II QUINC',
}

type_ident = {
    'cedula': 'C',
    'ruc': 'R',
    'pasaporte':'P',
}

class AccountPaymentPayroll(models.Model):
    _name = 'account.payment.payroll'
    _inherit = 'account.payment'
    _description = ''
    
    @api.multi
    @api.depends('move_line_ids.reconciled')
    def _get_move_reconciled(self):
        for payment in self:
            rec = True
            for aml in payment.move_line_ids.filtered(lambda x: x.account_id.reconcile):
                if not aml.reconciled:
                    rec = False
            payment.move_reconciled = rec

    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True)
    name = fields.Char(readonly=True, copy=False) # The name is attributed upon post()
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('sent', 'Sent'), ('reconciled', 'Reconciled'), ('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status")

    payment_type = fields.Selection(selection_add=[('transfer', 'Internal Transfer')])
    payment_reference = fields.Char(copy=False, readonly=True, help="Reference of the document used to issue this payment. Eg. check number, file name, etc.")
    move_name = fields.Char(string='Journal Entry Name', readonly=True,
        default=False, copy=False,
        help="Technical field holding the number given to the journal entry, automatically set when the statement line is reconciled then stored to set the same number again if the line is cancelled, set to draft and re-processed again.")

    # Money flows from the journal_id's default_debit_account_id or default_credit_account_id to the destination_account_id
    destination_account_id = fields.Many2one('account.account', compute='_compute_destination_account_id', readonly=True)
    # For money transfer, money goes from journal_id to a transfer account, then from the transfer account to destination_journal_id
    destination_journal_id = fields.Many2one('account.journal', string='Transfer To', domain=[('type', 'in', ('bank', 'cash'))])

    invoice_ids = fields.Many2many('account.invoice', 'account_invoice_payment_rel', 'payment_id', 'invoice_id', string="Invoices", copy=False, readonly=True, help="""Technical field containing the invoices for which the payment has been generated.
                                                                                                                                                                       This does not especially correspond to the invoices reconciled with the payment,
                                                                                                                                                                       as it can have been generated first, and reconciled later""")
    reconciled_invoice_ids = fields.Many2many('account.invoice', string='Reconciled Invoices', compute='_compute_reconciled_invoice_ids', help="Invoices whose journal items have been reconciled with this payment's.")
    has_invoices = fields.Boolean(compute="_compute_reconciled_invoice_ids", help="Technical field used for usability purposes")

    # FIXME: ondelete='restrict' not working (eg. cancel a bank statement reconciliation with a payment)
    move_line_ids = fields.One2many('account.move.line', 'payment_id', readonly=True, copy=False, ondelete='restrict')
    move_reconciled = fields.Boolean(compute="_get_move_reconciled", readonly=True)
    batch_payment_id = fields.Many2one('account.batch.payment.payroll', ondelete='set null', copy=False)
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    bank_id = fields.Many2one('res.bank',related="employee_id.bank_account_id.bank_id", string='Banco')
    
    @api.onchange('batch_payment_id')
    @api.multi
    def onchange_batch_payment_id(self):
        if self.batch_payment_id:
            self.journal_id = self.batch_payment_id.journal_id.id

    @api.multi
    def post(self):
        for s in self:
            lines = []
            s.state = 'posted'
            new_name = ""
            if s.journal_id.sequence_id:
                sequence = s.journal_id.sequence_id
                new_name = sequence.with_context(ir_sequence_date= date.today()).next_by_id()
            move_data = {
                    'journal_id': s.journal_id.id,
                    'date': date.today(), 
                    }
            lines.append((0, 0,
                {
                    'name': new_name,
                    'account_id': s.journal_id.default_debit_account_id.id,
                    'credit': s.amount,
                    'debit': 0.0
                }))
                    
            lines.append((0,0,
                {
                    'name': new_name,
                    'account_id': s.journal_id.default_credit_account_id.id,
                    'credit': 0.0,
                    'debit': s.amount,
                }))
            acc_move_obj = s.env['account.move']
            move_data.update({'line_ids': lines})
            move = acc_move_obj.create(move_data)
            move.post()
    
    @api.model
    def create_batch_payment(self):
        # We use self[0] to create the batch; the constrains on the model ensure
        # the consistency of the generated data (same journal, same payment method, ...)
        if any([p.payment_type == 'transfer' for p in self]):
            raise UserError(
                _('You cannot make a batch payment with internal transfers. Internal transfers ids: %s')
                % ([p.id for p in self if p.payment_type == 'transfer'])
            )

        batch = self.env['account.batch.payment.payroll'].create({
            'journal_id': self[0].journal_id.id,
            'payment_ids': [(4, payment.id, None) for payment in self],
            'payment_method_id': self[0].payment_method_id.id,
            'batch_type': self[0].payment_type,
        })

        return {
            "type": "ir.actions.act_window",
            "res_model": "account.batch.payment.payroll",
            "views": [[False, "form"]],
            "res_id": batch.id,
        }
    
    # @api.multi
    # def generate_bank_transfer(self,type_pay):
    #     txt = ''
    #     for payment in self:
    #         if payment.employee_id.bank_account_id:
    #             employee = payment.employee_id
    #             bank = employee.bank_account_id
    #             txt += "PA\t%s\tUSD\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" %(employee.identification_id,'%.2f'%(payment.amount),
    #                 type_account[bank.tipo_cuenta],bank.acc_number,type_doc[type_pay], payment.payment_date.month,
    #                 payment.payment_date.year,type_ident[payment.partner_id.type_identifier],employee.identification_id,employee.name)
    #     return txt


class AccountBatchPaymentPayroll(models.Model):
    _name = 'account.batch.payment.payroll'
    _description = ''

    payment_ids = fields.One2many('account.payment.payroll', 'batch_payment_id', string="Payments", required=True, readonly=True, states={'draft': [('readonly', False)]})
    name = fields.Char(required=True, copy=False, string='Reference', readonly=True, states={'draft': [('readonly', False)]})
    date = fields.Date(required=True, copy=False, default=fields.Date.context_today, readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'New'), ('sent', 'Sent'), ('reconciled', 'Reconciled')], readonly=True, default='draft', copy=False)
    journal_id = fields.Many2one('account.journal', string='Bank', domain=[('type', '=', 'bank')], required=True, readonly=True, states={'draft': [('readonly', False)]})
    amount = fields.Monetary(compute='_compute_amount', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', compute='_compute_currency', store=True, readonly=True)
    batch_type = fields.Selection(selection=[('inbound', 'Inbound'), ('outbound', 'Outbound')], required=True, readonly=True, states={'draft': [('readonly', '=', False)]}, default='inbound')
    payment_method_id = fields.Many2one(comodel_name='account.payment.method', string='Payment Method', required=True, readonly=True, states={'draft': [('readonly', '=', False)]}, help="The payment method used by the payments in this batch.")
    payment_method_code = fields.Char(related='payment_method_id.code', readonly=False)
    export_file_create_date = fields.Date(string='Generation Date', default=fields.Date.today, readonly=True, help="Creation date of the related export file.")
    export_file = fields.Binary(string='File', readonly=True, help="Export file related to this batch")
    export_filename = fields.Char(string='File Name', help="Name of the export file generated for this batch", store=True)
    type_pay = fields.Selection([('week','Semanal'),('fortnight','Quincena'),('monthly','Mensual')],'Tipo',default='monthly')
    available_payment_method_ids = fields.One2many(comodel_name='account.payment', compute='_compute_available_payment_method_ids')
    file_generation_enabled = fields.Boolean(help="Whether or not this batch payment should display the 'Generate File' button instead of 'Print' in form view.", compute='_compute_file_generation_enabled')

    @api.depends('payment_method_id')
    def _compute_file_generation_enabled(self):
        for record in self:
            record.file_generation_enabled = record.payment_method_id.code in record._get_methods_generating_files()

    def _get_methods_generating_files(self):
        """ Hook for extension. Any payment method whose code stands in the list
        returned by this function will see the "print" button disappear on batch
        payments form when it gets selected and an 'Export file' appear instead.
        """
        return []

    @api.depends('journal_id', 'batch_type')
    def _compute_available_payment_method_ids(self):
        for record in self:
            record.available_payment_method_ids = record.batch_type == 'inbound' and record.journal_id.inbound_payment_method_ids.ids or record.journal_id.outbound_payment_method_ids.ids

    @api.one
    @api.depends('journal_id')
    def _compute_currency(self):
        if self.journal_id:
            self.currency_id = self.journal_id.currency_id or self.journal_id.company_id.currency_id
        else:
            self.currency_id = False

    @api.one
    @api.depends('payment_ids', 'payment_ids.amount', 'journal_id')
    def _compute_amount(self):
        company_currency = self.journal_id.company_id.currency_id or self.env.user.company_id.currency_id
        journal_currency = self.journal_id.currency_id or company_currency
        amount = 0
        for payment in self.payment_ids:
            payment_currency = payment.currency_id or company_currency
            if payment_currency == journal_currency:
                amount += payment.amount
            else:
                # Note : this makes self.date the value date, which IRL probably is the date of the reception by the bank
                amount += payment_currency._convert(payment.amount, journal_currency, self.journal_id.company_id, self.date or fields.Date.today())
        self.amount = amount

    @api.constrains('batch_type', 'journal_id', 'payment_ids')
    def _check_payments_constrains(self):
        for record in self:
            all_companies = set(record.payment_ids.mapped('company_id'))
            if len(all_companies) > 1:
                raise ValidationError(_("All payments in the batch must belong to the same company."))
            for lines in record.payment_ids:
                lines.journal_id = self.journal_id.id
                # lines.payment_method_id = self.payment_method_id
            all_journals = set(record.payment_ids.mapped('journal_id'))
            if len(all_journals) > 1 or record.payment_ids[0].journal_id != record.journal_id:
                raise ValidationError(_("The journal of the batch payment and of the payments it contains must be the same."))
            all_types = set(record.payment_ids.mapped('payment_type'))
            if all_types and record.batch_type not in all_types:
                raise ValidationError(_("The batch must have the same type as the payments it contains."))
            all_payment_methods = set(record.payment_ids.mapped('payment_method_id'))
            if len(all_payment_methods) > 1:
                raise ValidationError(_("All payments in the batch must share the same payment method."))
            if all_payment_methods and record.payment_method_id not in all_payment_methods:
                raise ValidationError(_("The batch must have the same payment method as the payments it contains."))

    @api.model
    def create(self, vals):
        vals['name'] = self._get_batch_name(vals.get('batch_type'), vals.get('date', fields.Date.context_today(self)), vals)
        rec = super(AccountBatchPaymentPayroll, self).create(vals)
        rec.normalize_payments()
        return rec

    @api.multi
    def write(self, vals):
        if 'batch_type' in vals:
            vals['name'] = self.with_context(default_journal_id=self.journal_id.id)._get_batch_name(vals['batch_type'], self.date, vals)

        rslt = super(AccountBatchPaymentPayroll, self).write(vals)

        if 'payment_ids' in vals:
            self.normalize_payments()

        return rslt

    @api.one
    def normalize_payments(self):
        # Since a batch payment has no confirmation step (it can be used to select payments in a bank reconciliation
        # as long as state != reconciled), its payments need to be posted
        self.payment_ids.filtered(lambda r: r.state == 'draft')

    @api.model
    def _get_batch_name(self, batch_type, sequence_date, vals):
        if not vals.get('name'):
            sequence_code = 'account.inbound.batch.payment'
            if batch_type == 'outbound':
                sequence_code = 'account.outbound.batch.payment'
            return self.env['ir.sequence'].with_context(sequence_date=sequence_date).next_by_code(sequence_code)
        return vals['name']

    def validate_batch(self):
        txt = ''
        records = self.filtered(lambda x: x.state == 'draft')
        for record in records:
            record.payment_ids.write({'state':'sent', 'payment_reference': record.name})
            record.payment_ids.post()
        records.write({'state': 'sent'})
        records = self.filtered(lambda x: x.file_generation_enabled)
        # self.format_report_id.report_action(self)
        if records:
            return self.export_batch_payment()

    @api.multi
    def report_bank(self):
        dtc = []
        data = {'employees':''}
        for payment in self.payment_ids:
            if payment.employee_id.bank_account_id:
                employee = payment.employee_id
                bank = employee.bank_account_id
                dtc.append({
                    'identifier':employee.identification_id,
                    'amount':'%.2f'%(payment.amount),
                    'type_account':type_account[bank.tipo_cuenta],
                    'account_number':bank.acc_number,
                    'reference':type_doc[self.type_pay],
                    'month':payment.payment_date.month,
                    'year':payment.payment_date.year,
                    'type_identifier':type_ident[payment.partner_id.type_identifier],
                    'name':employee.name,
                })
        if not dtc:
            raise ValidationError(_("Ninguno de los empleados tiene asignada una cuenta bancaria."))
        data = {'employees':dtc}
        if self.journal_id.format_transfer_id:
            tmpl_path = os.path.join(os.path.dirname(__file__), 'template')
            env = Environment(loader=FileSystemLoader(tmpl_path))
            format_report = env.get_template(self.journal_id.format_transfer_id+'.xml')
            report = format_report.render(data)
            buf = io.StringIO()
            buf.write(report)
            out = base64.encodestring(buf.getvalue().encode('utf-8')).decode()
            logging.error(out)
            buf.close()
            self.export_file = out
            self.export_filename = 'Transferencias Bancarias.txt'
            return out
        else:
            raise ValidationError(_("Primero debe configurar un formato de Transferencia Bancaria en el Diario."))


class accountJournal(models.Model):
    _inherit = 'account.journal'

    format_transfer_id = fields.Selection([
        ('banco_pichincha','Banco Pichincha')],string='Formato de Transferencia Bancaria')