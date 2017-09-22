from openerp import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    partner_num = fields.Char(string='Partner Number', copy=False, required=False)

    #@api.model
    #def create(self, vals):
        # SequenceObj = self.env['ir.sequence']
        # partner_num = SequenceObj.with_context(self._context).next_by_code('res.partner')
        # vals.update(partner_num=partner_num)
    #    return super(ResPartner, self).create(vals)

    #@api.one
    #def copy(self, default=None):
        # SequenceObj = self.env['ir.sequence']
        # partner_num = SequenceObj.with_context(self._context).next_by_code('res.partner')
        # default.update(partner_num=partner_num)
    #    return super(ResPartner, self).copy(default)

    _sql_constraints = [
        ('patner_num_uniq', 'unique(partner_num)', 'Partner Number must be unique !'),
    ]
