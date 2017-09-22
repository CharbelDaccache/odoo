{
    'name': 'Crop-R invoice',
    'category': 'Hidden',
    'description': """
Store Crop-R invoice token and show it as a URL on invoice view. And Crop-R order number
""",
    'version': '1.7',
    'depends': ['base','odoo2exact_module'],
    'author': 'Dacom',
    'website': 'https://www.dacom.nl',
    'data': [
        'views/invoice_view.xml',
    ],
    'qweb': [
        'static/src/xml/custom-widget.xml'
    ],
    'auto_install': False,
    'instalable': True,
}
