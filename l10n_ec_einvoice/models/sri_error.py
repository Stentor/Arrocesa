# -*- coding: utf-8 -*-


from openerp import api, models, fields
from openerp.exceptions import Warning as UserError

class SriError(models.Model):

    _name="sri.error" #sri_error

    invoice_id = fields.Many2one('account.invoice', string="Factura")
    message = fields.Char('Mensaje')
    state = fields.Char('Estado')