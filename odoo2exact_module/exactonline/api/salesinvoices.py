# vim: set ts=8 sw=4 sts=4 et ai tw=79:
"""
Helper for salesinvoice resources.

"""
from .manager import Manager


class SalesInvoices(Manager):
    resource = 'salesinvoice/SalesInvoices'

    def get(self, **kwargs):
        sales_invoice_dict = super(SalesInvoices, self).get(**kwargs)
        try:
            uri = sales_invoice_dict[u'SalesInvoiceLines'][u'__deferred']['uri']
        except KeyError:
            # Perhaps there is a 'select' filter.
            pass
        else:
            sales_invoicelines_dict = self._api.restv1('GET', str(uri))
            sales_invoice_dict[u'SalesInvoiceLines'] = sales_invoicelines_dict
        return sales_invoice_dict


    def filter(self, sales_invoice_number=None, sales_invoice_number__in=None, **kwargs):
        if sales_invoice_number is not None:
            #allard = self.get(filter='InvoiceNumber eq {0}'.format(sales_invoice_number))
            #allard2 = self.get(filter='InvoiceNumber eq 17700001')
            
            # assert 'expand' not in kwargs
            kwargs['expand'] = 'SalesInvoiceLines'
            #kwargs['select'] = ('SalesInvoiceLines/LineNumber,'
            #                    'SalesInvoiceLines/VATAmountDC')
        return super(SalesInvoices, self).filter(**kwargs)

    
    def _remote_sales_invoice_number(self, sales_invoice_number):
        return u"'%s'" % (sales_invoice_number.replace("'", "''"),)
