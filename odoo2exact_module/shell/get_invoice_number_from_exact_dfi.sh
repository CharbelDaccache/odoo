#!/bin/bash
cd /mnt/extra-addons/odoo2exact_module
sed -i "s/division =.*/division = 1518516/" /mnt/extra-addons/odoo2exact_module/exactonline/config.ini
python /mnt/extra-addons/odoo2exact_module/odoo2exact_main.py getandsetinvoicenumber 1518516
