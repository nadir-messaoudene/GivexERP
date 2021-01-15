#**************************************************************************
#* PR1 CONFIDENTIAL - Copyrighted Code - Do not re-use. Do not distribute.
#* __________________
#*  [2019] PR1 (pr1.xyz) -  All Rights Reserved. 
#* NOTICE:  All information contained herein is, and remains the property of PR1 and its suppliers, if any.  The intellectual and technical concepts contained herein are proprietary to PR1.xyz and its holding company and are protected by trade secret or copyright law. Dissemination of this information, copying of the concepts used or reproduction of any part of this material in any format is strictly forbidden unless prior written permission is obtained from PR1.xyz.
#**************************************************************************
from odoo import api, fields, models
class general_config(models.Model):
    _name = "pr1_iframe_forms.general_config" 
    _description = "General Config"
    #additional_css_files=fields.Char('Additional CSS Files', help="If you want to load in additional CSS files please list the URLs in here as comma seperated CSS")
    name=fields.Char("Name")
    css_class_substitutes = fields.One2many('pr1_iframe_forms.css_class_substitue', 'general_config_id', "Substitute CSS class names")
    add_links = fields.One2many('pr1_iframe_forms.add_link', 'general_config_id', "Additional CSS Link files to add")
    @api.model
    def get_config(self):
        records=self.sudo().search([('name','=','Default')])
        if(len(records)>0):
            return records[0]
        else:
            self.create({'name':'Default'})
            return False