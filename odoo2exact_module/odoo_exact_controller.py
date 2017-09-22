# -*- coding: UTF-8 -*-

'''
 let op het is niet mogelijk om contactpersonen te verplaatsen tussen bedrijven in Exact
 work-around is om een nieuwe contactpersoon (met een nieuw id) aan te maken in ODOO
 de oude contactpersoon kan dan op inactief worden gezet.


 ### definities
 cropr   odoo_backend    odoo_fronend    exact_backend   exact_frontend
 farm    res_partner     bedrijf         accounts        klanten
 user    res_partner     persoon         contacts        contactpersonen
 
 in de odoo_backend is een apart veld: company_type waarin de definitie van persoon/bedrijf staat

'''


# toevoegen in productie: from openerp.exceptions import Warning
import settings
import logging
from urllib2 import HTTPError
import sys
from exactonline.api import ExactApi
from exactonline.exceptions import ObjectDoesNotExist
from exactonline.storage import IniStorage
import xmlrpclib
from datetime import datetime, timedelta
import pytz

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
_logger = logging.getLogger(__name__)


def is_valid_tld(emailaddress):
    is_valid = False

    if emailaddress:
        space_start_idx = emailaddress.rfind(' ')
        tld_start_idx = emailaddress.rfind('.')
        if space_start_idx == -1 and tld_start_idx > -1:
            tld_start_idx += 1
            is_valid = emailaddress[tld_start_idx:].isalpha()

    return is_valid




