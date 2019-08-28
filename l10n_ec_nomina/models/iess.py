# -*- coding: utf-8 -*-
import logging

from openerp import (
    api,
    fields,
    models
)


class Comision(models.Model):
    _name = "iess.sectorial.comision"

    name = fields.Char("Nombre")
    code = fields.Char("Codigo")
    rama_ids = fields.One2many("iess.sectorial.rama", "comision_id", string="Ramas")

class Rama(models.Model):
    _name = "iess.sectorial.rama"

    name = fields.Char("Nombre")
    code = fields.Char("Codigo")
    comision_id = fields.Many2one("iess.sectorial.comision", "Comision")
    cargos_ids = fields.One2many("iess.sectorial.cargo", "rama_id", string="Cargos")

class Cargo(models.Model):
    _name = "iess.sectorial.cargo"

    name = fields.Char("Nombre")
    code = fields.Char("Codigo")
    value = fields.Float("Valor")
    rama_id = fields.Many2one("iess.sectorial.rama", "Rama")


