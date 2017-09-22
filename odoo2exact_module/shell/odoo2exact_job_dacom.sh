#!/bin/bash
cd /mnt/extra-addons/odoo2exact_module
sed -i "s/division =.*/division = 1518265/" /mnt/extra-addons/odoo2exact_module/exactonline/config.ini
python /mnt/extra-addons/odoo2exact_module/odoo2exact_main.py 1518265