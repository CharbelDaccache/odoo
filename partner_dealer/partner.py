from openerp import api, fields, models, _

class ResPartner(models.Model):
    _inherit = "res.partner"

    dealer = fields.Boolean(string='Is Dealer')
    dealer_id = fields.Many2one('res.partner', string="Dealer")