{
    'name': 'Odoo2exact migration',
    'category': 'Hidden',
    'description': """This module migrates invoices from the ODOO environment to the Exact environment.
                      Extra fields and an export button are added to the account.invoice model/page in order to maintain a link between the two systems.
                      After an invoice is succesfully transferred to Exact, the ordernumber from the Exact system is transferred to this new field in ODOO.
                      The button is only visible if the invoice state is open AND if the exact ordernumber field is empty.

                      ** Handleiding installatie **
                        Zip file met module uploaden in /mnt/extra-addons
                        Inloggen in ODOO, zet developer mode aan --> en ga naar toepassingen --> Modulelijst bijwerken
                        Klik daarnaa op "toepassingen" --> ga naar het zoekveld rechtsboven en haal het woord "toepassingen" daar weg en type odoo2exact
                        Klik op installeren.
                        Configure Exact --> self.storage --> pad naar exactonline config.ini

                        config.ini moet eigenaar/group odoo hebben
                      
                      ** handleiding bijwerken:
                        Klik op bijwerken in de UI, daarna server opnieuw opstarten om wijzigingen actief te maken
                        
                      # todo: setup proces koppeling exact beschrijvenm7gs1kfskd
                        
                        
                        
                      ** Configuratie in ODOO **
                        betalingsconditie  : Boekhouding --> Instellingen --> Beheer --> Betalingscondities --> "Exact code" invullen voor elke conditie.
                        journaal/dagboeken : Boekhouding --> Instellingen --> Boekhouding --> Dagboeken --> "Exact code" invullen voor elk journaal/dagboek.
                        exact division     : Algemene instellingen -> Bedrijven --> Voor elk bedrijf de "Exact division code" instellen.

        """,
    'version': '0.27',
    'depends':['base', 'account'],
    'author': 'Allard',
    'website': "https://www.dacom.nl",
    'data' : [
        'views/odoo_exact_view.xml',
    ],
    'auto_install': False,
    'installable': True,
}
