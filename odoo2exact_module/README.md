# odoo2exact
This script reads the customer data from ODOO and imports this data to ExactOnline

## prerequisites
- handmatig kopieren script vanaf ontwikkelaar's pc naar felsina /root:
    
    `scp odoo2exact.tar.gz cropr@felsina.crop-r.com:`

- handmatig kopieren script vanaf felsina/root naar de docker-container:
    
    `ssh cropr@felsina.crop-r.com`
    `docker cp odoo2exact.tar.gz odoo:/root/`

- in de odoo container uitvoeren:
    
    `apt-get install cron net-tools vim`
    `pip install flask`

- daarna README van odoo2exact volgen.

- cronjobs in de container zetten:

    `*/30 * * * * /root/odoo2exact/odoo2exact_job.sh >/root/odoo2exact_job.log 2>&1`


    odoo2exact_job.sh:
    #!/bin/bash
    cd /root/odoo2exact
    python /root/odoo2exact/odoo2exact.py 1557337


## odoo2exact setup notes
- go to https://apps.exactonline.com/ --> click login --> and login with your ExactOnline credentials --> register api keys...
- app name: odoo2exact / redirect-url = https://erp-dev.crop-r.com/exact/get-code/
- configure the client-id and the client-secret in exactonline/config.ini (make sure the client-id is surrounded with brackets {})
- make sure the response-url in config.ini is set to: response-url = https://erp-dev.crop-r.com/exact/get-code/
- only on DEVELOPER PC: run an instance of this app with argument `web` to setup the initial authentication tokens `python odoo2exact.py web`
  this is NOT NECESSARY on PRODUCTION because the oauth2 callback routine is integrated in the odoo-module.
- run a second instance of this app with argument `setup` to setup the initial authentication tokens `python odoo2exact.py setup`
- start a webbrowser and browse to the url provided by the previous step.
- browse to https://start.exactonline.nl/api/v1/current/Me search for division code and put the resulting value in the config.ini file
- an ExactOnline login screen is shown which will ask you to login with your ExactOnline credentials
- after succesfull authentication the authentication tokens in the transient section of config.ini will be updated automatically by the odoo2exact script. Login with username/password is no longer necessary after this step.
- Done. The application can now be started without arguments to start the data transfer process.


