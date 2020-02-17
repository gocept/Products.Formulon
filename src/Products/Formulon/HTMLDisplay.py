# Formulon - Lets you manage Forms on the ZOPE Application Server
# Copyright (C) 2001-2010 Christian Theune, gocept gmbh & co. kg,
#                         Michael Howitz, gocept gmbh & co. kg
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
## Module for Display-Widgets
#
# $Id$

__doc__ = """HTMLWidget Display module."""
__version__ = '2'

import Acquisition
import AccessControl
import OFS.SimpleItem
from Globals import HTMLFile, MessageDialog, Persistent, InitializeClass
from OFS.DTMLDocument import DTMLDocument

from types import StringTypes, ListType, TupleType, StringType
from WidgetBase import WidgetBase
from IWidget import IWidget

manage_addHTMLDisplayForm=HTMLFile('dtml/HTMLDisplayAdd', globals())
def manage_addHTMLDisplay(self, id, REQUEST=None):
    """Add a new Display to the Folder."""
    self._setObject(id, HTMLDisplay(id, REQUEST))
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(self.absolute_url()+"/manage_visualEdit")

class HTMLDisplay(WidgetBase, OFS.SimpleItem.Item, Persistent, Acquisition.Implicit, \
            AccessControl.Role.RoleManager):
    """Widget for Displays"""

    __implements__ = IWidget
        
    security = AccessControl.ClassSecurityInfo()
    
    meta_type='HTML Display'
    css_class='FormDisplay'
    
    colspan=0
    title = hint = ''
    
    aliases = []
   
    security.declareProtected('View management screens', 'manage_properties')
    manage_properties=HTMLFile('dtml/HTMLDisplayEdit', globals())
    
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
        return self.title

    security.declareProtected('Change Formulon instances', 'manage_edit')
    def manage_edit(self, REQUEST=None):
        """Save edited properties."""
        self.changeProperties(REQUEST)
        return MessageDialog(title='Edited', 
            message="Properties for %s changed." % (self.id, ), 
            action='./manage_properties')

    security.declareProtected('Change Formulon instances', 'changeProperties')
    def changeProperties(self, REQUEST=None, encoding="iso-8859-1"):
        if REQUEST is not None:
            # Update the base properties
            self.changeBaseProperties(REQUEST, encoding)

            self.title = unicode(REQUEST.title, encoding)
            
            self.column = REQUEST.column
            if self.column < 1:
                self.column = 1
            
            self.row = REQUEST.row
            if self.row < 1:
                self.row = 1
            
            self.colspan = REQUEST.colspan
            self.cssclass = REQUEST.cssclass
            self.aliases = REQUEST.aliases
            self.false = unicode(REQUEST.false, encoding)

    ############ Here comes the widget specific code
    security.declareProtected('View', 'render')
    def render(self, parent, tabindex=None):
        data = self.getValue()

        # make data displayable
        if not data and self.false:
            data = self.false
        elif type(data) in StringTypes:
            # Already a string? Don't do anything
            pass
        elif type(data) in (ListType, TupleType):
            data = ", ".join(data)
        else:
            data = str(data)

        if data.startswith('http://') or "@" in data:
                node = parent.appendChild(parent.ownerDocument.createElement("a"))
                if "@" in data:
                        node.setAttribute("href", "mailto:"+data)
                else:
                        node.setAttribute("href", data)
                        node.setAttribute("target", "blank")
        else:
                node = parent.appendChild(parent.ownerDocument.createElement("span"))
                
        # We need to store our display value ...
        hidden = node.appendChild(parent.ownerDocument.createElement("input"))
        hidden.setAttribute("type", "hidden")
        hidden.setAttribute("name", self.id + "_value")
        hidden.setAttribute("value", data)

        if self.cssclass:
            node.setAttribute("class", self.cssclass)
                
        # For display, we need to break the textnode into parts at the linebreaks
        parts = data.split("\n")

        while len(parts) > 1:
            part = parts.pop(0)
            node.appendChild(parent.ownerDocument.createTextNode(part))
            node.appendChild(parent.ownerDocument.createElement("br"))
        node.appendChild(parent.ownerDocument.createTextNode(parts[0]))

        return node

    security.declareProtected('View', 'validate')
    def validate(self, against=None):
        __traceback_info__ = (self.id, against)
        return against["value"]

    security.declareProtected('View', 'height')
    def height(self):
        return 1

    security.declareProtected('View', 'getValue')
    def getValue(self):
        value = self.REQUEST['__source_data__'].get(self.id, "")
        if type(value) is StringType:
                value = unicode(value, self.site_encoding)
        return value

InitializeClass(HTMLDisplay)

