# -*- coding: utf-8 -*-
from odoo import http

# class L10nEcIce(http.Controller):
#     @http.route('/l10n_ec_ice/l10n_ec_ice/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_ec_ice/l10n_ec_ice/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_ec_ice.listing', {
#             'root': '/l10n_ec_ice/l10n_ec_ice',
#             'objects': http.request.env['l10n_ec_ice.l10n_ec_ice'].search([]),
#         })

#     @http.route('/l10n_ec_ice/l10n_ec_ice/objects/<model("l10n_ec_ice.l10n_ec_ice"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_ec_ice.object', {
#             'object': obj
#         })