# $Id: create_invoice.py,v 1.4 2021/03/31 13:09:41 skumar Exp $
# Copyright Givex Corporation.  All rights reserved.

from odoo import api, fields, models, _
import logging
from operator import itemgetter
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
import traceback, sys

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _name="account.move.line"
    _inherit="account.move.line"
    
    def _get_computed_name(self):
        self.ensure_one()

        if not self.product_id:
            return ''

        # if a name already exists for an imported invoice, return that
        if self.move_id.invoice_origin == 'import' and self.name:
            return self.name
        
        if self.partner_id.lang:
            product = self.product_id.with_context(lang=self.partner_id.lang)
        else:
            product = self.product_id

        values = []
        if product.partner_ref:
            values.append(product.partner_ref)
        if self.journal_id.type == 'sale':
            if product.description_sale:
                values.append(product.description_sale)
        elif self.journal_id.type == 'purchase':
            if product.description_purchase:
                values.append(product.description_purchase)
        
        return '\n'.join(values)


class AccountMoveXmlrpc(models.Model):
    _name = 'account.move.xmlrpc'

    def create(self, customer_id, product_list, date_desc):
        partner = self.env['res.partner'].sudo().browse(customer_id)
        account_id = partner.property_account_receivable_id.id
        company_id = partner.company_id.id

        self.env.cr.execute("SELECT currency_id FROM res_company WHERE id = %s", (company_id,))
        currency_id = self.env.cr.dictfetchone().get('currency_id')
        
        journal = self.env['account.journal'].sudo().search([('type', '=', 'sale'), ('company_id', '=', company_id)], limit=1)
        journal_id = journal.id
        
        partner_address = partner.address_get(['contact', 'invoice'])
        # date_desc in format "month YYYY-mm"   or "range [YYYY-mm-dd,YYYY-mm-dd]"
        try:
            if 'range' in date_desc:            
                date_invoice = datetime.strptime((date_desc.split(' ')[1].strip('[])')).split(',')[1], '%Y-%m-%d') + relativedelta(days=-1)
            else:
                date_invoice = datetime.strptime(str(date_desc).split(' ')[1], '%Y-%m') + relativedelta(day=31)
        except Exception as e:
            ex = sys.exc_info()
            tb = ''.join(traceback.format_exception(ex[0], ex[1], ex[2]))
            _logger.error('Error in calculating invoice date!\n'+tb)
            date_invoice = date.today() + relativedelta(day=31, months=-1)

        # Check if the invoice is to a child company having parent company as a dealer
        name = partner.ref
        if partner.parent_id:
            if partner.parent_id and partner.parent_id.x_studio_entity_type == 'dealer':
                # Copy partner name into customer reference field for dealer invoices
                name = partner.name  
                if partner.ref:
                    name += ' : %s' % partner.ref
                partner_id = partner.parent_id.id
            else:
                # Find the top most parent customer
                while partner.parent_id:
                    partner = partner.parent_id
                partner_id = partner.id

            partner = self.env['res.partner'].sudo().browse(customer_id)
            account_id = partner.property_account_receivable_id.id
        else:
            partner_id = customer_id

        invoice_address = None
        if partner_address['invoice']:
            invoice_address = partner_address['invoice']
        elif partner_address['contact']:
            invoice_address = partner_address['contact']

        # get the fiscal position based on the shipping address
        fiscal_position_id = None
        if invoice_address:
            fiscal_position_id = self.env['account.fiscal.position'].with_context(force_company=company_id).get_fiscal_position(partner_id, invoice_address)
        
        move = {'type': 'out_invoice',
                'state': 'draft',
                'invoice_origin': 'import',
                'extract_state': 'no_extract_requested',
                'partner_shipping_id': invoice_address,
                'fiscal_position_id': fiscal_position_id,
                'date': date_invoice,
                'invoice_date': date_invoice,
                'invoice_date_due': date_invoice,
                'partner_id' : partner_id,
                'company_id': company_id,
                'currency_id': currency_id,
                'journal_id': journal_id,
        }
        
        pids = list(map(itemgetter(0), product_list))
        pquantity = list(map(itemgetter(1), product_list))
        pdescription = list(map(itemgetter(2), product_list))
        product_counter = 0
        invoice_line_ids = []

        while product_counter < len(pids):
            product_id = pids[product_counter]
            product_description = pdescription[product_counter]
            product_rec = self.env['product.product'].sudo().browse(product_id)
            quantity = pquantity[product_counter]

            property_obj = self.env['ir.property'].sudo().with_context(force_company=company_id)
            # get the product pricelist of the customer from the company property
            res_id = 'res.partner,' + str(partner_id)
            property_id = property_obj.search([('name', '=', 'property_product_pricelist'),
                                               ('res_id', '=', res_id),
                                               ('company_id', '=', company_id)], limit=1)
            if property_id and property_id.value_reference:
                pricelist_id = int(str(property_id.value_reference).split(',')[1])
            else:
                pricelist_id = partner.property_product_pricelist.id
            
            pricelist = self.env['product.pricelist'].search([('id', '=', pricelist_id)])
            price_unit = pricelist.price_get(product_id, quantity, customer_id)[pricelist_id]

            if not price_unit > 0:
                _logger.info("Product {0} has $0 price. Skipping...".format(product_id))
                product_counter += 1
                continue

            res_id = str("product.template," + str(product_id))
            # Check for the product level account
            property_id = property_obj.search([('name', '=', 'property_account_income_id'),
                                               ('res_id', '=', res_id),
                                               ('company_id', '=', company_id)], limit=1)

            product_obj = self.env['product.product'].sudo().browse(product_id)
            if not property_id:
                product_template_id =  product_obj.product_tmpl_id.id
                product_category = self.env['product.template'].sudo().browse(product_template_id).categ_id.id
                res_id = str("product.category," + str(product_category))
                # Check for the product category level account
                property_id = property_obj.search([('name', '=', 'property_account_income_categ_id'),
                                                   ('res_id', '=', res_id),
                                                   ('company_id', '=', company_id)], limit=1)

            if not property_id:
                # Check for the company level account
                property_id = property_obj.search([('name', '=', 'property_account_income_categ_id'),
                                                   ('company_id', '=', company_id)], limit=1)[0]
            else:
                property_id = property_id[0]

            property_res_id = False
            if property_id and property_id.value_reference:
                property_res_id = int(str(property_id.value_reference).split(',')[1])
            
            if property_res_id:
                acc_id = self.env.get('account.account').sudo().browse(property_res_id).id
            else:
                acc_id = False
            
            price = product_obj.list_price

            # fiscal position for taxes
            fpos_obj = self.env['account.fiscal.position'].sudo()
            fpos = fiscal_position_id and fpos_obj.browse(fiscal_position_id) or False
            taxes = False
            taxes_ids = []
            if product_rec.taxes_id:
                taxes = product_rec.taxes_id
            elif acc_id:
                taxes = self.env['account.account'].sudo().browse(acc_id).tax_ids
            
            if fpos and taxes:
                taxes = taxes.filtered(lambda tax: tax.company_id.id == company_id)
                taxes_ids = fpos.map_tax(taxes._origin, partner=partner_id).ids

            # Set the invoice date to 1st of the month if its a store product
            if str(product_rec.default_code).find('GVX-TRX-STORE') != -1:
                date_invoice = date.today() + relativedelta(day=1)
                move['invoice_date'] = move['invoice_date_due'] = date_invoice

            # Set the product desc with the correct date its invoiced for
            if 'Per active store' in product_description:
                product_description += " for month %s" % date_invoice.strftime('%Y-%m') 

            # Calculate billing period
            ref = ''
            if partner.x_studio_frequency and date_invoice:
                if partner.x_studio_frequency == 'monthly':
                    ref = date_invoice.strftime("%B %Y")
                elif partner.x_studio_frequency == 'quarterly':
                    # Q1 - Jan, Feb, Mar
                    # Q2 - Apr, May, Jun
                    # Q3 - Jul, Aug, Sep
                    # Q4 - Oct, Nov, Dec
                    month = int(date_invoice.strftime("%m"))
                    if month in (1, 2, 3):
                        ref = 'Q1 %s' % date_invoice.strftime('%Y')
                    elif month in (4, 5, 6):
                        ref = 'Q2 %s' % date_invoice.strftime('%Y')
                    elif month in (7, 8, 9):
                        ref = 'Q3 %s' % date_invoice.strftime('%Y')
                    elif month in (10, 11, 12):
                        ref = 'Q4 %s' % date_invoice.strftime('%Y')
                elif partner.x_studio_frequency == 'yearly':
                    # For store transactions, set annual billing period for the future
                    # if invoice date is first of month, then invoice date's month, current year - previous month, year +1
                    if str(product_rec.default_code).find('GVX-TRX-STORE') != -1:
                        ref = '%s - %s' % (date_invoice.strftime("%B %Y"), (date_invoice + relativedelta(years=1, months=-1)).strftime("%B %Y"))
                    # so for invoices with invoice date end of month, the billing period is invoice date month+1, year -1 to invoice date month, year
                    else:
                        ref = '%s - %s' % ((date_invoice + relativedelta(months=1, years=-1)).strftime("%B %Y"), date_invoice.strftime("%B %Y"))

                if str(product_description).find('Increment Fee') != -1: 
                    ref = 'Upto ' + ref
                    
            move_line = {'account_id': acc_id,
                         'name': product_description,
                         'product_id': product_id,
                         'quantity': quantity,
                         'price_unit': price_unit,
                         'ref' : ref,
            }
            if taxes_ids:
                move_line['tax_ids'] = [(6, 0, taxes_ids)]

            invoice_line_ids.append(move_line)
            product_counter += 1

        try:
            move_id = None
            move['invoice_line_ids'] = [(0, 0, line) for line in invoice_line_ids]
            # before creating the invoice, check if already an invoice
            # was created last month due to the threshold limit not reached
            q_move = self.env['account.move'].sudo().search([('partner_id', '=', partner_id),
                                                             ('invoice_origin', '=', 'import'), ('state', '=', 'draft'),
                                                             ('invoice_date', '=', date_invoice)])

            if q_move and q_move[0].id:
                q_move[0].write({'date': date_invoice,
                                 'invoice_date': date_invoice,
                                 'invoice_date_due': date_invoice,
                                 'invoice_line_ids': move['invoice_line_ids'],
                                 })
                move_id = q_move[0]
            else:
                # create a new invoice
                move_id = self.env['account.move'].sudo().create([move])

        except Exception as e:
            ex = sys.exc_info()
            tb = ''.join(traceback.format_exception(ex[0], ex[1], ex[2]))
            _logger.error('Invoice generation error!\n'+tb)
            raise Exception(_("Import Invoices: Error while generating the invoice."), e, str(e), _("For more reference inspect error logs."))

        if move_id:
            # delete the $0 invoices
            self.env.cr.execute("SAVEPOINT script_invoice_reserve")
            if not move_id.amount_total or move_id.amount_total <= 0:
                _logger.info('Deleting $0 invoice {0}'.format(move_id.id))
                self.env.cr.execute("DELETE FROM account_move WHERE id = %s", (move_id.id,))
            else:
                # if invoice total not beyond threshold, move the invoice date
                # to the next month so that it will not be posted
                if partner.x_studio_threshold and move_id.amount_total < partner.x_studio_threshold:
                    update_invoice_date = date_invoice + relativedelta(day=31, months=+1)
                    _logger.info('Due to threshold, setting invoice date to future for {0} - {1}'.format(move_id.id, update_invoice_date))
                    move_id.write({'invoice_date': update_invoice_date,
                                   'invoice_date_due': update_invoice_date})
                else:
                    self.env.cr.execute("ROLLBACK TO script_invoice_reserve")

            return move_id


AccountMoveXmlrpc()
