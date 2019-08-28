# -*- coding: utf-8 -*-
# © <2016> <Cristian Salamea>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import logging

from openerp import (
    api,
    fields,
    models
)
from openerp.exceptions import (
    Warning as UserError
)
import openerp.addons.decimal_precision as dp

# mapping invoice type to journal type
TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale_refund',
    'in_refund': 'purchase_refund',
    'liq_purchase': 'purchase'
}


class Invoice(models.Model):

    _name = 'account.invoice'
    _inherit = 'account.invoice'
    __logger = logging.getLogger(_inherit)

    PRECISION_DP = dp.get_precision('Account')

    amount_ice = fields.Monetary(
        string='ICE',
        store=True,
        readonly=True,
        compute='_compute_amount'
    )
    amount_vat = fields.Monetary(
        string='Base 12 %',
        store=True,
        readonly=True,
        compute='_compute_amount'
    )
    amount_untaxed = fields.Monetary(
        string='Untaxed',
        store=True,
        readonly=True,
        compute='_compute_amount'
    )
    amount_untaxed_ice = fields.Monetary(
        string='Untaxed',
        store=True,
        readonly=True,
        compute='_compute_amount'
    )
    amount_tax = fields.Monetary(
        string='Tax',
        store=True,
        readonly=True,
        compute='_compute_amount'
    )
    amount_total = fields.Monetary(
        string='Total a Pagar',
        store=True,
        readonly=True,
        compute='_compute_amount'
    )
    amount_pay = fields.Monetary(
        string='Total',
        store=True,
        readonly=True,
        compute='_compute_amount'
    )
    amount_noret_ir = fields.Monetary(
        string='Monto no sujeto a IR',
        store=True,
        readonly=True,
        compute='_compute_amount'
    )
    amount_tax_retention = fields.Monetary(
        string='Total Retenciones',
        store=True,
        readonly=True,
        compute='_compute_amount'
    )
    amount_tax_ret_ir = fields.Monetary(
        string='Base IR',
        store=True,
        readonly=True,
        compute='_compute_amount'
    )
    taxed_ret_ir = fields.Monetary(
        string='Impuesto IR',
        store=True,
        readonly=True,
        compute='_compute_amount'
    )
    amount_tax_ret_vatb = fields.Monetary(
        string='Base Ret. IVA',
        store=True,
        readonly=True,
        compute='_compute_amount'
    )
    taxed_ret_vatb = fields.Monetary(
        string='Retencion en IVA',
        store=True,
        readonly=True,
        compute='_compute_amount'
    )
    amount_tax_ret_vatsrv = fields.Monetary(
        string='Base Ret. IVA',
        store=True,
        readonly=True,
        compute='_compute_amount'
    )
    taxed_ret_vatsrv = fields.Monetary(
        string='Retencion en IVA',
        store=True,
        readonly=True,
        compute='_compute_amount'
    )
    amount_vat_cero = fields.Monetary(
        string='Base IVA 0%',
        store=True,
        readonly=True,
        compute='_compute_amount'
    )
    amount_novat = fields.Monetary(
        string='Base No IVA',
        store=True,
        readonly=True,
        compute='_compute_amount'
    )
    retention_id = fields.Many2one(
        'account.retention',
        string='Retención de Impuestos',
        store=True, readonly=True,
        copy=False
    )
    has_retention = fields.Boolean(
        compute='_check_retention',
        string="Tiene Retención en IR",
        store=True,
        readonly=True
        )
    type = fields.Selection(
        [
            ('out_invoice', 'Customer Invoice'),
            ('in_invoice', 'Supplier Invoice'),
            ('out_refund', 'Customer Refund'),
            ('in_refund', 'Supplier Refund'),
            ('liq_purchase', 'Liquidacion de Compra')
        ], 'Type', readonly=True, index=True, change_default=True)
    withholding_number = fields.Char(
        'Num. Retención',
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False
    )
    create_retention_type = fields.Selection(
        [
            ('auto', 'Automatico'),
            ('manual', 'Manual')
        ],
        string='Numerar Retención',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default='auto'
    )
    reference = fields.Char(copy=False)
    ats_earning_id=fields.Many2one('ats.earning', string="Tipo de ingreso exterior")

    @api.model
    def _default_journal(self):
        if self._context.get('default_journal_id', False):
            return self.env['account.journal'].browse(self._context.get('default_journal_id'))  # noqa
        inv_type = self._context.get('type', 'out_invoice')
        inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
        company_id = self._context.get('company_id', self.env.user.company_id.id)  # noqa
        domain = [
            ('type', 'in', list(filter(None, list(map(TYPE2JOURNAL.get, inv_types))))),
            ('company_id', '=', company_id),
        ]
        return self.env['account.journal'].search(domain, limit=1)

    journal_id = fields.Many2one('account.journal', string='Journal',
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=_default_journal,
        domain="[('type', 'in', {'out_invoice': ['sale'], 'out_refund': ['sale'], 'in_refund': ['purchase'], 'in_invoice': ['purchase'], 'liq_purchase': ['purchase']}.get(type, [])), ('company_id', '=', company_id)]")
    

    @api.multi
    def print_move(self):
        # Método para imprimir comprobante contable
        return self.env.ref('l10n_ec_withholding.account_move_report').report_action(self)

    @api.multi
    def print_liq_purchase(self):
        # Método para imprimir reporte de liquidacion de compra
        return self.env['report'].get_action(
            self.move_id,
            'l10n_ec_withholding.account_liq_purchase_report'
        )

    @api.multi
    def print_retention(self):
        """
        Método para imprimir reporte de retencion
        """
        return self.env.ref('l10n_ec_withholding.account_withdrawing_report').report_action(self)

    @api.model
    def get_ice(self):
        ice = [tax for tax in self.tax_line_ids if tax.tax_id.tax_group_id.code == 'ice']
        return ice
        
    def _prepare_tax_line_vals(self, line, tax):
        """ Prepare values to create an account.invoice.tax line

        The line parameter is an account.invoice.line, and the
        tax parameter is the output of account.tax.compute_all().
        """
        current = self.env['account.tax'].browse(tax['id'])
        group = current.tax_group_id
        vals = {
            'invoice_id': self.id,
            'name': tax['name'],
            'group': group.code,
            'tax_id': tax['id'],
            'amount': tax['amount'],
            'price': line.product_id.standard_price*line.quantity,
            'base': tax['base'],
            'manual': False,
            'sequence': tax['sequence'],
            'account_analytic_id': tax['analytic'] and line.account_analytic_id.id or False,
            'account_id': self.type in ('out_invoice', 'in_invoice') and (tax['account_id'] or line.account_id.id) or (tax['refund_account_id'] or line.account_id.id),
            'analytic_tag_ids': tax['analytic'] and line.analytic_tag_ids.ids or False,
        }
        current = self.env['account.tax'].browse(tax['id'])
        group = current.tax_group_id
        if group.code == 'ice':
            vals.update({
                'base': max(line.product_id.standard_price*1.25*line.quantity, tax['base']/1.0515),
                'amount': max(line.product_id.standard_price*1.25*line.quantity, tax['base']/1.0515)*float(current.percent_report)/100.0,
            })
        if group.code in ['vat', 'ret_vat_srv', 'ret_vat_b', 'ret_ir']:
            ice = self.get_ice()
            if len(ice)>0:
                ice = ice[0]
                vals.update({
                    'base': vals['base']+ice.amount,
                    'amount': (vals['base']+ice.amount) * current.amount/100.0
                })  
        # If the taxes generate moves on the same financial account as the invoice line,
        # propagate the analytic account from the invoice line to the tax line.
        # This is necessary in situations were (part of) the taxes cannot be reclaimed,
        # to ensure the tax move is allocated to the proper analytic account.
        if not vals.get('account_analytic_id') and line.account_analytic_id and vals['account_id'] == line.account_id.id:
            vals['account_analytic_id'] = line.account_analytic_id.id
        return vals

    # @api.multi
    # def get_taxes_values(self):
    #     tax_grouped = {}
    #     tax_reg = []
    #     round_curr = self.currency_id.round
    #     for line in self.invoice_line_ids:
    #         if not line.account_id:
    #             continue
    #         price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
    #         taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']
    #         for tax in taxes:
    #             val = self._prepare_tax_line_vals(line, tax)
    #             tax_reg.append(val)
    #         tax_reg = self.fix_taxes_ice(tax_reg)
    #         for tax in tax_reg:
    #             key = self.env['account.tax'].browse(tax['tax_id']).get_grouping_key(tax)
    #             if key not in tax_grouped:
    #                 tax_grouped[key] = tax
    #                 tax_grouped[key]['base'] = round_curr(tax['base'])
    #             else:
    #                 tax_grouped[key]['amount'] += tax['amount']
    #                 tax_grouped[key]['base'] += round_curr(tax['base'])
    #     return tax_grouped

    def fix_taxes_ice(self, taxes):
        ice = [tax for tax in taxes if tax['group'] == 'ice']
        mods = [tax for tax in taxes if tax['group'] in ['vat', 'ret_vat_srv', 'ret_vat_b', 'ret_ir'] ]
        others =  [tax for tax in taxes if tax['group'] not in ['ice','vat', 'ret_vat_srv', 'ret_vat_b', 'ret_ir'] ]
        res = []

        if len(ice)>0:
            ice = ice[0]
            current = self.env['account.tax'].browse(ice['tax_id'])
            
            ice.update({
                'base': max(ice['price']*1.25, ice['base']/1.0515),
                'amount': max(ice['price']*1.25, ice['base']/1.0515)*float(current.percent_report)/100.0,
            })
            res.append(ice)
            for tax in mods:
                current = self.env['account.tax'].browse(tax['tax_id'])
                tax.update({
                     'base': tax['base']+ice['amount'],
                     'amount': (tax['base']+ice['amount']) * current.amount/100.0
                 })
                res.append(tax)
        else:
            return taxes

        return res+others



    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'tax_line_ids.amount_rounding',
                 'currency_id', 'company_id', 'date_invoice', 'type')   # noqa
    def _compute_amount(self):
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)  # noqa
        amount_manual = 0
        for line in self.tax_line_ids:
            if line.manual:
                amount_manual += line.amount
            if line.tax_id.tax_group_id.code == 'vat':
                self.amount_vat += line.base
                self.amount_tax += line.amount
            elif line.tax_id.tax_group_id.code == 'vat0':
                self.amount_vat_cero += line.base
            elif line.tax_id.tax_group_id.code == 'novat':
                self.amount_novat += line.base
            elif line.tax_id.tax_group_id.code == 'no_ret_ir':
                self.amount_noret_ir += line.base
            elif line.tax_id.tax_group_id.code in ['ret_vat_b', 'ret_vat_srv', 'ret_ir', 'comp']:  # noqa
                self.amount_tax_retention += line.amount
                if line.tax_id.tax_group_id.code == 'ret_vat_b':
                    self.amount_tax_ret_vatb += line.base
                    self.taxed_ret_vatb += line.amount
                elif line.tax_id.tax_group_id.code == 'ret_vat_srv':
                    self.amount_tax_ret_vatsrv += line.base
                    self.taxed_ret_vatsrv += line.amount
                elif line.tax_id.tax_group_id.code == 'ret_ir':
                    self.amount_tax_ret_ir += line.base
                    self.taxed_ret_ir += line.amount
            elif line.tax_id.tax_group_id.code == 'ice':
                self.amount_ice += line.amount
        if self.amount_vat == 0 and self.amount_vat_cero == 0:
            # base vat not defined, amount_vat by default
            self.amount_vat_cero = self.amount_untaxed
        self.amount_untaxed_ice = self.amount_untaxed + self.amount_ice
        self.amount_total = self.amount_untaxed + self.amount_tax + self.amount_tax_retention + amount_manual + self.amount_ice  # noqa
        self.amount_pay = self.amount_tax + self.amount_untaxed + self.amount_ice
        # continue odoo code for *signed fields
        amount_total_company_signed = self.amount_total
        
        amount_untaxed_signed = self.amount_untaxed 
        if self.currency_id and self.currency_id != self.company_id.currency_id:  # noqa
            amount_total_company_signed = self.currency_id.compute(self.amount_total, self.company_id.currency_id)  # noqa
            amount_untaxed_signed = self.currency_id.compute(self.amount_untaxed, self.company_id.currency_id)  # noqa
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign

    @api.multi
    def name_get(self):
        result = []
        for inv in self:
            result.append((inv.id, "%s %s" % (inv.reference, inv.number and inv.number or '*')))  # noqa
        return result

    @api.one
    @api.depends('tax_line_ids.tax_id')
    def _check_retention(self):
        TAXES = ['ret_vat_b', 'ret_vat_srv', 'ret_ir', 'no_ret_ir']  # noqa
        for tax in self.tax_line_ids:
            if tax.tax_id.tax_group_id.code in TAXES:
                self.has_retention = True


    @api.onchange('withholding_number')
    def _onchange_withholding(self):
        if self.create_retention_type == 'manual' and self.withholding_number:
            auth_ret = self.journal_id.auth_retention_id
            if not auth_ret.is_valid_number(int(self.withholding_number)):
                raise UserError('El número de retención no pertenece a una secuencia activa en la empresa.')  # noqa
            self.withholding_number = self.withholding_number.zfill(9)

    @api.multi
    def action_invoice_open(self):
        # lots of duplicate calls to action_invoice_open,
        # so we remove those already open
        # redefined to create withholding and numbering
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: inv.state not in ['proforma2', 'draft']):  # noqa
            raise UserError(_("Invoice must be in draft or Pro-forma state in order to validate it."))  # noqa
        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create()
        to_open_invoices.action_number()
        to_open_invoices.action_withholding_create()
        return to_open_invoices.invoice_validate()

    @api.multi
    def action_invoice_cancel(self):
        """
        Primero intenta cancelar la retencion
        """
        if self.retention_id:
            self.retention_id.action_cancel()
        super(Invoice, self).action_invoice_cancel()

    @api.multi
    def action_invoice_draft(self):
        """
        Redefinicion de metodo para cancelar la retencion asociada.
        En facturacion electronica NO se permite regresar a cancelado.
        Redefinicion de metodo para borrar la retencion asociada.
        TODO: reversar secuencia si fue auto ?
        """
        for inv in self:
            if inv.retention_id:
                inv.retention_id.unlink()
        super(Invoice, self).action_invoice_draft()
        return True

    @api.multi
    def action_withholding_create(self):
        """
        Este método genera el documento de retencion en varios escenarios
        considera casos de:
        * Generar retencion automaticamente
        * Generar retencion de reemplazo
        * Cancelar retencion generada
        """
        TYPES_TO_VALIDATE = ['in_invoice', 'liq_purchase']
        wd_number = False
        for inv in self:
            if not self.has_retention:
                continue

            # Autorizacion para Retenciones de la Empresa
            auth_ret = inv.journal_id.auth_retention_id
            if inv.type in ['in_invoice', 'liq_purchase'] and not auth_ret:
                raise UserError(
                    u'No ha configurado la autorización de retenciones.'
                )

            if self.create_retention_type == 'manual':
                wd_number = inv.withholding_number

            # move to constrains ?
            if inv.create_retention_type == 'manual' and inv.withholding_number <= 0:  # noqa
                raise UserError(u'El número de retención es incorrecto.')
                # TODO: read next number

            ret_taxes = inv.tax_line_ids.filtered(lambda l: l.tax_id.tax_group_id.code in ['ret_vat_b', 'ret_vat_srv', 'ret_ir'])  # noqa

            if inv.retention_id:
                ret_taxes.write({
                    'retention_id': inv.retention_id.id,
                    'num_document': inv.invoice_number
                })
                inv.retention_id.action_validate(wd_number)
                return True

            withdrawing_data = {
                'partner_id': inv.partner_id.id,
                'name': wd_number,
                'invoice_id': inv.id,
                'auth_id': auth_ret.id,
                'type': inv.type,
                'in_type': 'ret_%s' % inv.type,
                'date': inv.date_invoice,
                'manual': False
            }

            withdrawing = self.env['account.retention'].create(withdrawing_data)  # noqa

            ret_taxes.write({'retention_id': withdrawing.id, 'num_document': inv.reference})  # noqa

            if inv.type in TYPES_TO_VALIDATE:
                withdrawing.action_validate(wd_number)

            inv.write({'retention_id': withdrawing.id})
        return True

    @api.multi
    def action_retention_cancel(self):
        """
        TODO: revisar si este metodo debe llamarse desde el cancelar
        factura
        """
        for inv in self:
            if inv.retention_id:
                inv.retention_id.action_cancel()
        return True

    @api.multi
    @api.returns('self')
    def refund(self, date_invoice=None, date=None, description=None, journal_id=None):  # noqa
        new_invoices = super(Invoice, self).refund(date_invoice, date, description, journal_id)  # noqa
        new_invoices._onchange_journal_id()
        return new_invoices

    @api.model
    def tax_line_move_line_get(self):
        res = []
        # keep track of taxes already processed
        done_taxes = []
        # loop the invoice.tax.line in reversal sequence
        for tax_line in sorted(self.tax_line_ids, key=lambda x: -x.sequence):
            if tax_line.amount_total:
                tax = tax_line.tax_id
                if tax.amount_type == "group":
                    for child_tax in tax.children_tax_ids:
                        done_taxes.append(child_tax.id)

                analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in tax_line.analytic_tag_ids]
                res.append({
                    'invoice_tax_line_id': tax_line.id,
                    'tax_line_id': tax_line.tax_id.id,
                    'type': 'tax',
                    'tax_group': tax_line.tax_id.tax_group_id.code,
                    'name': tax_line.name,
                    'price_unit': tax_line.amount_total,
                    'quantity': 1,
                    'price': tax_line.amount_total,
                    'account_id': tax_line.account_id.id,
                    'account_analytic_id': tax_line.account_analytic_id.id,
                    'analytic_tag_ids': analytic_tag_ids,
                    'invoice_id': self.id,
                    'tax_ids': [(6, 0, list(done_taxes))] if tax_line.tax_id.include_base_amount else []
                })
                done_taxes.append(tax.id)
        if self.type in ['out_invoice', ]:
            res = filter( lambda tax: tax['tax_group'] not in ['ret_ir', 'ret_vat_b', 'ret_vat_srv'], res)
        return res


#class AccountInvoiceLine(models.Model):
#    _inherit = 'account.invoice.line'
#
#    def _set_taxes(self):
#        """
#        Redefinicion para leer impuestos desde category_id
#        TODO: leer impuestos desde category_id
#        """
#        super(AccountInvoiceLine, self)._set_taxes()


class AccountInvoiceTax(models.Model):

    _inherit = 'account.invoice.tax'

    retention_id = fields.Many2one(
        'account.retention',
        'Retención',
        index=True
    )

    @api.multi
    def get_invoice(self, number):
        return self.env['account.invoice'].search([('number', '=', number)])

    @api.onchange('tax_id')
    def _onchange_tax(self):
        if not self.tax_id:
            return
        self.name = self.tax_id.description
        self.account_id = self.tax_id.account_id and self.tax_id.account_id.id
        self.base = self.retention_id.invoice_id.amount_untaxed
        self.amount = self.tax_id.compute_all(self.retention_id.invoice_id.amount_untaxed)['taxes'][0]['amount']  # noqa
