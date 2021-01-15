#**************************************************************************
#* PR1 CONFIDENTIAL - Copyrighted Code - Do not re-use. Do not distribute.
#* __________________
#*  [2019] PR1 (pr1.xyz) -  All Rights Reserved. 
#* NOTICE:  All information contained herein is, and remains the property of PR1 and its suppliers, if any.  The intellectual and technical concepts contained herein are proprietary to PR1.xyz and its holding company and are protected by trade secret or copyright law. Dissemination of this information, copying of the concepts used or reproduction of any part of this material in any format is strictly forbidden unless prior written permission is obtained from PR1.xyz.
#**************************************************************************
from odoo import api, fields, models
class css_class_substitue(models.Model):
    _name = "pr1_iframe_forms.css_class_substitue" 
    _description = "CSS Class Substitute"
    class_to_replace=fields.Char("Class to replace",help="Enter the name of the css class you wish to replace e.g. col-lg-3",required=True)
    class_to_replace_with=fields.Char("Class to replace with",help="Enter the name of the css class you wish to change the class to replace with e.g. to change col-lg-3 to col-lg-4 simply put in col-lg-4",default="")
    general_config_id = fields.Many2one('pr1_iframe_forms.general_config', 'Config')