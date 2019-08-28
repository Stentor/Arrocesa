# -*- coding: utf-8 -*-

from odoo import models, fields, api

class arrocesa_balanza(models.Model):
    _name = 'arrocesa_balanzas.weighting'

    
    barcode=fields.Char('Barcode')
    client_id = fields.Many2one('res.partner')
    in_time = fields.Datetime('In Time')
    out_time = fields.Datetime('Out time')  
    product = fields.Many2one('product.product')
    peso =  fields.Float('Peso')
    sacas = fields.Float('Sacas')
    num = fields.Char('num')
    humedad = fields.Float('humedad')
    peso_especifico = fields.Float('pesoEspecifico')
    granos_partidos = fields.Float('granosPartidos')
    hongos = fields.Float('hongos')
    impureza = fields.Float('impureza')
    yesados = fields.Float('yesados')
    trizados = fields.Float('trizados')
    verdes = fields.Float('verdes')
    rojos = fields.Float('rojos')
    bultos = fields.Float('bultos')
    variedad = fields.Char('variedad')
    comment = fields.Char('comment')
    