class Exact:
    def __init__(self):
        self.storage = IniStorage(settings.exact_config_file)
        self.api = ExactApi(storage=self.storage)
        self.default_payment_condition_sales_days = settings.exact_default_payment_condition_sales_days
        self.invoice_types = {'out_invoice': 8020, 'out_refund': 8021}
        if len(self.storage.get_code()) > 0:
            if len(self.api.restv1('GET', 'financial/GLAccounts?$filter=Code%20eq%20\'{0}\''.format(settings.exact_debiteuren_rekening))) == 1:
                self.default_debiteuren_rekening_uuid = self.api.restv1('GET', 'financial/GLAccounts?$filter=Code%20eq%20\'{0}\''.format(settings.exact_debiteuren_rekening))[0].get('ID')
            else: exit("no debiteurenrekening with code {0} found".format(settings.exact_debiteuren_rekening))

    def set_division_code(self, div_code):
        self.storage.set_division(div_code)

    def exact_request_token(self, code):
        self.api.request_token(code)

    def get_accountguid_from_odoo_id(self, odoo_id):
        relation = None
        try:
            relation = self.api.relations.get(relation_code=str(odoo_id))
        except ObjectDoesNotExist:
            _logger.warn("parent company id does not exist {0}".format(odoo_id))
            pass

        if relation:
            return relation.get('ID', None)

    # in exact ophalen InvoiceNumber a.d.h.v. OrderNumber where Status = 50 (=verwerkt)
    def get_invoice_number(self, order_number):
        invoice_number = None
        try:
            exact_invoice = self.api.salesinvoices.filter(filter="Status eq 50 and OrderNumber eq %s" % (order_number,))
            if len(exact_invoice)==1:
                invoice_number = exact_invoice[0].get("InvoiceNumber", None)
        except ObjectDoesNotExist:
            _logger.warn("no invoice found with order_number {0}".format(order_number))
            pass
        return invoice_number


    def get_all_relations(self):
        rels = []
        for relation in self.api.relations.all():
            relation_guid = relation.get('ID')
            relation_name = relation.get('Name')
            relation_code = relation.get('Code')
            # filter the suppliers away. (suppliers are relations starting with code 700000)
            if int(relation_code) < 700000:
                _logger.info("processing user %s" % (relation_name,))
                rels.append({relation_guid: {"name": relation_name}})
            else:
                _logger.info("not processing user %s because this is a supplier" % (relation_name,))
        return rels


    def get_relations_with_invoices(self):
        rels_with_invoices = []
        for relation in self.api.relations.all():
            relation_guid = relation.get('ID')
            relation_name = relation.get('Name')
            relation_code = relation.get('Code')
            # filter the suppliers away. (suppliers are relations starting with code 700000)
            if int(relation_code) < 700000:
                _logger.info("processing user %s" % (relation_name,))
                aantal_invoices = len(self.api.salesinvoices.filter(filter="DeliverTo eq guid'%s'" % (relation_guid,)))
                if aantal_invoices > 0:
                    rels_with_invoices.append({relation_guid: {"name": relation_name, "aantal": aantal_invoices}})
            else:
                _logger.info("not processing user %s because this is a supplier" % (relation_name,))
        return rels_with_invoices


    def get_relations_without_invoices(self):
        rels_without_invoices = []
        for relation in self.api.relations.all():
            relation_guid = relation.get('ID')
            relation_name = relation.get('Name')
            relation_code = relation.get('Code')
            # filter the suppliers away. (suppliers are relations starting with code 700000)
            if int(relation_code) < 700000:
                _logger.info("processing user %s" % (relation_name,))
                aantal_invoices = len(self.api.salesinvoices.filter(filter="DeliverTo eq guid'%s'" % (relation_guid,)))
                if aantal_invoices == 0:
                    rels_without_invoices.append({relation_guid: {"name": relation_name}})
            else:
                _logger.info("not processing user %s because this is a supplier" % (relation_name,))
        return rels_without_invoices


    def get_relations_with_transactionlines(self):
        rels_with_transactionlines = []
        for relation in self.api.relations.all():
            relation_guid = relation.get('ID')
            relation_name = relation.get('Name')
            relation_code = relation.get('Code')
            # filter the suppliers away. (suppliers are relations starting with code 700000)
            if int(relation_code) < 700000:
                _logger.info("processing user %s" % (relation_name,))

                aantal_transacties  = len(self.api.restv1('GET', 'financialtransaction/TransactionLines?$filter=Account%20eq%20guid\'{0}\'&$select=ID'.format(relation_guid) ))

                if aantal_transacties > 0:
                    rels_with_transactionlines.append({relation_guid: {"name": relation_name, "aantal": aantal_transacties}})
            else:
                _logger.info("not processing user %s because this is a supplier" % (relation_name,))
        return rels_with_transactionlines


    def get_relations_without_transactionlines(self):
        rels_without_transactionlines = []
        for relation in self.api.relations.all():
            relation_guid = relation.get('ID')
            relation_name = relation.get('Name')
            relation_code = relation.get('Code')
            # filter the suppliers away. (suppliers are relations starting with code 700000)
            if int(relation_code) < 700000:
                _logger.info("processing user %s" % (relation_name,))

                aantal_transacties  = len(self.api.restv1('GET', 'financialtransaction/TransactionLines?$filter=Account%20eq%20guid\'{0}\'&$select=ID'.format(relation_guid) ))

                if aantal_transacties == 0:
                    rels_without_transactionlines.append({relation_guid: {"name": relation_name}})
            else:
                _logger.info("not processing user %s because this is a supplier" % (relation_name,))
        return rels_without_transactionlines


    def get_langcode_from_odoo_lang(self, odoo_lang_code):
        # in odoo is alleen en_US of nl_NL geconfigureerd: lang in odoo = en_US of nl_NL
        exact_lang_code = 'EN'
        if odoo_lang_code == 'nl_BE':
            exact_lang_code = 'NL'
        elif odoo_lang_code == 'nl_NL':
            exact_lang_code = 'NL'
        return exact_lang_code

    # contacts = crm/Contacts
    def create_contact(self, record):
        contact_id = record.get('SocialSecurityNumber', None)
        if contact_id:
            existing_contact = None
            try:
                existing_contact = self.api.contacts.filter(filter="SocialSecurityNumber eq '{0}'".format(contact_id))
            except ObjectDoesNotExist:
                pass

            if not existing_contact:
                try:
                    _logger.info("trying to add contact {0}".format(contact_id))
                    resp = self.api.contacts.create(record)
                except HTTPError as e:
                    _logger.error("contact_code={0}. Fout: {1}. Details: {2}".format(contact_id, e.msg, e.response))
            else:
                _logger.info("contact {0}: (already exists) check if update is necessary...".format(contact_id))
                lidx = existing_contact[0].get('Modified').find('(')
                ridx = existing_contact[0].get('Modified').find(')')
                exact_record_modified_time_str = existing_contact[0].get('Modified')[lidx+1:ridx-3]
                exact_record_modified_time = datetime.utcfromtimestamp(float(exact_record_modified_time_str)) - timedelta(hours=1)
                # if new record modified_time is newer than existing exact contact modified_time,
                # then the exact contact needs to be updated, else it has already been updated

                # existing contact modified is in GMT, new record modified is in UTC
                amsterdam_tz = pytz.timezone('Europe/Amsterdam')
                exact_record_modified_time  = amsterdam_tz.localize(exact_record_modified_time)

                if record.get('Modified', False):
                    new_record_modified_time = datetime.strptime(record.get('Modified'), '%Y-%m-%d %H:%M:%S')

                utc_tz = pytz.timezone('utc')
                new_record_modified_time = utc_tz.localize(new_record_modified_time)

                if new_record_modified_time and new_record_modified_time > exact_record_modified_time:
                    try:
                        _logger.info("trying to update contact {0}".format(contact_id))
                        resp = self.api.contacts.update(existing_contact[0]['ID'], record)
                    except HTTPError as e:
                        _logger.error("contact_code={0}. Fout: {1}. Details: {2}".format(contact_id, e.msg, e.response))
                else:
                    _logger.warn("contact {0} is not going to be updated because the contact in ExactOnline is already newer".format(contact_id))
        else:
            _logger.error("error while trying to get contact id")

    # relations = crm/Accounts
    def create_account(self, odoo, record):
        relation_code = record.get('Code', None)
        if relation_code:
            existing_relation = None
            try:
                existing_relation = self.api.relations.get(relation_code=relation_code)
            except ObjectDoesNotExist:
                pass

            if not existing_relation:
                try:
                    _logger.info("trying to add relation {0}".format(relation_code))
                    resp = self.api.relations.create(record)

                    # also add all the underlying contacts for companies that are synced for the first fime
                    odoo_users_for_company = odoo.get_odoo_users_for_company(company_id=int(relation_code))
                    _logger.info("trying to add all contacts of relation {0}".format(relation_code))
                    for odoo_user_record in odoo_users_for_company:
                        exact_user_record = self.convert_odoo_user_to_exact_contact(odoo_user_record)
                        self.create_contact(exact_user_record)
                except HTTPError as e:
                    _logger.error("relation_code={0}. Fout: {1}. Details: {2}".format(relation_code, e.msg, e.response))
            else:
                _logger.info("relation {0}: (already exists) check if update is necessary...".format(relation_code))

                lidx = existing_relation.get('Modified').find('(')
                ridx = existing_relation.get('Modified').find(')')
                exact_record_modified_time_str = existing_relation.get('Modified')[lidx+1:ridx-3]
                exact_record_modified_time = datetime.utcfromtimestamp(float(exact_record_modified_time_str)) - timedelta(hours=1)
                # if new record modified_time is newer than existing exact contact modified_time,
                # then the exact contact needs to be updated, else it has already been updated

                # existing contact modified is in GMT, new record modified is in UTC
                amsterdam_tz = pytz.timezone('Europe/Amsterdam')
                exact_record_modified_time  = amsterdam_tz.localize(exact_record_modified_time)

                if record.get('Modified', False):
                    new_record_modified_time = datetime.strptime(record.get('Modified'), '%Y-%m-%d %H:%M:%S')
                utc_tz = pytz.timezone('utc')
                new_record_modified_time = utc_tz.localize(new_record_modified_time)

                if new_record_modified_time and new_record_modified_time > exact_record_modified_time:
                    try:
                        _logger.info("trying to update relation {0}".format(relation_code))
                        resp = self.api.relations.update(existing_relation['ID'], record)
                    except HTTPError as e:
                        _logger.error("relation={0}. Fout: {1}. Details: {2}".format(relation_code, e.msg, e.response))
                else:
                    _logger.info("relation {0} is not going to be updated because the contact in ExactOnline is already newer".format(relation_code))
        else:
            _logger.error("fout bij ophalen relation code")

    def try_make_shorter_name(self, long_name):
        try:
            _logger.info("trying to make shorter name for company {0}".format(long_name))
            shorter_name = long_name

            if 'Agrarische' in long_name:
                shorter_name = long_name.replace('Agrarische', 'Agr.')
            if 'Maatschap' in long_name:
                shorter_name = long_name.replace('Maatschap', 'Mts.')

            if len(shorter_name) > 50:
                _logger.warn("warning: could not create shorter name for company {0}".format(long_name))
                return long_name[:50]
            else:
                return shorter_name
        except UnicodeEncodeError:
            _logger.error("error while trying to generate a shorter company name, truncating to 50 chars")
            return long_name[:50]

    def prefix_vatnr(self, vatnr):
        correct_len=14
        vatnr_len = len(vatnr)
        if vatnr_len < correct_len:
            for x in range(0, correct_len - vatnr_len):
                vatnr = vatnr[:2] + '0' + vatnr[2:]
        return vatnr

    # result: Exact Klant
    def convert_odoo_company_to_exact_account(self, odoo, record):
        # let op in Exact kan het name field max. 50 char
        name = record.get('name')
        if name:
            if len(name) > 50:
                name = self.try_make_shorter_name(name)
        else:
            _logger.error("error: no company name found, set default")
            name='fout: geen naam opgegeven in ODOO'

        vatnumber = record.get('vat') if record.get('vat') else None
        if vatnumber:
            vatnumber = vatnumber.replace('.','').replace(' ','').replace('-','')
            if record.get('country_id')[0] == 166 and len(vatnumber) != 14:
                vatnumber = ''
                #self.prefix_vatnr(vatnumber)
                #_logger.error("Error: VAT nummer exists for company {0} but format is incorrect, the company is copied, " \
                #      "but the VATNumber is skipped!".format(record.get('id')))


        data = {'Code': str(record.get('id')),
                'Name': name,
                'AddressLine1': record.get('street') if record.get('street') else None,
                'AddressLine2': record.get('street2') if record.get('street2') else None,
                'Postcode': record.get('zip') if record.get('zip') else None,
                'City': record.get('city') if record.get('city') else None,
                'Country': odoo.get_country_code(record.get('country_id')[0]) if record.get('country_id') else None,  # alleen country code invullen, dan vult de API vanzelf de CountryName in / NL
                'Phone': record.get('phone') if record.get('phone') else record.get('mobile') if record.get('mobile')
                else None,  # in Exact heeft een bedrijf (Account) alleen een Phone, en geen mobile. Maar een user (Contact) heeft zowel Phone als Mobile. In ODDO heeft zowel bedrijf als user een phone en een mobile
                'Email': record.get('email') if record.get('email') else None,
                'Website': record.get('website') if record.get('website') else None,
                'Logo': record.get('image') if record.get('image') else None,
                'VATNumber': vatnumber,
                'Language': self.get_langcode_from_odoo_lang(record.get('lang')) if record.get('lang') else None,
                'Status': 'C',  # C stands for Customer / Klant
                'GLAR': self.default_debiteuren_rekening_uuid,  # Debiteurenrekening,
                'PaymentConditionSales': self.default_payment_condition_sales_days,
                'Modified': record.get('write_date') if record.get('write_date') else None,
                }

        return data

    # result: Exact Contactpersoon
    def convert_odoo_user_to_exact_contact(self, record):
        _logger.info("trying to convert odoo user with id {0} to exactrecord".format(record.get('id')))
        # create a default account to which all the users are linked who have no parent_id set
        lastname = record.get('name')
        if lastname:
            if len(lastname) > 50:
                lastname = self.try_make_shorter_name(lastname)
        else:
            _logger.error("error: no user name found, set default")
            lastname='fout: geen naam opgegeven in ODOO'

        notes = None

        email = record.get('email') if record.get('email') else None,
        if email and not is_valid_tld(email[0]):
            notes = email[0]
            email = None
            _logger.error("error: while trying to get e-mailaddress for contact {0}. The contact is added but the " \
                  "e-mailaddress is stored in the remarks field".format(record.get('id')))
        else:
            email = email[0]

        data = {'SocialSecurityNumber': str(record.get('id')), #'Code': kan niet, is de code van de bovenliggende bedrijfsaccount
                'LastName': lastname,
                'Phone': record.get('phone') if record.get('phone') else None,
                'Mobile': record.get('mobile') if record.get('mobile') else None,
                'Email': email,
                'Notes': notes,
                'Language': self.get_langcode_from_odoo_lang(record.get('lang')) if record.get('lang') else None,
                'Account': self.get_accountguid_from_odoo_id(record.get('parent_id')[0]) if record.get('parent_id') else None,
                'Picture': record.get('image') if record.get('image') else None,
                'AccountIsCustomer': True if record.get('customer') == True else False,
                'AccountIsSupplier': False,
                'Modified': record.get('write_date') if record.get('write_date') else None,
                }
        return data
    
   


    # result: Exact Invoice
    def convert_odoo_invoice_to_exact_invoice(self, odoo, odoo_invoice_record):
        relation_code = odoo_invoice_record.get('partner_id', None)[0]
        relation_guid = None
        try:
            relation = self.api.relations.get(relation_code=str(relation_code))
            relation_guid = relation.get('ID', None)
        except ObjectDoesNotExist:
            _logger.error("relation with code {0} does not exist in Exact database".format(relation_code))  # todo: relatie automatisch aanmaken indien deze nog niet bestaat
            pass

        payment_condition_code = odoo.get_exact_payment_term_code(odoo_invoice_record.get('payment_term_id', None))
        journal_code = odoo.get_exact_journal_code(odoo_invoice_record.get('journal_id', None))
        yourref = odoo_invoice_record.get('name') if odoo_invoice_record.get('name') else None
        remarks = odoo_invoice_record.get('comment') if odoo_invoice_record.get('comment') else None
        invoice_type = self.invoice_types.get(odoo_invoice_record.get('type'))
        subject = odoo_invoice_record.get('exact_invoice_subject') if odoo_invoice_record.get('exact_invoice_subject') else None

        invoice_line_ids = odoo_invoice_record.get('invoice_line_ids', None)
        if invoice_line_ids:
            odoo_invoice_lines = odoo.get_invoice_lines(invoice_line_ids)

        exact_sales_invoice_lines = []

        if odoo_invoice_lines:
            for odoo_invoice_line in odoo_invoice_lines:
                idx = odoo_invoice_line.get('product_id', None)[1].find(']')
                if idx>=0:
                    item_code = odoo_invoice_line.get('product_id', None)[1][1:idx]
                else:
                    _logger.error("product {0} niet gevonden in exact database".format(odoo_invoice_line.get('product_id', None)[1]))

                logisticsitem_guid = None
                try:
                    logisticsitem = self.api.logisticsitems.get(item_code=str(item_code))
                    logisticsitem_guid = logisticsitem.get('ID', None)
                except ObjectDoesNotExist:
                    _logger.error("artikel / logistics item with code {0} not found in exact db".format(item_code))
                    pass
                
                vatcode = odoo.get_tax_code(odoo_invoice_line.get('invoice_line_tax_ids', None)[0])
                quantity = odoo_invoice_line.get('quantity', None)
                price_unit = odoo_invoice_line.get('price_unit', None)
                if invoice_type==self.invoice_types.get('out_refund'):
                    quantity=-quantity
                discount = odoo_invoice_line.get('discount', None)
                if discount:
                    discount = discount / 100;

                notes =  odoo.get_extra_notes(odoo_invoice_line.get('name', None))
                itemdescription = odoo.get_item_description(odoo_invoice_line.get('name', None))
                
                if logisticsitem_guid:
                    exact_sales_invoice_line = { 'Item': logisticsitem_guid,
                                                 'VATCode': vatcode,
                                                 'Quantity': quantity,
                                                 'UnitPrice': price_unit,
                                                 'Description': itemdescription,
                                                 'Notes': notes,
                                                 'Discount': discount,
                                               }
                    exact_sales_invoice_lines.append(exact_sales_invoice_line)
        else:
            _logger.error("invoice {0} has no corresponding invoice lines".format(odoo_invoice_record.get('id', None)))
            raise Exception("invoice {0} has no corresponding invoice lines".format(odoo_invoice_record.get('id', None)))

        if len(exact_sales_invoice_lines)>0:
            if relation_guid:
                sales_invoice_record = { 'OrderedBy': relation_guid,
                                         'PaymentCondition': payment_condition_code,
                                         'Journal': journal_code,
                                         'Remarks': remarks,
                                         'YourRef': yourref,
                                         'SalesInvoiceLines': exact_sales_invoice_lines,
                                         'Type': invoice_type,
                                         'Description': subject }

                return sales_invoice_record
            else:
                _logger.error("no relation_guid found")
                raise Exception("no relation_guid found")
        else:
                _logger.error("no exact_sales_invoice_lines")
                raise Exception("no exact_sales_invoice_lines")


