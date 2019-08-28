# -*- coding: utf-8 -*-
{
    'name': "Account Account Farletza Data",

    'summary': """  """,

    'description': """
        Importar el plan contable de la compania Farlteza
    """,

    'author': "Opa-Consulting",
    'website': "www.opa-consulting.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account'],

    # always loaded
    'data': [
        'data/category.xml',
        'data/account.xml'
        
    ],
    'installable': True,
}