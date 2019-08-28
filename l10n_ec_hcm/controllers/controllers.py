# -*- coding: utf-8 -*-
from odoo import http

# class L10nEcHcm(http.Controller):
#     @http.route('/l10n_ec_hcm/l10n_ec_hcm/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_ec_hcm/l10n_ec_hcm/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_ec_hcm.listing', {
#             'root': '/l10n_ec_hcm/l10n_ec_hcm',
#             'objects': http.request.env['l10n_ec_hcm.l10n_ec_hcm'].search([]),
#         })

#     @http.route('/l10n_ec_hcm/l10n_ec_hcm/objects/<model("l10n_ec_hcm.l10n_ec_hcm"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_ec_hcm.object', {
#             'object': obj
#         })