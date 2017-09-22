# -*- coding: utf-8 -*-

'''
    opzoeken form view names in ir_model_data :
    voorbeeld: select * from ir_model_data where name ilike '%view%journal%';
'''

from openerp import api, fields, models, _
from openerp.exceptions import Warning
from openerp import http
from odoo_exact_controller import Odoo, Exact, export_invoice_to_exact
import logging
_logger = logging.getLogger(__name__)

class exact_auth(http.Controller):
    @http.route('/exact/get-code/', auth='public')
    def get_code(self, **kw):
        _logger.info("requested get_code")
        _logger.info("kwargs={0}".format(kw))
        code = kw.get('code', None)
        if code is None:
            return "geen code opgegeven!"
        else:
            exact = Exact()
            if exact:
                _logger.info("exact object exists")
            else:
                _logger.info("exact object not exists")
            try:
                exact.exact_request_token(code)
            except Exception as e:
                _logger.info("fout bij request token: msg={0}, args={1}".format(e.message, e.args))

            return "{{ \"code\": {0} }}".format(code)

    @http.route('/exact/setup/', auth='public')
    def do_setup(self, **kw):
        exact = Exact()
        if exact:
            _logger.info("exact object exists")
        else:
            _logger.info("exact object not exists")
        try:
            auth_url = exact.api.create_auth_request_url()
            _logger.info("auth_url result = {0}".format(auth_url))
        except Exception as e:
            _logger.info("fout bij genereren request url: {0}".format(e.message))
        # "make sure the values in the transient section of config.ini are empty"
        return "please open a webbrowser and go to {0}\nafter that the API should work.".format(auth_url)


    @http.route('/exact/log/dacom', auth='public')
    def get_dacom_log(self, **kw):
        try:
            dacom_log = '/var/log/odoo2exact_job_dacom.log'
            f = open(dacom_log, 'r')
            log_file_contents =  f.read()
            f.close()
        except Exception as e:
            _logger.info("fout bij ophalen dacom-logfile: {0}".format(e.message))
        return "inhoud dacom-logfile:\n\n{0}".format(log_file_contents)


    @http.route('/exact/log/dfi', auth='public')
    def get_dfi_log(self, **kw):
        try:
            dfi_log = '/var/log/odoo2exact_job_dfi.log'
            f = open(dfi_log, 'r')
            log_file_contents =  f.read()
            f.close()
        except Exception as e:
            _logger.info("fout bij ophalen dfi-logfile: {0}".format(e.message))
        return "inhoud dfi-logfile:\n\n{0}".format(log_file_contents)


    @http.route('/exact/set-invoice-number/', auth='public')
    def set_invoice_number(self, **kw):
        _logger.info("requested set_invoice_number")
        _logger.info("kwargs={0}".format(kw))
        invoice_number = kw.get('invoice_number', None)
        if invoice_number is None:
            return "geen invoice_number opgegeven!"
        else:
            return "{{ \"invoice_number\": {0} }}".format(invoice_number)


class account_invoice(models.Model):
    _inherit = "account.invoice"
    _name = "account.invoice"

    name = fields.Char(string="Title", required=False)

    exact_order_number = fields.Char(string='Exact ordernumber', copy=False)
    exact_invoice_number = fields.Char(string='Exact invoicenumber', copy=False)
    exact_invoice_subject = fields.Char(string='Exact onderwerp/omschrijving', copy=False)

    @api.multi
    def export_exact(self):
       try:
           order_number = export_invoice_to_exact(self.id)
           if order_number and order_number >0:
               raise Warning( _("invoice {0} is met succes geexporteerd naar Exact".format(self.id)))
       except Exception as e:
           raise Warning( _("resultaat: {0} / details: {1}".format(e.message, e.args) ))


class _res_partner(models.Model):
    _inherit = "res.partner"
    _name = "res.partner"

    name = fields.Char(string="Title", required=False)

    dfi_active = fields.Boolean(string='DFI active', copy=False)

    # exact_order_number = fields.Char(string='Exact ordernumber', copy=False)
    #exact_invoice_number = fields.Char(string='Exact invoicenumber', copy=False)

    # nieuw record
    #def create(self, cr, uid, vals, context=None):
    #@api.model
    #def create(self, vals):
    #    raise Warning( _("dit is de create functie van res.partner van odoo"))
    #    # let op, na een raise Warning wordt geen code meer uitgevoerd
    #    res = super(_res_partner, self).create(cr, uid, vals, context=context)
    #    #Your code goes here
    #    return res

    ## update record
    #@api.multi
    #def write(self, vals):
    #    raise Warning( _("dit is de update functie van res.partner van odoo"))
    #    vals['first_name'] = '37'
    #    #return super(models.Model, self).write(vals)
    #    res = super(_res_partner, self).write(vals)
    #    return res

class _account_payment_term(models.Model):
    _inherit = "account.payment.term"
    _name = "account.payment.term"

    name = fields.Char(string="Title", required=False)

    exact_code = fields.Char(string='Exact code', copy=False)


class _res_company(models.Model):
    _inherit = "res.company"
    _name = "res.company"

    name = fields.Char(string="Title", required=False)

    exact_division_code = fields.Char(string='Exact division code', copy=False)


class _account_journal(models.Model):
    _inherit = "account.journal"
    _name = "account.journal"

    name = fields.Char(string="Title", required=False)

    exact_code = fields.Char(string='Exact code', copy=False)
