# -*- coding: utf-8 -*-
from odoo import http

# class L10nEcRemision(http.Controller):
#     @http.route('/l10n_ec_remision/l10n_ec_remision/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_ec_remision/l10n_ec_remision/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_ec_remision.listing', {
#             'root': '/l10n_ec_remision/l10n_ec_remision',
#             'objects': http.request.env['l10n_ec_remision.l10n_ec_remision'].search([]),
#         })

#     @http.route('/l10n_ec_remision/l10n_ec_remision/objects/<model("l10n_ec_remision.l10n_ec_remision"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_ec_remision.object', {
#             'object': obj
#         })