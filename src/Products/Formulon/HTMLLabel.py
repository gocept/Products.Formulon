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
# Module for Label-Widgets
#
# $Id$

__doc__ = """HTMLLabel Button module."""
__version__ = '3'

import OFS.SimpleItem
import Acquisition
import AccessControl
from Globals import HTMLFile, MessageDialog, Persistent, InitializeClass

from WidgetBase import WidgetBase
from IWidget import IWidget

manage_addHTMLLabelForm=HTMLFile('dtml/HTMLLabelAdd', globals())

def manage_addHTMLLabel(self, id, REQUEST=None):
    """Adds a new HTML Label to the Folder."""
    self._setObject(id, HTMLLabel(id, REQUEST))
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(self.absolute_url()+"/manage_visualEdit")

class HTMLLabel(WidgetBase, OFS.SimpleItem.Item, Persistent,
        Acquisition.Implicit, AccessControl.Role.RoleManager):
    """HTMLWidget for Labels"""

    __implements__ = IWidget

    security = AccessControl.ClassSecurityInfo()

    meta_type = 'HTML Label'
    css_class = 'FormLabel'
    user_css = ""
    colspan = -1
    aliases = []

    security.declareProtected('View management screens', 'manage_properties')
    manage_properties=HTMLFile('dtml/HTMLLabelEdit', globals())

    manage_options=(
        {'label':'Properties', 'action':'manage_properties'},
        {'label':'Security', 'action':'manage_access'},
        )

    ########### Zopish management stuff


    def __init__(self, id, REQUEST=None):
        self.id=id
        self.__version__ = __version__
        if REQUEST is not None:
            self.changeProperties(REQUEST)

    security.declareProtected('Change Formulon instances', 'manage_edit')
    def manage_edit(self, REQUEST=None):
        """ set the new properties """
        if REQUEST is not None:
            self.changeProperties(REQUEST)
            return MessageDialog(title='Edited',
                message="Properties for %s changed." % (self.id, ),
                action='./manage_properties')

    security.declareProtected('Change Formulon instances', 'changeProperties')
    def changeProperties(self, REQUEST=None, encoding='iso-8859-1'):
        if REQUEST is not None:
            # Update the base properties
            self.changeBaseProperties(REQUEST, encoding)

            self.value=unicode(REQUEST.value, encoding)
            self.title = self.value
            self.column=REQUEST.column
            self.user_css=REQUEST.user_css
            if self.column<1:
                self.column=1
            self.row=REQUEST.row
            if self.row<1:
                self.row=1
            self.colspan=REQUEST.colspan

    def title_or_id(self):
        assert isinstance(self.value, unicode)
        return self.value

    security.declareProtected('View', 'validate')
    def validate(self, against):
        return against

    security.declareProtected('View', 'height')
    def height(self):
        return 1

    security.declareProtected('View', 'render')
    def render(self, parent, tabindex=None):
        node = parent.appendChild(parent.ownerDocument.createElement("span"))

        if self.user_css:
            node.setAttribute("class", self.user_css)
        else:
            node.setAttribute("class", self.css_class)

        node.appendChild(parent.ownerDocument.createTextNode(self.value))
        return node


    security.declareProtected('View', 'getValue')
    def getValue(self):
        return None

InitializeClass(HTMLLabel)

