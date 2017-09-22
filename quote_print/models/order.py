
import base64
from contextlib import closing
import logging
import os
import re
import tempfile

from openerp import api, fields, models
from openerp.addons.quote_print.caretutils import listutils
from openerp.tools import ustr
from openerp.exceptions import UserError


_logger = logging.getLogger(__name__)


class SaleOrderInherit(models.Model):
    _inherit = "sale.order"

    website_description_footer = fields.Html('Template Footer', translate=True)
    website_description_footer_below = fields.Html('Template Footer', translate=True)
    show_only_total = fields.Boolean(string='Show Only Total')
    cover_image = fields.Binary("Cover Image", store=True)

    @api.multi
    def onchange_template_id(self, template_id, partner=None, fiscal_position_id=None, pricelist_id=None, context=None):
        res = super(SaleOrderInherit, self).onchange_template_id(template_id, partner=partner, fiscal_position_id=fiscal_position_id, pricelist_id=pricelist_id, context=context)
        if not template_id:
            return res
        template = self.env['sale.quote.template'].with_context(lang=self.partner_id.lang).browse(template_id)
        if template:
            res['value'].update({
                    'website_description_footer': template.website_description_footer,
                    'website_description_footer_below': template.website_description_footer_below,
                    'cover_image': template.cover_image
                })
        return res

    @api.multi
    def get_quote_print_pdf(self):
        report_xml_obj = self.env['ir.actions.report.xml'].search([('report_name','=','website_quote.report_quote')])
        if report_xml_obj:
            report_xml_obj.write({'name':'Offerte_'+ustr(self.company_id.name or '')+'_'+ustr(self.name or '')})
        else:
            report_xml_obj.write({'name':'Web Quotation'})
        self.write({'quote_viewed': True})
        return self.env['report'].get_action(self, 'website_quote.report_quote')


class sale_quote_template_inherit(models.Model):
    _inherit = "sale.quote.template"

    website_description_footer = fields.Html('Template Footer', translate=True)
    website_description_footer_below = fields.Html('Template Footer', translate=True)
    cover_image = fields.Binary("Cover Image", attachment=True)
    file_name_cover = fields.Char('File Name')
    cover_image_pdf = fields.Binary("Cover Image Pdf", attachment=True)
    report_layout = fields.Selection([
        ('address_only', 'First Page Address Only'),
        ('no_extra_space', 'Start Content From First Page'),
        ], string='Report Layout')
    file_name_cover_pdf = fields.Char('Pdf File Name')
    cover_height = fields.Integer(string="Cover Image Height", default=1031)
    IsfooterAdrsIma_first_page = fields.Boolean(string="Remove Footer", help="Show footer address image on first page when rest pages don't have footer")

    @api.multi
    def write(self, values):
        needPdfUpdate = True if values.get('cover_image') else False
        result = super(sale_quote_template_inherit, self).write(values)
        if self.cover_image and values.get('cover_height'):
            self.generate_pdf()
            return result
        if needPdfUpdate:
            self.generate_pdf()
            return result
        return result

    @api.multi
    def generate_pdf(self):
        if not self.cover_image:
            self.cover_image_pdf = None
            self.file_name_cover_pdf = None
            return
        pdf = self.env['report'].sudo().get_pdf([self.id], 'quote_print.report_quote_cover')
        self.cover_image_pdf = base64.b64encode(pdf)
        self.file_name_cover_pdf = (self.file_name_cover.split('.')[0] or 'cover') + '.pdf'


