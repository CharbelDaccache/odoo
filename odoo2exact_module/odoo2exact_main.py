import sys
import logging
from flask import Flask, request
from odoo_exact_controller import *

app = Flask(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
_logger = logging.getLogger(__name__)


# flask entry point
@app.route("/callback")
def get_code():
    code = request.args.get('code', None)
    if code is None:
        return "geen code opgegeven!"
    else:
        exact = Exact()
        exact.exact_request_token(code)
        return "{{ \"code\": {0} }}".format(code)


# this app can be started in either webserver mode or run as a standalone application
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "web":
            app.run('127.0.0.1',5000)  #172.17.0.8 is the IP of the odoo docker container, make sure the callback url redirects to here.
        elif sys.argv[1] == "setup":
            _logger.info("trying to generate initial url")
            exact = Exact()
            auth_url = exact.api.create_auth_request_url()
            _logger.info("make sure the values in the transient section of config.ini are empty")
            _logger.info("make sure a second instance of this program is started in web-mode")
            _logger.info("then please open a webbrowser and go to the following url: {0}".format(auth_url))
            _logger.info("after that the API should work.")
        elif sys.argv[1] == "getandsetinvoicenumber" and sys.argv[2].isdigit():
            _logger.info("trying to get and set invoice number for division {0}".format(sys.argv[2]))
            odoo = Odoo()
            exact = Exact()
            exact.set_division_code(sys.argv[2])

            odoo_invoices_without_number = odoo.get_invoices_without_invoice_number()
            for odoo_invoice in odoo_invoices_without_number:
                exact_order_number = odoo_invoice.get("exact_order_number", None)
                if exact_order_number:
                    # in exact ophalen InvoiceNumber a.d.h.v. OrderNumber where Status = 50 (=verwerkt)
                    exact_invoice_number = exact.get_invoice_number(exact_order_number)
                    if exact_invoice_number:
                        _logger.info("found exact_invoice_number {0} for order_number {1}".format(exact_invoice_number, exact_order_number))
                        odoo.set_exact_invoice_number(exact_order_number, exact_invoice_number)

        elif sys.argv[1].isdigit():
            _logger.info('trying to start odoo')
            odoo = Odoo()
            _logger.info('trying to start exact')
            exact = Exact()
            exact.set_division_code(sys.argv[1])
            # eerst alle bedrijven toevoegen
            # daarna contactpersonen
            _logger.info('Get companies from ODOO.')
            from_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
            odoo_company_records = odoo.get_odoo_companies(from_date=from_date)

            _logger.info('Import companies to ExactOnline.')
            for odoo_company_record in odoo_company_records:
                is_dfi_active = odoo_company_record.get('dfi_active', False)
                if is_dfi_active:
                    exact_company_record = exact.convert_odoo_company_to_exact_account(odoo, odoo_company_record)
                    exact.create_account(odoo, exact_company_record)
                else:
                    _logger.info('company with id {0} is not active'.format(odoo_company_record.get('id')))

            _logger.info('Companies import finished.')

            _logger.info('Get users from ODOO.')
            from_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
            odoo_user_records = odoo.get_odoo_users_from_date(from_date=from_date)

            _logger.info('Import users to ExactOnline.')
            for odoo_user_record in odoo_user_records:
                parent_id = odoo_user_record.get('parent_id')
                if parent_id:
                    parent_id = parent_id[0]
                    if odoo.company_is_active(parent_id):
                        exact_user_record = exact.convert_odoo_user_to_exact_contact(odoo_user_record)
                        exact.create_contact(exact_user_record)
                    else:
                        _logger.info('parent company for this user {0} is not active'.format(odoo_user_record.get('id')))
                else:
                    _logger.error('error while trying to get parent company id for user {0}'.format(odoo_user_record.get('id')))

            _logger.info('Users import finished.')
        else:
            _logger.info("unknown argument")
    else:
        _logger.warn("no argument given. valid arguments are: web, setup, or a divisioncode")

