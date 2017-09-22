import os

odoo_url = "https://erp.crop-r.com"
odoo_db = "production"
odoo_user = "admin"
odoo_pwd = "Dacom123!"
odoo_exclude_list = [4545,]  # czav
exact_config_file = os.path.join(os.path.dirname(__file__), 'exactonline/config.ini')
exact_default_account_id = 1
exact_default_payment_condition_sales_days = '14'
exact_debiteuren_rekening = '1300'
