# -*- coding: utf-8 -*-
{
    'name': 'Reporte Dinardap',
    'version': '10.0.0.1.0',
    'author': 'Opa-Consulting',
    'category': 'Localization',
    'license': 'AGPL-3',
    'complexity': 'normal',
    'data': [
        'data/ote.province.csv',
        'data/ote.canton.csv',
        'data/ote.parroquia.csv',
        'views/dinardap.xml',
        'wizard/wizard.xml',
        'security/ir.model.access.csv'
    ],
    'depends': [
        'base',
        'l10n_ec_partner',
        'l10n_ec_withholding',
        'web',
        'account_reports_followup',
        'sale'
    ]
}
