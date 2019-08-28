# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    costs_overheads_fixed_percentage = fields.Float(string='Fixed OVH Costs %', default="0.0")
    costs_overheads_fixed_analytic_account_id = fields.Many2one('account.analytic.account', string="Fixed OVH Costs Analytic Account")
    costs_overheads_variable_percentage = fields.Float(string='Variable OVH Costs %', default="0.0")
    costs_overheads_variable_analytic_account_id = fields.Many2one('account.analytic.account', string="Variable OVH Costs Analytic Account")