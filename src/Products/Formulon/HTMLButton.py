# Formulon - Let's you manage Forms on the ZOPE Application Server
# Copyright (C) 2001-2010 Christian Theune, gocept gmbh & co. kg
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
## Module for Button-Widgets
#
# $Id$

__doc__ = """HTMLWidget Button module."""
__version__ = '2'

import Acquisition
import AccessControl
import OFS.SimpleItem
from Globals import HTMLFile, MessageDialog, Persistent, InitializeClass
from OFS.DTMLDocument import DTMLDocument
from ComputedAttribute import ComputedAttribute
from WidgetBase import WidgetBase
from IWidget import IWidget

manage_addHTMLButtonForm=HTMLFile('dtml/HTMLButtonAdd', globals())
def manage_addHTMLButton(self, id, REQUEST=None):
    """Add a new HTML Button to the Folder."""
    self._setObject(id, HTMLButton(id, REQUEST))
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(self.absolute_url()+"/manage_visualEdit")

class HTMLButton(WidgetBase, OFS.SimpleItem.Item, Persistent, Acquisition.Implicit, \
            AccessControl.Role.RoleManager):
    """HTMLWidget for Buttons"""

    __implements__ = IWidget
        
    security = AccessControl.ClassSecurityInfo()
    
    meta_type = 'HTML Button'
    css_class = 'FormButton'
    user_css = ''
    
    colspan=0
    hint = ''
    
    
    title = u""
    
    aliases = []
   
    security.declareProtected('View management screens', 'manage_properties')
    manage_properties=HTMLFile('dtml/HTMLButtonEdit', globals())
    
    manage_options=(
        {'label':'Properties', 'action':'manage_properties'},
        {'label':'Security', 'action':'manage_access'},
        )

    ########### Zopish management stuff
    def __init__(self, id, REQUEST=None):
        self.id = id
        self.__version__ = __version__
        if REQUEST is not None:
            self.changeProperties(REQUEST)

    def title_or_id(self):
        return self.value

    security.declareProtected('Change Formulon instances', 'manage_edit')
    def manage_edit(self, REQUEST=None):
        """Save edited properties."""
        self.changeProperties(REQUEST)
        return MessageDialog(title='Edited', 
            message="Properties for %s changed." % (self.id, ), 
            action='./manage_properties')

    security.declareProtected('Change Formulon instances', 'changeProperties')
    def changeProperties(self, REQUEST=None, encoding='iso-8859-1'):
        # iso-8859 is ZMI's encoding.
        if REQUEST is not None:
            # Update the base properties
            self.changeBaseProperties(REQUEST, encoding)
            
            self.type = REQUEST.type
            self.value = unicode(REQUEST.value, encoding)
            self.user_css = unicode(REQUEST.user_css, encoding)
            
            self.column = REQUEST.column
            if self.column < 1:
                self.column = 1
            
            self.row = REQUEST.row
            if self.row < 1:
                self.row = 1
            
            self.colspan = REQUEST.colspan
            if REQUEST.has_key('isimg'):
                self.isimg = 1
            else:
                self.isimg = 0
            
            self.imgsrc = REQUEST.imgsrc
            self.aliases = REQUEST.aliases

    
    ############ Here comes the widget specific code
    security.declareProtected('View', 'render')
    def render(self, parent, tabindex=None):
        node = parent.appendChild(parent.ownerDocument.createElement("input"))
        
        if self.type=='submit' and self.isimg:
            node.setAttribute("type","image")
            node.setAttribute("src",self.imgsrc)
        else:
            node.setAttribute("type", self.type)
        if not tabindex is None:
            node.setAttribute("tabindex", str(tabindex))

        if not self.type=='submit':
            node.setAttribute("onClick", "resetForm()")

        if self.user_css:
            node.setAttribute("class", self.user_css)
        else:
            node.setAttribute("class", self.css_class)
            
        node.setAttribute("name", self.id+"_value")
        node.setAttribute("value",self.value)
        return node

    security.declareProtected('View', 'validate')
    def validate(self, against=None):
        return against 

    security.declareProtected('View', 'height')
    def height(self):
        return 1

    security.declareProtected('View', 'getValue')
    def getValue(self):
        return self.value

InitializeClass(HTMLButton)

