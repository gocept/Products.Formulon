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
# Module for Textarea-Widgets
#
# $Id$

__doc__="""HTMLWidget Textarea module."""
__version__='2.1'

import re

import OFS.SimpleItem
import Acquisition
import AccessControl
from Globals import HTMLFile, MessageDialog, Persistent, InitializeClass
from DocumentTemplate.html_quote import html_quote

from WidgetBase import WidgetBase, ValidationError, TALESMethod
from IWidget import IWidget

manage_addHTMLTextareaForm=HTMLFile('dtml/HTMLTextareaAdd', globals())
def manage_addHTMLTextarea(self, id, REQUEST=None):
    """Adds a new HTML Textarea Widget."""
    self._setObject(id, HTMLTextarea(id, REQUEST))
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(self.absolute_url()+"/manage_visualEdit")

class HTMLTextarea(WidgetBase, OFS.SimpleItem.Item, Persistent,
        Acquisition.Implicit, AccessControl.Role.RoleManager):
    """HTMLWidget for Textareas"""

    __implements__ = IWidget

    security = AccessControl.ClassSecurityInfo()

    security.declareProtected('View management screens', 'manage_properties')
    security = AccessControl.ClassSecurityInfo()

    meta_type = 'HTML Textarea'
    css_class = 'FormTextarea'
    user_css = ''
    aliases = []

    colspan=0
    wrapping='virtual'

    manage_properties=HTMLFile('dtml/HTMLTextareaEdit', globals())

    manage_options=(
        {'label':'Properties', 'action':'manage_properties'},
        {'label':'Security', 'action':'manage_access'},
    )

    ################## Some zopish management stuff

    def __init__(self, id, REQUEST=None):
        self.id = id
        self.__version__ = __version__
        if REQUEST is not None:
            self.changeProperties(REQUEST)

    def __setstate__(self, state):
        HTMLTextarea.inheritedAttribute('__setstate__')(self, state)
        self._update_cache()

    security.declareProtected('Change Formulon instances', 'manage_edit')
    def manage_edit(self, REQUEST=None):
        """Sets the new properties."""
        if REQUEST is not None:
            self.changeProperties(REQUEST)
            return MessageDialog(title='Edited',
                message="Properties for %s changed." % self.id,
                action='./manage_properties')

    security.declareProtected('Change Formulon instances', 'changeProperties')
    def changeProperties(self, REQUEST, encoding='iso-8859-1'):
        if REQUEST is None:
            return

        # Update the base properties
        self.changeBaseProperties(REQUEST, encoding)

        self.title = unicode(REQUEST.title, encoding)
        self.cols = REQUEST.cols
        self.rows = REQUEST.rows
        self.colspan=REQUEST.colspan
        self.aliases = REQUEST.aliases
        self.user_css = unicode(REQUEST.user_css, encoding)

        self.column=REQUEST.column
        if self.column<1:
            self.column=1

        self.row=REQUEST.row
        if self.row<1:
            self.row=1

        if REQUEST.has_key("wrapping"):
            self.wrapping=REQUEST["wrapping"]

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


    #################### The widget specific code

    security.declareProtected('View', 'render')
    def render(self, parent, tabindex=None):
        doc = parent.ownerDocument
        node = parent.appendChild(doc.createElement("textarea"))
        if tabindex is not None:
            node.setAttribute("tabindex",str(tabindex))
        if self.user_css:
            node.setAttribute("class", self.user_css)
        else:
            node.setAttribute("class", self.css_class)

        node.setAttribute("name", self.id+"_value")
        node.setAttribute("cols", str(self.cols))
        node.setAttribute("rows", str(self.rows))
        node.setAttribute("wrapping", self.wrapping)
        node.setAttribute("onChange", "reportChange(this)")
        node.appendChild(doc.createTextNode(self.value()))
        return node

    security.declareProtected('View', 'validate')
    def validate(self, against=None):
        __traceback_info__ = self.getId(), against
        against = against["value"]
        if isinstance(against, str):
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
        height = self.rows-2
        if height < 1:
            height = 1
        return height

    security.declareProtected('View', 'value')
    def value(self):
        try:
            a = self.REQUEST['__source_data__'][self.id]
            if a is None:
                a = ''
            return a
        except KeyError:
            pass
        try:
            return self.REQUEST[self.id]
        except KeyError:
            pass
        return self.callMethod(self.default)

    security.declareProtected('View', 'getValue')
    getValue = value

InitializeClass(HTMLTextarea)

