from openerp import api, fields, models


class ResPartner(models.Model):
    _inherit = "account.invoice"

    cropr_invoice_token = fields.Char(string='Crop-R invoice token', copy=False)
    cropr_order_number = fields.Char(string='Crop-R order number', copy=False)
