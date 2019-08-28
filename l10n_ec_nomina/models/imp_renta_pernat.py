# -*- coding: utf-8 -*-
import logging

from openerp import (
    api,
    fields,
    models
)


class Imprentapernat(models.Model):
    _name = "hr.impuesto.renta"

    code = fields.Char("Codigo")
    frac_bas = fields.Float("Fracción Básica")
    exceso_hasta = fields.Float("Exceso Hasta")
    imp_frac_bas = fields.Float("Impuesto Fracción Básica")
    porc_imp_frac_exc = fields.Float("% Impuesto Fracción Excedente")


   