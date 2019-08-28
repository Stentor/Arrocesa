# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MrpProdCostParameters (models.TransientModel):
    _name = 'mrp.product.costing.parameters'
    _description = 'mrp product costing setting'
    _rec_name = "company_id"

    costs_planned_variances_account_id = fields.Many2one('account.account', string="Planned Variance Cost Account*",
        related="company_id.costs_planned_variances_account_id", readonly=False)
    costs_material_variances_account_id = fields.Many2one('account.account', string="Material Variances Cost Account*",
        related="company_id.costs_material_variances_account_id", readonly=False)
    costs_labour_variances_account_id = fields.Many2one('account.account', string="Labour/Machine Variances Cost Account*",
        related="company_id.costs_labour_variances_account_id", readonly=False)
    costs_planned_variances_analytic_account_id = fields.Many2one('account.analytic.account', string="Material Variance Costs Analytic Account*",
        related="company_id.costs_planned_variances_analytic_account_id", readonly=False)
    costs_material_variances_analytic_account_id = fields.Many2one('account.analytic.account', string="Material Variances Costs Analytic Account*",
        related="company_id.costs_material_variances_analytic_account_id", readonly=False)
    costs_labour_variances_analytic_account_id = fields.Many2one('account.analytic.account', string="Labour\Machine Variances Costs Analytic Account*",
        related="company_id.costs_labour_variances_analytic_account_id", readonly=False)
    manufacturing_journal_id = fields.Many2one('account.journal', string="Manufacturing journal id*", related="company_id.manufacturing_journal_id",    
        readonly=False) 
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    


class ResCompany(models.Model):
    _inherit = 'res.company'

    costs_planned_variances_account_id = fields.Many2one('account.account', string="Planned Variance Cost Account")
    costs_material_variances_account_id = fields.Many2one('account.account', string="Material Variance Cost Account")
    costs_labour_variances_account_id = fields.Many2one('account.account', string="Labour/Machine Variance Cost Account")
    costs_planned_variances_analytic_account_id = fields.Many2one('account.analytic.account', string="Planned Variance Costs Analytic Account")
    costs_material_variances_analytic_account_id = fields.Many2one('account.analytic.account', string="Material Variance Costs Analytic Account")
    costs_labour_variances_analytic_account_id = fields.Many2one('account.analytic.account', string="Labour\Machine Variance Costs Analytic Account")
    manufacturing_journal_id = fields.Many2one('account.journal', string="Manufacturing journal id")
    

 
