
from lxml import etree
from io import StringIO
import odoo
from odoo import fields
from odoo.http import Response

def remove_elements(tree,xpath):
    for itm in tree.xpath(xpath):
        try:
            tree.remove(itm)
        except:
            pass
def set_attribute(tree,xpath,attribute,value):
        try:
            tree.xpath(xpath)[0].set(attribute,value)
        except:
            pass
        
import lxml.html

def flatten(self):
    """ Forces the rendering of the response's template, sets the result
    as response body and unsets :attr:`.template`
    """
    if self.template:
        data=self.render()
        self.template = None
        from odoo.http import request
        if(request.httprequest.path != "/web" and str(request.httprequest.query_string).find("iframe=0")==-1 and str(data).find("<!DOCTYPE html")!=-1 and ( str(request.httprequest.query_string).find("iframe=1")!=-1 or ("iframe" in request.httprequest.session and request.httprequest.session["iframe"]==1))):
            request.httprequest.session["iframe"]=1
            parser = etree.HTMLParser()
            tree   = etree.parse(StringIO(data.decode('utf8')), parser)            
            remove_elements(tree.xpath("//head")[0], "//meta")
            remove_elements(tree.xpath("//body")[0], "//nav")
            remove_elements(tree.xpath("//body//div[@id='wrapwrap']")[0], "//header")
            remove_elements(tree.xpath("//body//div[@id='wrapwrap']")[0], "//footer")
            set_attribute(tree, "//div[@id='wrapwrap']", 'class', '')
            set_attribute(tree, "//div[@id='wrapwrap']", 'style', 'min-height:auto;')
            set_attribute(tree, "//body", 'class', '')
            set_attribute(tree, "//body", 'style', 'height:auto;min-height:auto;')
            set_attribute(tree, "//html", 'style', 'height:auto;min-height:auto;')
            config = request.env['pr1_iframe_forms.general_config'].get_config()
            head_elem = tree.find(".//head")
            if(len(config.add_links)>0):
                for olink in config.add_links:
                    if(olink.path_to_link!=False and olink.path_to_link!="" and olink.path_to_link!=None):
                        link = lxml.html.fromstring(olink.path_to_link).find('.//link')
                        head_elem.append(link)
                    
            if(len(config.css_class_substitutes)>0):
                for sub in config.css_class_substitutes:
                    if(sub.class_to_replace!=False and sub.class_to_replace !=None and sub.class_to_replace!=""):
                        items_to_replace = tree.xpath("//*[contains(concat(' ', normalize-space(@class), ' '), '"+sub.class_to_replace+"')]")
                        for item in items_to_replace:
                            if(sub.class_to_replace_with==False or sub.class_to_replace_with==None):
                                sub.class_to_replace_with=""
                            item.attrib['class'] = item.attrib['class'].replace(sub.class_to_replace,sub.class_to_replace_with)
                        
            new_data = etree.tostring(tree,method="html") 
            self.response.append(new_data)
        elif(str(data).find("<!DOCTYPE html")!=-1 and ( str(request.httprequest.query_string).find("iframe=0")!=-1)):
            request.httprequest.session["iframe"]=0
            self.response.append(data)
        else:
            self.response.append(data)
        
Response.flatten = flatten

