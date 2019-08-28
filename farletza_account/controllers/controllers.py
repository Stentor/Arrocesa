# -*- coding: utf-8 -*-
from odoo import http

# class FarlexaAccount(http.Controller):
#     @http.route('/farlexa_account/farlexa_account/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/farlexa_account/farlexa_account/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('farlexa_account.listing', {
#             'root': '/farlexa_account/farlexa_account',
#             'objects': http.request.env['farlexa_account.farlexa_account'].search([]),
#         })

#     @http.route('/farlexa_account/farlexa_account/objects/<model("farlexa_account.farlexa_account"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('farlexa_account.object', {
#             'object': obj
#         })