# -*- coding: utf-8 -*-
{
    'name': "Blueprint Arrocesa",
    'summary': """
        Instalacion modulos arrocesa + datos iniciales""",

    'description': """
        Implementacion Arrocesa acorde al blueprint
    """,
    'author': "OPA-Consulting",
    'website': "http://www.opa-consulting.com",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base', 
        'account_accountant',
        'stock',
        'uom',
        'purchase',
        'mrp',
        'mrp_mps',
        'mrp_workorder',
        'arrocesa_balanzas',
        'hr_payroll_account',
        'l10n_ec_nomina',
        'l10n_ec_einvoice'
        ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/product.category.csv',
        'data/stock.warehouse.csv',
        'data/uom.uom.csv',
        'data/product.product.csv',
        #'data/stock.route.product.csv',
        'data/mrp.workcenter.csv',
        'data/mrp.routing.csv',
        'data/mrp.routing.workcenter.csv',
        'data/category.xml',
        'data/account.xml',
        'data/res.bank.csv',
        'data/hr.department.csv',
        'data/hr.job.csv',
        'data/hr.employee.csv',
        'data/cargas/hr.employee.csv',
        #'data/contacts/hr.employee.csv',
        #'data/res.partner.csv',
        'data/hr.rules.xml',
        'views/config.xml',
        'views/materia_prima.xml'
    ],

}