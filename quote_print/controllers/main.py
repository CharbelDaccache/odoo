# -*- coding: utf-8 -*-

import re

from openerp import http
from openerp.http import request
from openerp.addons.website_quote.controllers.main import sale_quote


class customSaleQuote(sale_quote):

    @http.route("/quote/<int:order_id>/<token>", type='http', auth="public", website=True)
    def view(self, order_id, pdf=None, token=None, message=False, **post):
        result = super(customSaleQuote, self).view(order_id, pdf=pdf, token=token, message=message, **post)

        if token:
            order = request.env['sale.order'].sudo().search([('id', '=', order_id), ('access_token', '=', token)])
        else:
            order = request.env['sale.order'].search([('id', '=', order_id)])

        if not order:
            return result

        if hasattr(result, 'render'):
            renderedResult = result.render()
        elif hasattr(result, 'replace'):
            renderedResult = result
        else:
            return result

        variables = re.findall(r'\${custom:.*?}', renderedResult)
        if not variables:
            return result

        object = order
        for variable in variables:
            value = eval(variable[9:-1])
            if isinstance(value, (int, float, long, list, tuple, dict)):
                try:
                    # There are uncertain possible data. So making generic and ignore issue.
                    try:
                        value = str(value).encode("utf-8").decode("utf-8")
                    except:
                        value = str(value).decode("utf-8")
                except:
                    print 'Invalid Data'
                    value = u''
            renderedResult = renderedResult.replace(variable, value.encode('utf-8'))

        return renderedResult
