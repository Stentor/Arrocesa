# -*- coding: utf-8 -*-
# Copyright (c) Open Value All Rights Reserved                     
# License LGPL-3 or later (https://www.gnu.org/licenses/).

{
    'name': 'Work Center Cost Parameters',
    'summary': 'Cost parameters on work center master data',
    'version': '12.0.1.0.0',
    'category': 'Manufacturing',
    "website": 'linkedin.com/in/openvalue-consulting-472448176',
    'author': "Open Value",
    'support': 'opentechvalue@gmail.com',
    'license': "LGPL-3",
    'price': 00.00,
    'currency': 'EUR',
    'depends': [
        'mrp', 
        'account'
    ],
    'data': [
        'views/mrp_workcenter_view.xml'
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
    'images': ['static/description/banner.png'],
}
