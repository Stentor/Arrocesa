# -*- coding: utf-8 -*-
# Copyright (c) Open Value All Rights Reserved 

{
'name': 'Product Costing',
 'summary': 'Product Costing',
 'version': '12.0.1.2.0',
 'category': 'Manufacturing',
  "website": 'linkedin.com/in/openvalue-consulting-472448176',
  'author': "Open Value",
  'support': 'opentechvalue@gmail.com',
  'license': "Other proprietary",
  'price': 200.00,
  'currency': 'EUR',
    "depends": [
        'stock',
        'stock_account',
        'purchase',
        'mrp', 
        'mrp_workcenter_costing',
        'account',
    ],
    "data": [
        'views/mrp_product_costing_parameters.xml',        
        'views/mrp_bom_view.xml',
        'views/mrp_product_costing_view.xml',
        'views/mrp_postings_view.xml'
    ],
  'application': False,
  'installable': True,
  'auto_install': False,
  'images': ['static/description/banner.png'],
}
