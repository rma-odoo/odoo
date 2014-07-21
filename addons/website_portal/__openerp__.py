# -*- coding: utf-8 -*-
{
    'name': "website_portal",
    'summary': "website portal",
    'description': "Display portal in website",
    'author': 'OpenERP SA',
    'website': "http://www.yourcompany.com",
    'category': 'Website',
    'version': '1.0',
    'depends': ["base", "portal", "website", "web"],
    'data': ["views/website_portal.xml", "data/website_portal_data.xml"],
    'auto_install': False,
}
