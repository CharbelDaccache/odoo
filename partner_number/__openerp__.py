{
    'name': 'Partner Number',
    'category': 'Hidden',
    'description': """
Store unique Partner Number and show it as a URL on view.
""",
    'version': '3.1',
    'depends': ['base','odoo2exact_module'],
    'author': 'CaretCS',
    'website': 'http://www.caretcs.com',
    'data': [
        'views/partner_view.xml',
    ],
    'qweb': [
        'static/src/xml/custom-widget.xml'
    ],
    'auto_install': False,
    'instalable': True,
}
