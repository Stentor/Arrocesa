# -*- coding: utf-8 -*-
from odoo import http
from lxml import etree
from lxml import objectify

class ArrocesaBalanzas(http.Controller):
    @http.route('/balanzas/input/', auth='user', methods=["POST"], csrf=False)
    def index(self, **kw):
        root=etree.fromstring(http.request.httprequest.data)
        analysis = root.find('analisis')
        data = {
            'barcode': root.find('barcode').text,
            #'client_id': root.find('clientId').text,
            'in_time': root.find('inTime').text,
            'out_time': root.find('outTime').text,
            #'product': root.find('product').text,
            'peso': root.find('peso').text,
            'sacas': root.find('sacas').text,
            'num': analysis.find('num').text,
            'humedad': analysis.find('humedad').text,
            'peso_especifico': analysis.find('pesoEspecifico').text,
            'granos_partidos': analysis.find('granosPartidos').text,
            'hongos': analysis.find('hongos').text,
            'impureza': analysis.find('impureza').text,
            'yesados': analysis.find('yesados').text,
            'trizados': analysis.find('trizados').text,
            'verdes': analysis.find('verdes').text,
            'rojos': analysis.find('rojos').text,
            'bultos': analysis.find('bultos').text,
            'variedad': analysis.find('variedad').text,
            'comment': analysis.find('comment').text,            
        }
        
        record = http.request.env['arrocesa_balanzas.weighting'].sudo().create(data)
        http.request.env.cr.commit()
        return "OK"