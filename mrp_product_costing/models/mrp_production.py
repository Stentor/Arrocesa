# -*- coding: utf-8 -*-

import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, _


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    prod_std_cost = fields.Float(digits=dp.get_precision('Product Price'), string='Standard Cost', compute='calculate_planned_costs')
    cur_std_mat_cost = fields.Float(digits=dp.get_precision('Product Price'), string='Planned Material Cost', compute='calculate_planned_costs')
    cur_std_lab_cost = fields.Float(digits=dp.get_precision('Product Price'), string='Planned Labour/Machine Cost', compute='calculate_planned_costs')
    cur_std_cost = fields.Float(digits=dp.get_precision('Product Price'), string='Planned Cost', compute='calculate_planned_costs')
    
    mat_cost = fields.Float(digits=dp.get_precision('Product Price'), string='Actual Material Cost', compute='calculate_material_cost')
    mat_cost_unit = fields.Float(digits=dp.get_precision('Product Price'), string='Actual Material Cost per Unit', compute='calculate_material_cost')
    lab_mac_cost = fields.Float(digits=dp.get_precision('Product Price'), string='Actual Labour/Machine Cost', compute='calculate_labour_cost')
    lab_mac_cost_unit = fields.Float(digits=dp.get_precision('Product Price'), string=' Actual Labour/Machine Cost per unit', compute='calculate_labour_cost')
    fixed_cost = fields.Float(digits=dp.get_precision('Product Price'), string='Actual Fixed Cost (at standard times)', compute='calculate_fixed_cost')
    by_product_amount = fields.Float(digits=dp.get_precision('Product Price'), string='By Product Amount', compute='calculate_by_product_amount')
    
    fixed_ovh_lab_mac_cost = fields.Float(digits=dp.get_precision('Product Price'), string='Fixed OVH Labour/Machine Cost', 
        compute='calculate_overhead_cost')
    variable_ovh_lab_mac_cost = fields.Float(digits=dp.get_precision('Product Price'), string='Variable OVH Labour/Machine Cost', 
        compute='calculate_overhead_cost')
    fixed_ovh_mat_cost = fields.Float(digits=dp.get_precision('Product Price'), string='Fixed OVH Material Cost', compute='calculate_overhead_cost')
    variable_ovh_mat_cost = fields.Float(digits=dp.get_precision('Product Price'), string='Variable OVH Material Cost', compute='calculate_overhead_cost')
    
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id.id) 


    @api.multi
    def calculate_planned_costs(self):
        costmat = 0.0
        costlabmac = 0.0
        for production in self:
            product_id = production.product_id
            bom_id = production.bom_id
            result, result2 = bom_id.explode(product_id, 1)
            for sbom, sbom_data in result2:
                costmat += sbom.product_id.standard_price * sbom_data['qty']
            if bom_id.routing_id:
                for order in bom_id.routing_id.operation_ids:
                    costlabmac += (order.time_cycle/60) * order.workcenter_id.costs_hour
            production.prod_std_cost = production.product_id.standard_price
            production.cur_std_mat_cost = costmat
            production.cur_std_lab_cost = costlabmac
            production.cur_std_cost = costmat + costlabmac
        return True


    @api.multi
    def calculate_material_cost(self):
        matprice = 0.0
        matamount = 0.0
        planned_cost = False
        for production in self:
            for move in production.move_raw_ids:
                if not move.is_done:
                    planned_cost = True
            if not planned_cost:
                for move in production.move_raw_ids:
                    if move.state == 'done':
                        matamount += move.product_id.standard_price * move.product_uom_qty
                qty_produced = 0.0
                if production.qty_produced == 0.0:
                    qty_produced = production.product_qty
                else:
                    qty_produced = production.qty_produced
                matprice = matamount / qty_produced
            production.mat_cost = matamount
            production.mat_cost_unit = matprice 
        return True


    @api.multi
    def calculate_labour_cost(self):
        labmacprice = 0.0
        labmacamount = 0.0
        planned_cost = False
        for production in self:
            if production.state == "cancel" or production.state == "confirmed" or production.state == "planned":
                    planned_cost = True  
            if not planned_cost:
                workorders = production.workorder_ids  
                for wo in workorders:
                    labmacamount += (wo.duration) * wo.workcenter_id.costs_hour / 60 
                    #for time in wo.	time_ids:
                    #    labmacamount += (time.duration) * wo.workcenter_id.costs_hour / 60 
                qty_produced = 0.0
                if production.qty_produced == 0.0:
                    qty_produced = production.product_qty
                else:
                    qty_produced = production.qty_produced
                labmacprice = labmacamount / qty_produced
            production.lab_mac_cost = labmacamount 
            production.lab_mac_cost_unit = labmacprice
        return True
        
        
    @api.multi
    def calculate_fixed_cost(self):
        fixedamount = 0.0
        planned_cost = False
        for production in self:
            if production.state == "cancel" or production.state == "confirmed" or production.state == "planned":
                    planned_cost = True  
            if not planned_cost:
                workorders = production.workorder_ids  
                for wo in workorders:
                    for time in wo.time_ids:
                        fixedamount += (wo.workcenter_id.time_stop + wo.workcenter_id.time_start) * wo.workcenter_id.costs_hour_fixed / 60
            production.fixed_cost = fixedamount 
        return True
        

    @api.multi
    def calculate_overhead_cost(self):
        fixedlabmaccost = 0.0
        variablelabmaccost = 0.0
        planned_cost = False
        for production in self:
            if production.state == "cancel" or production.state == "confirmed" or production.state == "planned":
                    planned_cost = True  
            if not planned_cost:
                workorders = production.workorder_ids  
                for wo in workorders:
                    fixedlabmaccost += (wo.duration * wo.workcenter_id.costs_hour / 60) * (wo.workcenter_id.costs_overheads_fixed_percentage / 100)
                    variablelabmaccost += (wo.duration * wo.workcenter_id.costs_hour / 60) * (wo.workcenter_id.costs_overheads_variable_percentage / 100)
            production.fixed_ovh_lab_mac_cost = fixedlabmaccost
            production.variable_ovh_lab_mac_cost = variablelabmaccost
            production.fixed_ovh_mat_cost = production.mat_cost * (production.bom_id.costs_overheads_fixed_percentage / 100)
            production.variable_ovh_mat_cost = production.mat_cost * (production.bom_id.costs_overheads_variable_percentage / 100)
        return True
        
        
    @api.multi
    def calculate_by_product_amount(self):
        receipt_amount = 0.0
        for production in self:
            for move in production.move_finished_ids:
                if move.state == 'done':
                    receipt_amount += move.product_id.standard_price * move.product_uom_qty
            production.by_product_amount = receipt_amount - production.prod_std_cost * production.qty_produced
        return True