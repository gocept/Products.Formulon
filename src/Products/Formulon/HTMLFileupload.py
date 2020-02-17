# Formulon - Let's you manage Forms on the ZOPE Application Server
# Copyright (C) gocept gmbh & co. kg, http://www.gocept.com/
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
## Module for Fileupload
#
# $Id$

__doc__="""HTMLWidget Fileupload module."""
__version__='2.1'

import OFS.SimpleItem
import Acquisition
import AccessControl
import ZPublisher.HTTPRequest
from Globals import HTMLFile, MessageDialog, Persistent, InitializeClass

from WidgetBase import WidgetBase, ValidationError, TALESMethod
from IWidget import IWidget

manage_addHTMLFileuploadForm=HTMLFile('dtml/HTMLFileuploadAdd', globals())

def manage_addHTMLFileupload(self, id, REQUEST=None):
    """ This will instanciate a new Fileupload Widget in the ZODB"""
    self._setObject(id, HTMLFileupload(id, REQUEST))
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(self.absolute_url()+"/manage_visualEdit")

class HTMLFileupload(WidgetBase, OFS.SimpleItem.Item, Persistent,
                     Acquisition.Implicit, AccessControl.Role.RoleManager):
    """HTMLWidget for Fileuploads"""

    __implements__ = IWidget

    security = AccessControl.ClassSecurityInfo()

    meta_type = 'HTML Fileupload'
    css_class = 'FormFileupload'
    
    colspan = 1
    required = 0
    aliases = []
        
    security.declareProtected('View management screens', 'manage_properties')
    manage_properties=HTMLFile('dtml/HTMLFileuploadEdit', globals())
    
    manage_options=(
        {'label':'Properties', 'action':'manage_properties'},
        {'label':'Security', 'action':'manage_access'},
        )

    ################ Here comes Zope specific code

    def __init__(self, id, REQUEST):
        self.id = id
        self.__version__ = __version__
        if REQUEST is not None:
            self.changeProperties(REQUEST)

    security.declareProtected('Change Formulon instances', 'manage_edit')
    def manage_edit(self, REQUEST=None):
        """ set the new properties """
        if REQUEST is not None:
            self.changeProperties(REQUEST)
            return MessageDialog(title='Edited',
                message="Properties for %s changed." % self.id,
                action='./manage_properties' )
                    
    security.declareProtected('Change Formulon instances', 'changeProperties')
    def changeProperties(self, REQUEST=None, encoding='iso-8859-1'):
        if REQUEST is None:
            return
        # Update the base properties
        self.changeBaseProperties(REQUEST, encoding)

        self.title = unicode(REQUEST.title, encoding)
        self.column=REQUEST.column
        if self.column<1:
            self.column=1
        self.row=REQUEST.row
        if self.row<1:
            self.row=1
        self.colspan=REQUEST.colspan
                    
        self.required=0
        if REQUEST.has_key('required'):
            self.required=1

        self.aliases = REQUEST.aliases
        
        # Update TALES Methods
        for x in ['hint']:
            expression = REQUEST.get(x)
            if expression is None:
                continue
            setattr(self, x, TALESMethod(unicode(expression, encoding)))
            

    ################# Here comes the widget specific code
    security.declareProtected('View', 'render')
    def render(self, parent, tabindex=None):
        doc = parent.ownerDocument
        widget = parent.appendChild(doc.createElement('input'))
        set = widget.setAttribute
        if tabindex is not None:
            set('tabindex', str(tabindex))
        set('name', self.id+"_value")
        set('type', 'file')
        set('class', self.css_class)
        set("onChange", "reportChange(this)")
        return widget
    
    security.declareProtected('View', 'validate')
    def validate(self, against):
        filename = ''
        against = against.get('value')

        if isinstance(against, ZPublisher.HTTPRequest.FileUpload):
            filename = against.filename

        if self.required and not filename:
            raise ValidationError(self.callMethod(self.hint))
        return against

    security.declareProtected('View', 'height')
    def height(self):
        return 1

    security.declareProtected('View', 'getValue')
    def getValue(self):
        if self.REQUEST.has_key(self.id):
            return self.REQUEST[self.id]
        else:
            return None

InitializeClass(HTMLFileupload)