class Odoo:
    def __init__(self):
        self.url = settings.odoo_url
        self.db = settings.odoo_db
        self.username = settings.odoo_user
        self.password = settings.odoo_pwd

        self.models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(self.url))
        self.common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(self.url))
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})
        if self.uid == False:
            raise Exception('Incorrent Odoo credentials')
        self.company_black_list = settings.odoo_exclude_list
        self.countries = self.models.execute_kw(self.db, self.uid, self.password, 'res.country', 'search_read', [[]],
                                                {'fields': ['id','code']})


    def get_country_code(self, country_id):
        for country in self.countries:
            if country.get("id") == country_id:
                return country.get('code')
        return ''

    def get_odoo_companies(self, from_date=None):
        if from_date:
            # only modified records since from_date
            ids = self.models.execute_kw(self.db, self.uid, self.password, 'res.partner', 'search',
                                         [[['company_type', '=', 'company'],
                                           ['write_date', '>=', from_date]]])
        else:
            # get em all:
            ids = self.models.execute_kw(self.db, self.uid, self.password, 'res.partner', 'search',
                                         [[['company_type', '=', 'company']]])

        # company fields
        # test: bedrijf Basf 10342
        #odoo_company_records = self.models.execute_kw(self.db, self.uid, self.password, 'res.partner', 'read', [[6797,10342,]],
        odoo_company_records = self.models.execute_kw(self.db, self.uid, self.password, 'res.partner', 'read', [ids],
                                        {'fields': ['id',
                                                    'name',
                                                    'street',
                                                    'street2',
                                                    'zip',
                                                    'city',
                                                    'country_id',
                                                    'phone',
                                                    'mobile',
                                                    'email',
                                                    'website',
                                                    'image',
                                                    'vat',
                                                    'lang',
                                                    'customer',
                                                    'partner_num',  # begint met f voor farm en u voor user
                                                    'parent_id',
                                                    'create_date',
                                                    'write_date',
                                                    'dfi_active',
                                                    ]})

        odoo_company_records = [x for x in odoo_company_records if x.get('id') not in self.company_black_list]

        return odoo_company_records

    def company_is_active(self, company_id):
        result = False
        odoo_company_record = self.models.execute_kw(self.db, self.uid, self.password, 'res.partner', 'read', [company_id],
                                        {'fields': ['id',
                                                    'name',
                                                    'dfi_active',
                                                    ]})
        if odoo_company_record:
            result = odoo_company_record.get('dfi_active', False)
        else:
            _logger.warning('no company found with id {0}'.format(company_id))
        return result

    # get all invoices where exact_order_number is ingevuld AND exact_invoice_number is NULL
    def get_invoices_without_invoice_number(self):
        odoo_invoices = self.models.execute_kw(self.db, self.uid, self.password, 'account.invoice', 'search_read',
                         [[['exact_order_number', '>', '0'], ['exact_invoice_number', '=', False]]],
                         {'fields': ['id', 'exact_order_number', ]})
        return odoo_invoices




    def get_odoo_users(self, ids=None):
        odoo_user_records = []
        if ids:
            # user fields
            # test: de medewerkers van Basf
            #odoo_user_records = self.models.execute_kw(self.db, self.uid, self.password, 'res.partner', 'read', [[6798, 11358, 11315, 11179, 11356, 11201, 11355, 11184]],
            odoo_user_records = self.models.execute_kw(self.db, self.uid, self.password, 'res.partner', 'read', [ids],
                                            {'fields': ['id',
                                                        'name',
                                                        'phone',
                                                        'mobile',
                                                        'email',
                                                        'lang',
                                                        'customer',
                                                        'image',
                                                        'partner_num',
                                                        'parent_id',
                                                        'create_date',
                                                        'write_date',
                                                        'dfi_active',
                                                        ]})
        else:
            _logger.error("no user ids specified")
        return odoo_user_records


    def get_odoo_users_from_date(self, from_date=None):
        if from_date:
            # only modified records since from_date
            ids = self.models.execute_kw(self.db, self.uid, self.password, 'res.partner', 'search',
                                         [[['company_type', '=', 'person'],
                                           ['write_date', '>=', from_date]]])
        else:
            # get em all:
            ids = self.models.execute_kw(self.db, self.uid, self.password, 'res.partner', 'search',
                                          [[['company_type', '=', 'person']]])
        return self.get_odoo_users(ids)


    def get_odoo_users_for_company(self, company_id=None):
        if company_id:
            ids = self.models.execute_kw(self.db, self.uid, self.password, 'res.partner', 'search',
                                         [[['company_type', '=', 'person'],
                                           ['parent_id', '=', company_id]]])
        else:
            _logger.error("no company_id supplied")

        return self.get_odoo_users(ids)


    def get_invoice(self, invoice_id):
        _logger.info("get_invoice for invoice_id {0}".format(invoice_id))
        invoice = self.models.execute_kw(self.db, self.uid, self.password, 'account.invoice', 'read', [invoice_id],
                                             {'fields': ['id',
                                              'state',
                                              'partner_id',
                                              'company_id',
                                              'number',
                                              'payment_term_id',
                                              'date_invoice',
                                              'name',  # = referentie/omschrijving
                                              'journal_id',
                                              'invoice_line_ids',
                                              'type',
                                              'comment',
                                              'exact_invoice_subject',
                                              'exact_order_number']} )
        return invoice


    def get_invoice_lines(self, invoice_line_ids=None):
        if invoice_line_ids:
            invoice_lines = self.models.execute_kw(self.db, self.uid, self.password, 'account.invoice.line', 'read', [invoice_line_ids])
                                #{'fields': ['id','product_id', 'name', 'quantity', 'price_unit', 'discount', 'company_id', 'invoice_line_tax_ids', ]} )
        else:
            _logger.warn("please provide an array of invoice_line_ids")
        return invoice_lines

    
    def strip_vatcode(self, vatcode):
        # strip if firstchar is V 
        result = ''
        if vatcode[0] in ('V'):
            for char in vatcode[1:]:
                if char.isspace():
                    return result
                if char.isdigit():
                    result+=char
            return result
        else:
            return vatcode


    def get_tax_code(self, tax_id=None):
        if tax_id:
            tax_code = self.models.execute_kw(self.db, self.uid, self.password, 'account.tax', 'read', [tax_id], {'fields': ['id','name']} )
            tax_code = tax_code.get('name', None)
            if tax_code:
                tax_code = self.strip_vatcode(tax_code)
        else:
            _logger.warn("please provide a tax id")
        return tax_code


    def get_exact_payment_term_code(self, payment_term_id):
        if payment_term_id:
            payment_term_id = payment_term_id[0]
            payment_term_code = self.models.execute_kw(self.db, self.uid, self.password, 'account.payment.term', 'read', [payment_term_id], {'fields': ['exact_code']} )
            if payment_term_code:
                payment_term_code = payment_term_code.get('exact_code', None)
                return payment_term_code


    def get_exact_journal_code(self, journal_id):
        if journal_id:
            journal_id = journal_id[0]
            journal_code = self.models.execute_kw(self.db, self.uid, self.password, 'account.journal', 'read', [journal_id], {'fields': ['exact_code']} )
            if journal_code:
                journal_code = journal_code.get('exact_code', None)
                return journal_code


    def get_exact_id(self, odoo_id):
        exact_division_code = self.models.execute_kw(self.db, self.uid, self.password, 'res.company', 'read', [odoo_id], {'fields': ['exact_division_code']} )
        if exact_division_code:
            exact_division_code = exact_division_code.get('exact_division_code', None)
            return exact_division_code


    def get_odoo_id(self, exact_division_code):
        odoo_id = self.models.execute_kw(self.db, self.uid, self.password, 'res.company', 'search',
                                         [[['exact_division_code', '=', exact_division_code]]] )
        if len(odoo_id)>0:
            odoo_id = odoo_id[0]
            return odoo_id


    def set_exact_order_number(self, odoo_invoice_id, exact_order_number):
        result = self.models.execute_kw(self.db, self.uid, self.password, 'account.invoice', 'write', [[odoo_invoice_id], {
                               'exact_order_number': exact_order_number }])
        return result


    def set_exact_invoice_number(self, exact_order_number, exact_invoice_number):
        _logger.info("trying to set invoice number to {0} for exact_order_number {1}".format(exact_invoice_number, exact_order_number))
        result = False
        odoo_invoice = self.models.execute_kw(self.db, self.uid, self.password, 'account.invoice', 'search_read',
                         [[['exact_order_number', '=', exact_order_number], ['exact_invoice_number', '=', False]]],
                         {'fields': ['id', 'exact_order_number', ]})
        if len(odoo_invoice) == 1:
            odoo_invoice_id = odoo_invoice[0].get("id", None)
            if odoo_invoice_id:
                self.models.execute_kw(self.db, self.uid, self.password, 'account.invoice', 'write', [[odoo_invoice_id], {
                               'exact_invoice_number': exact_invoice_number }])
                result = True
                return result


    def get_extra_notes(self, name):
        if name:
            idx = name.find('\n')
            if idx >=0:
                return name[idx+1:]


    def get_item_description(self, name):
        if name:
            idx = name.find('\n')
            if idx >=0:
                return name[:idx]
            else:
                return name


