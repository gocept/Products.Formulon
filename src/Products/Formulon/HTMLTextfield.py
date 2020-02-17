# Formulon - Lets you manage forms on the ZOPE Application Server
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
#
# Module for Textfield-Widgets
#
# $Id$

__doc__="""HTMLWidget Textfield module."""
__version__ = '2.1'

import AccessControl
from Globals import HTMLFile, MessageDialog, Persistent, InitializeClass

import OFS.SimpleItem, Acquisition, AccessControl, re

from WidgetBase import ValidationError, WidgetBase, TALESMethod
from IWidget import IWidget

from types import StringType, StringTypes

manage_addHTMLTextfieldForm=HTMLFile('dtml/HTMLTextfieldAdd', globals())
def manage_addHTMLTextfield(dispatcher, id, REQUEST=None):
    """HTML Textfield factory"""
    dispatcher._setObject(id, HTMLTextfield(id))
    
    if REQUEST is not None:
        tf = getattr(dispatcher, id)
        tf.changeProperties(REQUEST)
        REQUEST.RESPONSE.redirect(dispatcher.absolute_url()+"/manage_visualEdit")

class HTMLTextfield(WidgetBase, OFS.SimpleItem.Item, Persistent, 
        Acquisition.Implicit, AccessControl.Role.RoleManager):
    """HTMLWidget for Textfields"""
    
    __implements__ = IWidget
    
    security = AccessControl.ClassSecurityInfo()
    
    meta_type='HTML Textfield'
    css_class='FormTextfield'
    colspan=0
    aliases = []

    security.declareProtected('View management screens', 'manage_properties')
    manage_properties=HTMLFile('dtml/HTMLTextfieldEdit', globals())
    
    manage_options=(
        {'label':'Properties', 'action':'manage_properties'},
        {'label':'Security', 'action':'manage_access'},
    )
    
    def __init__(self, id):
        self.id = id
        self.__version__ = __version__

    def __setstate__(self, state):
        HTMLTextfield.inheritedAttribute('__setstate__')(self, state)
        self._update_cache()

    security.declareProtected('Change Formulator instances', 'manage_edit')
    def manage_edit(self, REQUEST=None):
        """Set the new properties."""
        if REQUEST is not None:
            self.changeProperties(REQUEST)
            return MessageDialog(title='Edited',
                message="Properties for %s changed." % self.id,
                action='./manage_properties')
    
    security.declareProtected('Change Formulon instances', 'changeProperties')
    def changeProperties(self, REQUEST=None, encoding='iso-8859-1'):
        if REQUEST is None:
            return
        
        # Update the base properties
        self.changeBaseProperties(REQUEST, encoding)

        self.maxlength = REQUEST.maxlength
        self.size = REQUEST.size
        self.title = unicode(REQUEST.title, encoding)
        self.colspan = REQUEST.colspan
        self.aliases = REQUEST.aliases
        
        self.column = REQUEST.column
        if self.column < 1:
            self.column = 1
        
        self.row = REQUEST.row
        if self.row < 1:
            self.row = 1
        
        self.ispassword = 0
        if REQUEST.has_key('ispassword'):
            self.ispassword = 1

        # Update TALES Methods
        tales = ['default', 'regexp', 'hint']
        for x in tales:
            expression = REQUEST.get(x)
            if expression is None:
                continue
            setattr(self, x, TALESMethod(unicode(expression, encoding)))

        # cache the compiled regular expression:
        self._update_cache()

    def _update_cache(self):
        """Compiles a volatile attribute for caching the regex."""
        self._v_regex = self._compile_regex()

    def _compile_regex(self, force=False):
        """Compiles the regex attribute.

        If force is False regex is only compiled if it starts with 'string:'.
        (This is for the cache.)
        """
        if force or self.regexp.getExpression().startswith('string:'):
            try:
                return re.compile(self.callMethod(self.regexp), re.DOTALL)
            except AttributeError:
                # happens creating new widget because callMethod needs aq_parent
                return None

    security.declareProtected('View', 'render')
    def render(self, parent, tabindex=None):
        doc = parent.ownerDocument
        
        # Attributes must be str/unicode
        value = self.value()
        if not type(value) in StringTypes:
            value = str(value)

        node = parent.appendChild(doc.createElement("input"))
        if (self.ispassword == 1):
            node.setAttribute("type", "password")
        else:
            node.setAttribute("type", "text")
            node.setAttribute("value", value)

        if tabindex is not None:
            node.setAttribute("tabindex", str(tabindex))

        node.setAttribute("name", self.id+"_value")
        node.setAttribute("size", str(self.size))
        node.setAttribute("maxlength", str(self.maxlength))
        node.setAttribute("class", str(self.css_class))
        node.setAttribute('onChange', "reportChange(this)")
        return node

    security.declareProtected('View', 'validate')
    def validate(self, against):
        try:
            against = against["value"]
        except TypeError:
            raise ValueError(
                'Expected mapping with "value" key, got %r.' % against)
        except KeyError:
            print "WARNING: HTMLTextfield '%s' is behind another widget, "\
                  "please correct in VisualEditor." % self.id
            against = ''
        if type(against) is StringType:
            against = unicode(against, self.site_encoding)

        regex = getattr(self, '_v_regex', None)
        if regex is None:
            regex = self._compile_regex()
            if regex is not None: # starts with 'string:' so save it
                self._v_regex = regex
            else:
                regex = self._compile_regex(force=True)
        if not len(regex.findall(against)):
            raise ValidationError(self.callMethod(self.hint))

        return against
    
    security.declareProtected('View', 'height')
    def height(self):
        return 1

    security.declareProtected('View', 'value')
    def value(self):
        value = None
        value = self.REQUEST.get('__source_data__', {}).get(self.id)
        if value is None:
            value = self.REQUEST.get(self.id)
        if value is None:
            value = self.callMethod(self.default)
        return value

    security.declareProtected('View', 'getValue')
    getValue = value

InitializeClass(HTMLTextfield)
        
