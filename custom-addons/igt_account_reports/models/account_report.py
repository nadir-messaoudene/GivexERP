# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2020 (https://ingenieuxtech.odoo.com)
# ingenieuxtechnologies@gmail.com
# ingenieuxtechnologies
#
##############################################################################
from odoo import models, fields, api


class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    @api.model
    def _init_filter_partner(self, options, previous_options=None):
        options['partner_account_receivable_ids'] = \
            previous_options and previous_options.get(
                'partner_account_receivable_ids') or []
        selected_partner_account_receivable_ids = [
            int(account) for account in options[
                'partner_account_receivable_ids']]
        selected_partner_account_receivable = \
            selected_partner_account_receivable_ids and self.env[
                'account.account'].browse(
                selected_partner_account_receivable_ids) or self.env[
                'res.partner.category']
        options['selected_partner_account_receivable_ids'] = \
            selected_partner_account_receivable.mapped('name')
        res = super(AccountReport, self)._init_filter_partner(
            options=options, previous_options=previous_options)
        return res

    @api.model
    def _get_options_partner_domain(self, options):
        domain = super(AccountReport, self)._get_options_partner_domain(options=options)
        if options.get('partner_account_receivable_ids'):
            partner_account_receivable_ids = [
                int(partner) for partner in options[
                    'partner_account_receivable_ids']]
            domain.append(('partner_id.property_account_receivable_id',
                           'in', partner_account_receivable_ids))
        return domain

    def _set_context(self, options):
        ctx = super(AccountReport, self)._set_context(options=options)
        if options.get('partner_account_receivable_ids'):
            ctx['partner_account_receivable_ids'] = self.env[
                'account.account'].browse([
                int(account) for account in options[
                    'partner_account_receivable_ids']])
        return ctx

    def get_report_informations(self, options):
        info = super(AccountReport, self).get_report_informations(options=options)
        options = info.get('options')
        options['selected_partner_account_receivable_ids'] = [
            self.env['account.account'].browse(int(category)).name for
            category in (options.get('partner_account_receivable_ids') or [])]
        info['options'] = options
        return info
