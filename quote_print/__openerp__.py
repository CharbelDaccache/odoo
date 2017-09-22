
{
    'name': 'Print quotation',
    'author': 'Odoo',
    'category': 'Website',
    'summary': 'Print quotation same from frontend and backend',
    'version': '9.0',
    'description': """
Print quotation
=========================

        """,
    'depends': ['website_quote','custom_header_footer'],
    'data': [
        'data/quote_custom_header.xml',
        'data/mail_template_data.xml',
        'data/partnership_contact_template.xml',
        'views/quote_print.xml',
        'views/snippets.xml',
        'report/quotation_report.xml',
        'report/sale_order_reports.xml',
        'report/cover_image_report.xml',
    ],
    'demo': [
    ],
    'qweb': [],
    'installable': True,
}