class ReportInherit(models.Model):
    _inherit = "report"
    report_name_custom = None

    def get_html(self, cr, uid, docids, report_name, data=None, context=None):
        """This method generates and returns html version of a report after filling
        custom values.
        """
        html = super(ReportInherit, self).get_html(cr, uid, docids, report_name, data=data, context=context)
        if not isinstance(html, str or unicode):
            return html
        if report_name != 'website_quote.report_quote':
            return html
        reportModel = self._get_report_from_name(cr, uid, 'website_quote.report_quote').model
        if reportModel != 'sale.order':
            return html
        variables = re.findall(r'\${custom:.*?}', html)
        if not variables:
            return html
        for i, variChunk in enumerate(listutils.chunks(variables, len(variables) / len(docids))):
            docId = docids[i]
            object = self.pool['sale.order'].browse(cr, uid, docId)
            for variable in variChunk:
                value = eval(variable[9:-1])
                if isinstance(value, (int, float, long, list, tuple, dict)):
                    try:
                        # There are uncertain possible data. So making generic and ignore issue.
                        try:
                            value = str(value).encode("utf-8").decode("utf-8")
                        except:
                            value = str(value).decode("utf-8")
                    except:
                        print 'Invalid Data'
                        value = u''
                html = html.replace(variable, value.encode('utf-8'), 1)
        return html

    def get_pdf(self, cr, uid, docids, report_name, html=None, data=None, context=None):
        """This method generates and returns pdf version with background of a report.
        """
        self.report_name_custom = report_name
        pdf = super(ReportInherit, self).get_pdf(cr, uid, docids, report_name, html=html, data=data, context=context)

        if self.report_name_custom != 'website_quote.report_quote':
            return pdf

        reportModel = self._get_report_from_name(cr, uid,'website_quote.report_quote').model
        if reportModel != 'sale.order':
            return pdf

        soId = docids[0] if isinstance(docids, list) else docids
        so = self.pool['sale.order'].browse(cr, uid, soId)
        if not so.template_id:
            return pdf

        cover_image = so.template_id.cover_image
        cover_image_pdf = so.template_id.cover_image_pdf
        if cover_image and cover_image_pdf:
            report_fd, report_path = tempfile.mkstemp(suffix='.pdf', prefix='report.tmp.')
            with closing(os.fdopen(report_fd, 'w')) as repo:
                repo.write(pdf)

            cover_image_pdf = base64.decodestring(cover_image_pdf)
            cover_fd, cover_path = tempfile.mkstemp(suffix='.pdf', prefix='report.tmp.')
            with closing(os.fdopen(cover_fd, 'w')) as repo:
                repo.write(cover_image_pdf)

            mergeFile = self._merge_pdf([cover_path, report_path])
            with open(mergeFile, 'rb') as pdfdocument:
                pdf = pdfdocument.read()

        return pdf

    def _run_wkhtmltopdf(self, cr, uid, headers, footers, bodies, landscape, paperformat, spec_paperformat_args=None, save_in_attachment=None, set_viewport_size=False, context=None):
        """Execute wkhtmltopdf as a subprocess in order to convert html given in input into a pdf
        document.

        :param header: list of string containing the headers
        :param footer: list of string containing the footers
        :param bodies: list of string containing the reports
        :param landscape: boolean to force the pdf to be rendered under a landscape format
        :param paperformat: ir.actions.report.paperformat to generate the wkhtmltopf arguments
        :param specific_paperformat_args: dict of prioritized paperformat arguments
        :param save_in_attachment: dict of reports to save/load in/from the db
        :returns: Content of the pdf as a string
        """
        if self.report_name_custom == 'website_quote.report_quote':
            sale_order_id = bodies[0][0]
            sale_obj = self.pool['sale.order'].browse(cr, uid, sale_order_id)
            if sale_obj:
                ir_model_data = self.pool['ir.model.data']
                paperformate_id = ir_model_data.get_object_reference(cr, uid, 'quote_print', 'quote_print_custom_header_paperformat')[1]
                paperformatObj = self.pool['report.paperformat'].browse(cr, uid, paperformate_id)
                if sale_obj.template_id.IsfooterAdrsIma_first_page:
                    paperformatObj.write({'margin_bottom' : 23})
                else:
                    paperformatObj.write({'margin_bottom' : 53})
            set_viewport_size = True
        try:
            res = super(ReportInherit, self)._run_wkhtmltopdf(cr, uid, headers, footers, bodies, landscape, paperformat, spec_paperformat_args=spec_paperformat_args, save_in_attachment=save_in_attachment, set_viewport_size=set_viewport_size, context=context)
        except TypeError as err:
            if 'context' in err.message:
                res = super(ReportInherit, self)._run_wkhtmltopdf(cr, uid, headers, footers, bodies, landscape, paperformat, spec_paperformat_args=spec_paperformat_args, save_in_attachment=save_in_attachment, set_viewport_size=set_viewport_size)
            else:
                _logger.critical('TypeError: %s' % err.message)
                raise err
        return res


class CompanyInheritQuote(models.Model):
    _inherit = "res.company"

    footer_address_image = fields.Binary("Footer Address Image", attachment=True)
    file_name_footer_address = fields.Char('File Name')
    footerAdrs_first_page_img = fields.Binary("Footer Address Image First Page", attachment=True)
    file_name_footerAdrsFirstPage = fields.Char('File Name')
