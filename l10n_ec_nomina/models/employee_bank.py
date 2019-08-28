# -*- coding: utf-8 -*-
import logging

from openerp import (
    api,
    fields,
    models
)


class EmployeeBank(models.Model):
    _name = "res.partner.bank"
    _inherit = "res.partner.bank"


    tipo_cuenta = fields.Selection([('ahorros', 'Ahorros'),
                                 ('corriente', 'Corriente')], string='Tipo Cuenta', help='Tipo de Cuenta')