#**************************************************************************
#* PR1 CONFIDENTIAL - Copyrighted Code - Do not re-use. Do not distribute.
#* __________________
#*  [2019] PR1 (pr1.xyz) -  All Rights Reserved. 
#* NOTICE:  All information contained herein is, and remains the property of PR1 and its suppliers, if any.  The intellectual and technical concepts contained herein are proprietary to PR1.xyz and its holding company and are protected by trade secret or copyright law. Dissemination of this information, copying of the concepts used or reproduction of any part of this material in any format is strictly forbidden unless prior written permission is obtained from PR1.xyz.
#**************************************************************************
from odoo import api, fields, models
class add_link(models.Model):
    _name = "pr1_iframe_forms.add_link" 
    _description = "Additional Link"
    path_to_link=fields.Char('Path to link', help="To add additional link files please enter the full path here",required=True)
    general_config_id = fields.Many2one('pr1_iframe_forms.general_config', 'Config')