def export_invoice_to_exact(odoo_invoice_id):
    odoo = Odoo()

    exact_invoice_record = None
    odoo_invoice_record = odoo.get_invoice(odoo_invoice_id)
    if odoo_invoice_record:
        _logger.info("found odoo invoice with id {0}".format(odoo_invoice_id))
    else:
        _logger.info("no odoo invoice found with id {0}".format(odoo_invoice_id))

    partner_id = odoo_invoice_record.get("partner_id", None)
    _logger.info("partner id = {0}".format(partner_id))
    if not odoo.company_is_active(partner_id[0]):
        _logger.error("bedrijf is niet actief, kan niet exporteren")
        raise Exception("bedrijf is niet actief, kan niet exporteren")

    # get exact division code - company id = dacom bv / dfi
    odoo_company_id = odoo_invoice_record.get("company_id", None)
    if odoo_company_id:
        odoo_company_id = odoo_company_id[0]
    exact_division_code = odoo.get_exact_id(odoo_company_id)

    exact = Exact()
    exact.set_division_code(exact_division_code)

    _logger.info("division_code set to = {0}".format(exact_division_code))

    # create an exact-record for the selected odoo invoice
    exact_invoice_record = exact.convert_odoo_invoice_to_exact_invoice(odoo, odoo_invoice_record)

    if exact_invoice_record:
        _logger.info("exact_invoice_record succesvol aangemaakt")
    else:
        raise Exception("fout bij aanmaken exact_invoice_record")
        _logger.error("fout bij aanmaken exact_invoice_record")

    order_number = None
    if exact_invoice_record:
        try:
            _logger.info("trying to add invoice")
            resp = exact.api.salesinvoices.create(exact_invoice_record)
            order_number = resp.get('OrderNumber', None)
            if order_number:
                odoo.set_exact_order_number(odoo_invoice_id, order_number)
                _logger.info("factuur met ordernumber {0} succesvol toegevoegd".format(order_number))
            else:
                _logger.error("fout bij exporteren: {0} / {1}".format(resp))
                raise Exception("fout bij exporteren: {0} / {1}".format(resp))
        except HTTPError as e:
            _logger.error("Fout bij createn invoice: {0}. Details: {1}".format(e.msg, e.response))
            raise Exception("Fout bij createn invoice {0}. Details: {1}".format(e.msg, e.response))
    return order_number

