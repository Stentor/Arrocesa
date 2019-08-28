# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'


    @api.multi
    @api.constrains('state')
    def get_actual_posting(self):
        for record in self:
            if record.state == 'done':
                record._direct_cost_postings()
        return True
            

    @api.multi
    def _direct_cost_postings(self):
        # production direct costs posting
        for record in self:
            desc_wo = record.production_id.name + '-' + record.workcenter_id.name + '-' + record.name
            con_date_end = self.env['mrp.workcenter.productivity'].search([('workorder_id', '=', record.id)])[-1].date_end
            id_created_header = self.env['account.move'].create({
                'journal_id' : record.production_id.company_id.manufacturing_journal_id.id,
                'date': con_date_end,
                'ref' : "Labour/Machine direct costs",
                'company_id': record.workcenter_id.company_id.id,
            })
            id_credit_item = self.env['account.move.line'].with_context(check_move_validity=False).create({
                'move_id' : id_created_header.id,
                'account_id': record.workcenter_id.costs_dir_account_id.id,
                'analytic_account_id' : record.workcenter_id.costs_dir_analytic_account_id.id,
                'product_id': record.production_id.product_id.id,
                'name' : desc_wo,
                'quantity': record.qty_produced,
                'product_uom_id': record.production_id.product_uom_id.id,
                'credit': (record.duration) * record.workcenter_id.costs_hour / 60,
                'debit': 0.0,
            })
            id_debit_item= self.env['account.move.line'].with_context(check_move_validity=False).create({
                'move_id' : id_created_header.id,
                'account_id': record.production_id.product_id.property_stock_production.valuation_in_account_id.id,
                'product_id': record.production_id.product_id.id,
                'name' : desc_wo,
                'quantity': record.qty_produced,
                'product_uom_id': record.production_id.product_uom_id.id,
                'credit': 0.0,
                'debit': (record.duration) * record.workcenter_id.costs_hour / 60,
            })
            id_created_header.post()
        return True
