# -*- coding: utf-8 -*-

{
    'name': 'Custom Payment Acquirer',
    'category': 'Hidden',
    'summary': 'Payment Acquirer: Custom Implementation',
    'version': '1.0',
    'description': """Custom Payment Acquirer""",
    'author': 'OpenERP SA',
    'depends': ['payment'],
    'data': [
        'views/custom.xml',
        'views/templates.xml',
        'data/custom.xml',
    ],
    'installable': True,
}
