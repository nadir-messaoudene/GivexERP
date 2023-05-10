# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2020 (https://ingenieuxtech.odoo.com)
# ingenieuxtechnologies@gmail.com
# ingenieuxtechnologies
#
##############################################################################

from collections import defaultdict
from odoo import models, api, _


# class ReportAccountFinancialReport(models.Model):
#     _inherit = "account.financial.html.report"
class AccountFinancialReportLine(models.Model):
    _inherit = "account.financial.html.report.line"

    def _compute_amls_results(self, options_list, calling_financial_report, sign=1, operator=None):
        print("_compute_amls_results _inherit>>>>>>>>>>>>>>>", self, options_list, calling_financial_report, sign, operator)
        print("_compute_amls_results >>>>>>>>>>>>>>>>>>>", self, options_list, calling_financial_report, sign, operator)
        res = super(AccountFinancialReportLine, self)._compute_amls_results(options_list, calling_financial_report, sign, operator)
        print("res _inherit>>>>>>>>>>>>>>>>>>>>>>>>>>", res)
        # res = list(filter(lambda x: 0 not in list(x[-1].values()), res))
        res = list(filter(lambda x: any(list(x[-1].values())), res))
        return res

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

    def get_account_codes(self, account):
        # A code is tuple(id, name)
        super(AccountReport, self).get_account_codes(account=account)
        codes = []
        if account.group_id:
            group = account.group_id
            while group:
                # codes.append((group.id, group.display_name))
                codes.append((group.id, group.name))
                group = group.parent_id
        else:
            codes.append((0, _('(No Group)')))
        return list(reversed(codes))

        # def compute_hierarchy(lines, level, parent_id):
        #     # put every line in each of its parents (from less global to more global) and compute the totals
        #     super(AccountReport, self).get_account_codes(lines=lines, level=level, parent_id=parent_id)
        #     hierarchy = defaultdict(lambda: {'totals': [None] * len(lines[0]['columns']), 'lines': [], 'children_codes': set(), 'name': '', 'parent_id': None, 'id': ''})
        #     # print("lines >>>>>>>>>>>>>>>>>>>>>", lines)
        #     # accounts = [self.env['account.account'].browse(line.get('account_id', self._get_caret_option_target_id(line.get('id')))) for line in lines]
        #     # print("accounts >>>>>>>>>>>>>>>>>", accounts)
        #     # codes = []
        #     # for account in accounts:
        #     #     codes.append(self.get_account_codes(account)[0])
        #     # print("codes >>>>>>>>>>>>", codes)
        #     previous_codes = []

        #     for line in lines:
        #         account = self.env['account.account'].browse(line.get('account_id', self._get_caret_option_target_id(line.get('id'))))
        #         print("accounts >>>>>>>>>>>>>>>>>>>>>", account)
        #         codes = self.get_account_codes(account)  # id, name
        #         print("codes >>>>>>>>>>>>", codes)
        #         if previous_codes and previous_codes[0][1] == codes[0][1]:
        #             codes = previous_codes
        #         else:
        #             previous_codes = codes
        #         for code in codes:
        #             hierarchy[code[0]]['id'] = self._get_generic_line_id('account.group', code[1], parent_line_id=line['id'])
        #             # print("hierarchy[code[0]]['id'] >>>>>>>>>>>", hierarchy[code[0]]['id'])
        #             hierarchy[code[0]]['name'] = code[1]
        #             # print("hierarchy[code[0]]['name'] >>>>>>>>>", hierarchy[code[0]]['name'])
        #             for i, column in enumerate(line['columns']):
        #                 if 'no_format_name' in column:
        #                     no_format = column['no_format_name']
        #                 elif 'no_format' in column:
        #                     no_format = column['no_format']
        #                 else:
        #                     no_format = None
        #                 if isinstance(no_format, (int, float)):
        #                     if hierarchy[code[0]]['totals'][i] is None:
        #                         hierarchy[code[0]]['totals'][i] = no_format
        #                     else:
        #                         hierarchy[code[0]]['totals'][i] += no_format
        #         for code, child in zip(codes[:-1], codes[1:]):
        #             hierarchy[code[0]]['children_codes'].add(child[0])
        #             hierarchy[child[0]]['parent_id'] = hierarchy[code[0]]['id']
        #         hierarchy[codes[-1][0]]['lines'] += [line]
        #     # compute the tree-like structure by starting at the roots (being groups without parents)
        #     hierarchy_lines = []
        #     for root in [k for k, v in hierarchy.items() if not v['parent_id']]:
        #         add_to_hierarchy(hierarchy_lines, root, level, parent_id, hierarchy)
        #     return hierarchy_lines

        # new_lines = []
        # account_lines = []
        # current_level = 0
        # parent_id = 'root'
        # for line in lines:
        #     if not (line.get('caret_options') == 'account.account' or line.get('account_id')):
        #         # make the hierarchy with the lines we gathered, append it to the new lines and restart the gathering
        #         if account_lines:
        #             new_lines.extend(compute_hierarchy(account_lines, current_level + 1, parent_id))
        #         account_lines = []
        #         new_lines.append(line)
        #         current_level = line['level']
        #         parent_id = line['id']
        #     else:
        #         # gather all the lines we can create a hierarchy on
        #         account_lines.append(line)
        # # do it one last time for the gathered lines remaining
        # if account_lines:
        #     new_lines.extend(compute_hierarchy(account_lines, current_level + 1, parent_id))
        # return new_lines

    @api.model
    def _create_hierarchy(self, lines, options):
        super(AccountReport, self)._create_hierarchy(lines=lines, options=options)
        # lines = list(filter(lambda x: x.get('columns') and bool(x.get('columns')[0].get('no_format')) is not False, lines))
        lines = list(filter(lambda x: x.get('columns') and any(list(map(lambda x: x.get('no_format'), x.get('columns')))), lines))
        unfold_all = self.env.context.get('print_mode') and len(options.get('unfolded_lines')) == 0 or options.get('unfold_all')

        def add_to_hierarchy(lines, key, level, parent_id, hierarchy):
            val_dict = hierarchy[key]
            unfolded = val_dict['id'] in options.get('unfolded_lines') or unfold_all
            # add the group totals
            lines.append({
                'id': val_dict['id'],
                'name': val_dict['name'],
                'title_hover': val_dict['name'],
                'unfoldable': True,
                'unfolded': unfolded,
                'level': level,
                'parent_id': parent_id,
                'columns': [{'name': self.format_value(c) if isinstance(c, (int, float)) else c, 'no_format_name': c} for c in val_dict['totals']],
            })
            if not self._context.get('print_mode') or unfolded:
                for i in val_dict['children_codes']:
                    hierarchy[i]['parent_code'] = i
                all_lines = [hierarchy[id] for id in val_dict["children_codes"]] + val_dict["lines"]
                for line in sorted(all_lines, key=lambda k: k.get('account_code', '') + k['name']):
                    if 'children_codes' in line:
                        children = []
                        # if the line is a child group, add it recursively
                        add_to_hierarchy(children, line['parent_code'], level + 1, val_dict['id'], hierarchy)
                        lines.extend(children)
                    else:
                        # add lines that are in this group but not in one of this group's children groups
                        line['level'] = level + 1
                        line['parent_id'] = val_dict['id']
                        lines.append(line)

        def compute_hierarchy(lines, level, parent_id):
            # put every line in each of its parents (from less global to more global) and compute the totals
            hierarchy = defaultdict(lambda: {'totals': [None] * len(lines[0]['columns']), 'lines': [], 'children_codes': set(), 'name': '', 'parent_id': None, 'id': ''})
            previous_codes = []
            for line in lines:
                account = self.env['account.account'].browse(line.get('account_id', self._get_caret_option_target_id(line.get('id'))))
                print("accounts >>>>>>>>>>>>>>>>>>>>>", account)
                codes = self.get_account_codes(account)  # id, name
                print("codes >>>>>>>>>>>>", codes)
                if previous_codes and codes[0][1] in list(dict(previous_codes).values()):
                    for key, value in dict(previous_codes).items():
                        if value == codes[0][1]:
                            codes = [(key, value)]
                else:
                    previous_codes += codes
                # if previous_codes and previous_codes[0][1] == codes[0][1]:
                #     codes = previous_codes
                # else:
                #     previous_codes = codes
                for code in codes:
                    hierarchy[code[0]]['id'] = self._get_generic_line_id('account.group', code[0], parent_line_id=line['id'])
                    hierarchy[code[0]]['name'] = code[1]
                    for i, column in enumerate(line['columns']):
                        if 'no_format_name' in column:
                            no_format = column['no_format_name']
                        elif 'no_format' in column:
                            no_format = column['no_format']
                        else:
                            no_format = None
                        if isinstance(no_format, (int, float)):
                            if hierarchy[code[0]]['totals'][i] is None:
                                hierarchy[code[0]]['totals'][i] = no_format
                            else:
                                hierarchy[code[0]]['totals'][i] += no_format
                for code, child in zip(codes[:-1], codes[1:]):
                    hierarchy[code[0]]['children_codes'].add(child[0])
                    hierarchy[child[0]]['parent_id'] = hierarchy[code[0]]['id']
                hierarchy[codes[-1][0]]['lines'] += [line]
            # compute the tree-like structure by starting at the roots (being groups without parents)
            hierarchy_lines = []
            for root in [k for k, v in hierarchy.items() if not v['parent_id']]:
                add_to_hierarchy(hierarchy_lines, root, level, parent_id, hierarchy)
            return hierarchy_lines

        new_lines = []
        account_lines = []
        current_level = 0
        parent_id = 'root'
        for line in lines:
            if not (line.get('caret_options') == 'account.account' or line.get('account_id')):
                # make the hierarchy with the lines we gathered, append it to the new lines and restart the gathering
                if account_lines:
                    new_lines.extend(compute_hierarchy(account_lines, current_level + 1, parent_id))
                account_lines = []
                new_lines.append(line)
                current_level = line['level']
                parent_id = line['id']
            else:
                # gather all the lines we can create a hierarchy on
                account_lines.append(line)
        # do it one last time for the gathered lines remaining
        if account_lines:
            new_lines.extend(compute_hierarchy(account_lines, current_level + 1, parent_id))
        return new_lines
