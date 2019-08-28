# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api, _
from odoo import exceptions

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    state = fields.Selection(selection_add=[('cost', 'Closed')])
    financial_closed = fields.Boolean("Financial Closing Performed", default=False)

    @api.multi
    def action_economical_closure(self):
        for record in self:
            record._bom_analytic_postings()
            record._wc_analytic_postings()
            record._planned_variance_postings()
            record._variance_postings()
            record.state = 'cost'
            record.financial_closed = True
        return True

    @api.multi
    def button_mark_done(self):
        if self.financial_closed:
            raise exceptions.UserError('Manufacturing Order already closed')
        return super(MrpProduction, self).button_mark_done()

    @api.multi
    def _bom_analytic_postings(self):
        for record in self:
            desc_bom = str(record.name) 
            # overhead material fixed cost posting
            id_created= self.env['account.analytic.line'].create({
                'name': desc_bom,
                'account_id': record.bom_id.costs_overheads_fixed_analytic_account_id.id,
                'ref': "OVH fixed material costs",
                'date': record.date_finished,
                'product_id': record.product_id.id,
                'amount': - record.fixed_ovh_mat_cost,
                'unit_amount': record.qty_produced,
                'product_uom_id': record.product_uom_id.id,
                'company_id': record.company_id.id	
            })
            # overhead material variable cost posting
            id_created= self.env['account.analytic.line'].create({
                'name': desc_bom,
                'account_id': record.bom_id.costs_overheads_variable_analytic_account_id.id,
                'ref': "OVH variable material costs",
                'date': record.date_finished,
                'product_id': record.product_id.id,
                'amount': - record.variable_ovh_mat_cost,
                'unit_amount': record.qty_produced,
                'product_uom_id': record.product_uom_id.id,
                'company_id': record.company_id.id	
            })
        return True
        
        
    @api.multi
    def _wc_analytic_postings(self):
        for record in self:
            for workorder in record.workorder_ids:
                # fixed direct cost posting
                desc_wo = str(record.name) + '-' + str(workorder.workcenter_id.name) + '-' + str(workorder.name)
                fixedamount = 0.0
                for time in workorder.time_ids:
                    fixedamount += (workorder.workcenter_id.time_stop + workorder.workcenter_id.time_start) * workorder.workcenter_id.costs_hour_fixed / 60
                id_created= self.env['account.analytic.line'].create({
                    'name': desc_wo,
                    'account_id': workorder.workcenter_id.costs_fixed_analytic_account_id.id,
                    'ref': "fixed statistical direct costs",
                    'date': record.date_finished,
                    'product_id': record.product_id.id,
                    'amount': - fixedamount,
                    'unit_amount': record.qty_produced,
                    'product_uom_id': record.product_uom_id.id,
                    'company_id': workorder.workcenter_id.company_id.id	
                })
                # overhead Labour/Machine fixed cost posting
                id_created= self.env['account.analytic.line'].create({
                    'name': desc_wo,
                    'account_id': workorder.workcenter_id.costs_overheads_fixed_analytic_account_id.id,
                    'ref': "OVH fixed labour/machine costs",
                    'date': record.date_finished,
                    'product_id': record.product_id.id,
                    'amount': - (workorder.duration * workorder.workcenter_id.costs_hour / 60) * (workorder.workcenter_id.costs_overheads_fixed_percentage / 100),
                    'unit_amount': record.qty_produced,
                    'product_uom_id': record.product_uom_id.id,
                    'company_id': workorder.workcenter_id.company_id.id	
                })
                # overhead Labour/Machine variable cost posting
                id_created= self.env['account.analytic.line'].create({
                    'name': desc_wo,
                    'account_id': workorder.workcenter_id.costs_overheads_variable_analytic_account_id.id,
                    'ref': "OVH variable labour/machine costs",
                    'date': record.date_finished,
                    'product_id': record.product_id.id,
                    'amount': - (workorder.duration * workorder.workcenter_id.costs_hour / 60) * (workorder.workcenter_id.costs_overheads_variable_percentage / 100),
                    'unit_amount': record.qty_produced,
                    'product_uom_id': record.product_uom_id.id,
                    'company_id': workorder.workcenter_id.company_id.id	
                })
        return True


    @api.multi
    def _planned_variance_postings(self):
        for record in self:
             #production planned variance costs posting
             planned_cost = record.prod_std_cost 
             standard_cost = record.cur_std_cost 
             delta = (standard_cost - planned_cost) * record.qty_produced
             desc_bom = str(record.name) 
             if delta < 0.0:
                    id_created_header = self.env['account.move'].create({
                        'journal_id' : record.company_id.manufacturing_journal_id.id,
                        'date': record.date_finished,
                        'ref' : "Planned Variance Costs",
                        'company_id': record.company_id.id,
                    })
                    id_credit_item = self.env['account.move.line'].with_context(check_move_validity=False).create({
                        'move_id' : id_created_header.id,
                        'account_id': record.company_id.costs_planned_variances_account_id.id,
                        'analytic_account_id' : record.company_id.costs_planned_variances_analytic_account_id.id,
                        'product_id': record.product_id.id,
                        'name' : desc_bom,
                        'quantity': record.qty_produced,
                        'product_uom_id': record.product_uom_id.id,
                        'credit': - delta,
                        'debit': 0.0,
                    })
                    id_debit_item= self.env['account.move.line'].with_context(check_move_validity=False).create({
                        'move_id' : id_created_header.id,
                        'account_id': record.product_id.property_stock_production.valuation_out_account_id.id,
                        'product_id': record.product_id.id,
                        'name' : desc_bom,
                        'quantity': record.qty_produced,
                        'product_uom_id': record.product_uom_id.id,
                        'credit': 0.0,
                        'debit': - delta,
                    })
                    id_created_header.post()
             elif delta > 0.0:
                    id_created_header = self.env['account.move'].create({
                        'journal_id' : record.company_id.manufacturing_journal_id.id,
                        'date': record.date_finished,
                        'ref' : "Planned Variance Costs",
                        'company_id': record.company_id.id,
                    })
                    id_credit_item = self.env['account.move.line'].with_context(check_move_validity=False).create({
                        'move_id' : id_created_header.id,
                        'account_id': record.product_id.property_stock_production.valuation_out_account_id.id,
                        'product_id': record.product_id.id,
                        'name' : desc_bom,
                        'quantity': record.qty_produced,
                        'product_uom_id': record.product_uom_id.id,
                        'credit': delta,
                        'debit': 0.0,
                    })
                    id_debit_item= self.env['account.move.line'].with_context(check_move_validity=False).create({
                        'move_id' : id_created_header.id,
                        'account_id': record.company_id.costs_planned_variances_account_id.id,
                        'analytic_account_id' : record.company_id.costs_planned_variances_analytic_account_id.id,
                        'product_id': record.product_id.id,
                        'name' : desc_bom,
                        'quantity': record.qty_produced,
                        'product_uom_id': record.product_uom_id.id,
                        'credit': 0.0,
                        'debit': delta,
                    })
                    id_created_header.post()
        return True
        
    @api.multi
    def _variance_postings(self):
        for record in self:
             #production labour/machine variance costs posting
             lab_actual_amount = record.lab_mac_cost
             lab_planned_amount = record.cur_std_lab_cost * record.qty_produced
             delta = lab_actual_amount - lab_planned_amount
             desc_bom = str(record.name)
             if delta < 0.0:
                    id_created_header = self.env['account.move'].create({
                        'journal_id' : record.company_id.manufacturing_journal_id.id,
                        'date': record.date_finished,
                        'ref' : "Labour/Machine Variances",
                        'company_id': record.company_id.id,
                    })
                    id_credit_item = self.env['account.move.line'].with_context(check_move_validity=False).create({
                        'move_id' : id_created_header.id,
                        'account_id': record.company_id.costs_labour_variances_account_id.id,
                        'analytic_account_id' : record.company_id.costs_labour_variances_analytic_account_id.id,
                        'product_id': record.product_id.id,
                        'name' : desc_bom,
                        'quantity': record.qty_produced,
                        'product_uom_id': record.product_uom_id.id,
                        'credit': - delta,
                        'debit': 0.0,
                    })
                    id_debit_item= self.env['account.move.line'].with_context(check_move_validity=False).create({
                        'move_id' : id_created_header.id,
                        'account_id': record.product_id.property_stock_production.valuation_out_account_id.id,
                        'product_id': record.product_id.id,
                        'name' : desc_bom,
                        'quantity': record.qty_produced,
                        'product_uom_id': record.product_uom_id.id,
                        'credit': 0.0,
                        'debit': - delta,
                    })
                    id_created_header.post()
             elif delta > 0.0:
                    id_created_header = self.env['account.move'].create({
                        'journal_id' : record.company_id.manufacturing_journal_id.id,
                        'date': record.date_finished,
                        'ref' : "Labour/Machine Variances",
                        'company_id': record.company_id.id,
                    })
                    id_credit_item = self.env['account.move.line'].with_context(check_move_validity=False).create({
                        'move_id' : id_created_header.id,
                        'account_id': record.product_id.property_stock_production.valuation_out_account_id.id,
                        'product_id': record.product_id.id,
                        'name' : desc_bom,
                        'quantity': record.qty_produced,
                        'product_uom_id': record.product_uom_id.id,
                        'credit': delta,
                        'debit': 0.0,
                    })
                    id_debit_item= self.env['account.move.line'].with_context(check_move_validity=False).create({
                        'move_id' : id_created_header.id,
                        'account_id': record.company_id.costs_labour_variances_account_id.id,
                        'analytic_account_id' : record.company_id.costs_labour_variances_analytic_account_id.id,
                        'product_id': record.product_id.id,
                        'name' : desc_bom,
                        'quantity': record.qty_produced,
                        'product_uom_id': record.product_uom_id.id,
                        'credit': 0.0,
                        'debit': delta,
                    })
                    id_created_header.post()
        for record in self:
             # production material and by product variance costs posting
             mat_actual_amount = record.mat_cost
             mat_planned_amount = record.cur_std_mat_cost * record.qty_produced
             delta = mat_actual_amount - mat_planned_amount - record.by_product_amount
             desc_bom = str(record.name) 
             if delta < 0.0:
                    id_created_header = self.env['account.move'].create({
                        'journal_id' : record.company_id.manufacturing_journal_id.id,
                        'date': record.date_finished,
                        'ref' : "Material and By Products Variances",
                        'company_id': record.company_id.id,
                    })
                    id_credit_item = self.env['account.move.line'].with_context(check_move_validity=False).create({
                        'move_id' : id_created_header.id,
                        'account_id': record.company_id.costs_material_variances_account_id.id,
                        'analytic_account_id' : record.company_id.costs_material_variances_analytic_account_id.id,
                        'product_id': record.product_id.id,
                        'name' : desc_bom,
                        'quantity': record.qty_produced,
                        'product_uom_id': record.product_uom_id.id,
                        'credit': - delta,
                        'debit': 0.0,
                    })
                    id_debit_item= self.env['account.move.line'].with_context(check_move_validity=False).create({
                        'move_id' : id_created_header.id,
                        'account_id': record.product_id.property_stock_production.valuation_out_account_id.id,
                        'product_id': record.product_id.id,
                        'name' : desc_bom,
                        'quantity': record.qty_produced,
                        'product_uom_id': record.product_uom_id.id,
                        'credit': 0.0,
                        'debit': - delta,
                    })
                    id_created_header.post()
             elif delta > 0.0:
                    id_created_header = self.env['account.move'].create({
                        'journal_id' : record.company_id.manufacturing_journal_id.id,
                        'date': record.date_finished,
                        'ref' : "Material and By Products Variances",
                        'company_id': record.company_id.id,
                    })
                    id_credit_item = self.env['account.move.line'].with_context(check_move_validity=False).create({
                        'move_id' : id_created_header.id,
                        'account_id': record.product_id.property_stock_production.valuation_out_account_id.id,
                        'product_id': record.product_id.id,
                        'name' : desc_bom,
                        'quantity': record.qty_produced,
                        'product_uom_id': record.product_uom_id.id,
                        'credit': delta,
                        'debit': 0.0,
                    })
                    id_debit_item= self.env['account.move.line'].with_context(check_move_validity=False).create({
                        'move_id' : id_created_header.id,
                        'account_id': record.company_id.costs_material_variances_account_id.id,
                        'analytic_account_id' : record.company_id.costs_material_variances_analytic_account_id.id,
                        'product_id': record.product_id.id,
                        'name' : desc_bom,
                        'quantity': record.qty_produced,
                        'product_uom_id': record.product_uom_id.id,
                        'credit': 0.0,
                        'debit': delta,
                    })
                    id_created_header.post()
        return True