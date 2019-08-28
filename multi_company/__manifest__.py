# -*- coding: utf-8 -*-
{
    'name': "Multi Company Data",

    'summary': """
        Modulo para replicar Informacion entre compañías.
        """,

    'description': """
        Este modulo se emplea para duplicar informacion a nivel de multicompañias
        debido que hay informacion de compañias anteriores que puede ser reutilizada
        en las compañias nuevas a implementar.
    """,

    'author': "Opa Consulting",
    'website': "http://www.opa-consulting.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Settings',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_company_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],

    'installable': True,
    'auto_install': True,
}