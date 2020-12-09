import logging
from psycopg2 import sql
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.exceptions import UserError, AccessError
from collections import OrderedDict, defaultdict

_logger = logging.getLogger(__name__)

class Lead(models.Model):
    _inherit = "crm.lead"

    planned_revenue = fields.Monetary('Expected Revenue', currency_field='company_currency', tracking=True, compute="_compute_planned_revenue", store=True)
    x_studio_setup_fees = fields.Monetary('Setup Fees', currency_field='company_currency', tracking=True, required=True)
    x_studio_expected_annual_revenue = fields.Monetary('Expected Annual Revenue', currency_field='company_currency', tracking=True, required=True)
    x_studio_expected_recurring_revenue = fields.Monetary('Expected Monthly Recurring Revenue', currency_field='company_currency', tracking=True)
    company_currency_cad = fields.Many2one('res.currency', string='Active Currency (in CAD)', readonly=True,
                                           store=False, default=lambda self: self.env['res.currency'].search([('name', '=', 'CAD')]))
    planned_revenue_cad = fields.Monetary('Expected Revenue (in CAD)', currency_field='company_currency_cad',
                                          store=True, compute='_compute_planned_revenue_cad')
               
    def init(self):
        """
        Update the existing leads to set
        the expected revenue to be sum of
        setup fees and expected annual revenue.
        Also update the converted expected revenue
        to CAD currency.
        """
        
        res = self.env['crm.lead'].search([('type', '=', 'opportunity')])
        cad_currency = self.env['res.currency'].search([('name', '=', 'CAD')])
        cad_company = self.env['res.company'].search([('currency_id', '=', cad_currency.id), ('name', 'ilike', 'Canada')])
        date = fields.Date.today()
        _logger.warning("Initializing Givex CRM module...")
        for each in res:
            lead_curr = self.env['res.currency'].browse(each.company_id.currency_id.id)
            # Set the expected revenue to the sum of setup fees and annual revenue if both are non-zero
            if each.x_studio_setup_fees > 0 and each.x_studio_expected_annual_revenue > 0:
                planned_revenue = each.x_studio_setup_fees + each.x_studio_expected_annual_revenue
            elif each.planned_revenue > 0:
                planned_revenue = each.planned_revenue
            else:
                continue
                
            if each.company_id.id != cad_company.id:
                planned_revenue_cad = lead_curr._convert(planned_revenue, cad_currency, cad_company, date)
            else:
                planned_revenue_cad = planned_revenue
            self.env.cr.execute("""UPDATE crm_lead SET planned_revenue = {0}, planned_revenue_cad = {1}
                                    WHERE id = {2}""".format(planned_revenue, planned_revenue_cad, each.id))
    
    @api.depends('x_studio_setup_fees', 'x_studio_expected_annual_revenue')
    def _compute_planned_revenue(self):
        """
        Planned revenue = Setup fees + Expected Annual revenue
        """

        for lead in self:
            lead.planned_revenue = round((lead.x_studio_setup_fees or 0.0) + (lead.x_studio_expected_annual_revenue or 0), 2)
   
    @api.depends('planned_revenue')
    def _compute_planned_revenue_cad(self):
        """
        Calculate the sum of the planned revenues
        in the current state
        """
        
        active_currency = self.env['res.currency'].search([('name', '=', 'CAD')])
        date = self._context.get('date') or fields.Date.today()
        company = self.env['res.company'].search([('currency_id', '=', active_currency.id)])[0]
        for lead in self:
            if lead.planned_revenue:
                lead_curr = lead.company_id.currency_id
                lead.planned_revenue_cad = lead_curr._convert(lead.planned_revenue, active_currency, company, date)
            else:
                lead.planned_revenue_cad = 0

            return lead.planned_revenue_cad

