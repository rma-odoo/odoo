{
    'name': 'Twitter Wall',
    'category': 'Website',
    'summary': 'Show tweet',
    'version': '1.0',
    'description': """
Display best tweets from hashtag
=====================================

        """,
    'author': 'OpenERP SA',
    'depends': ['website'],
    'data': [
             'views/twitter_wall_backend.xml',
             'views/twitter_wall_conf.xml',
             'views/twitter_wall.xml',
             'security/ir.model.access.csv'
             ],
    'demo': [],
    'qweb': [],
    'installable': True,
}
