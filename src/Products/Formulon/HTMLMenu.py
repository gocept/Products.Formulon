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
# Module for Menu-Widgets
#
# $Id$

__doc__="""HTMLWidget Menu module."""
__version__='2.1'

import re
import pickle
import base64
import math
from types import TupleType, ListType, IntType, StringType, UnicodeType

import Acquisition
import AccessControl
from OFS.SimpleItem import Item
from Globals import HTMLFile, MessageDialog, Persistent, InitializeClass
from ZPublisher.mapply import mapply
from ZPublisher.Publish import call_object, missing_name, dont_publish_class

from WidgetBase import WidgetBase, TALESMethod, ValidationError, \
    makeListOfTuples
from IWidget import IWidget

manage_addHTMLMenuForm=HTMLFile('dtml/HTMLMenuAdd', globals())

class NotEnoughSelections(ValidationError):
    """raised if fewer selected than allowed"""

    def getHint(self):
        return "It is not possible to select less than %i entries" % (
            self.args[0], )

class ItemNotSelectable(ValidationError):
    """raised if a selected item is not selectable"""

    def getHint(self):
        id, title = self.args
        return "The selected item is not allowed to be selected (%s)." % (
            title, )

def manage_addHTMLMenu(self, id, REQUEST=None):
    """Adds a HTML menu to the folder."""
    self._setObject(id, HTMLMenu(id, REQUEST))
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(self.absolute_url()+"/manage_visualEdit")

def serializeValue(value):
    return base64.encodestring(pickle.dumps(value)).strip().replace('\n', '')


class HTMLMenu(WidgetBase, Item, Persistent,
        Acquisition.Implicit, AccessControl.Role.RoleManager):
    """HTMLWidget for Menues"""

    __implements__ = IWidget

    security = AccessControl.ClassSecurityInfo()

    meta_type = 'HTML Menu'
    css_class = 'FormMenu'
    usercss = ''

    security.declareProtected('View management screens', 'manage_properties')
    manage_properties=HTMLFile('dtml/HTMLMenuEdit', globals())

    manage_options=(
        {'label':'Properties', 'action':'manage_properties'},
        {'label':'Security', 'action':'manage_access'},
        )

    ########### Zopish management stuff

    def __init__(self, id, REQUEST=None):
        self.id = id
        self.__version__ = __version__

        self.aliases = []

        self.source = None
        self.default = None
        self.hint = None

        self.allowzero = 0
        self.zerodata = None
        self.zerotitle = ''

        self.required = 1
        self.ismenu = 1

        self.size = 5
        self.buttonColumns = 3
        self.colspan = 0

        self.column = 1
        self.row = 1
        self.multiple = 0
        self.providezero = 0

        self.allowAdd = 0
        self.addMethod = None

        self.usercss = ''

        if REQUEST is not None:
            self.changeProperties(REQUEST)

    security.declareProtected('Change Formulon instances', 'manage_edit')
    def manage_edit(self, REQUEST=None):
        """Sets the new properties."""
        if REQUEST is not None:
            self.changeProperties(REQUEST)
            return MessageDialog(title='Edited', \
                message="Properties for %s changed."%self.id, \
                action='./manage_properties')

    security.declareProtected('Change Formulon instances',
        'changeProperties')
    def changeProperties(self, REQUEST=None, encoding='iso-8859-1', **kw):
        if REQUEST is not None:
            for key, value in REQUEST.items():
                kw[key] = value
        # Update the base properties
        self.changeBaseProperties(kw, encoding)

        title = kw.get('title')
        if title is not None:
            self.title = unicode(title, encoding)
        aliases = kw.get('aliases', self.aliases)
        assert isinstance(aliases, (list, tuple))
        aliases = tuple(aliases)
        self.aliases = aliases

        column = kw.get('column', self.column)
        assert isinstance(column, int)
        assert column >= 1
        self.column = column

        row = kw.get('row', self.row)
        assert isinstance(row, int)
        assert row >= 1
        self.row = row

        self.colspan = kw.get('colspan', self.colspan)

        default = kw.get('default')
        if default is not None:
            self.default = TALESMethod(unicode(default, encoding))

        source = kw.get('source')
        if source is not None:
            self.source = TALESMethod(unicode(source, encoding))

        size = kw.get('size', self.size)
        assert isinstance(size, int)
        assert size >= 1
        self.size = size

        buttonColumns = kw.get('buttonColumns', self.buttonColumns)
        assert isinstance(buttonColumns, int)
        assert buttonColumns >= 1
        self.buttonColumns = buttonColumns

        zerodata = kw.get('zerodata')
        if zerodata is not None:
            self.zerodata = TALESMethod(unicode(zerodata,
                encoding))
        zerotitle = kw.get('zerotitle')
        if zerotitle is not None:
            self.zerotitle = unicode(zerotitle, encoding)

        required = kw.get('required', self.required)
        assert isinstance(required, int)
        assert required >= 0
        self.required = required

        self.ismenu = kw.get('ismenu', self.ismenu)
        self.multiple = kw.get('multiple', self.multiple)
        self.providezero = kw.get('providezero', self.providezero)
        self.allowzero = kw.get('allowzero', self.allowzero)

        # Update TALES Methods
        tales = ['hint']
        for x in tales:
            expression = REQUEST.get(x)
            if expression is None:
                continue
            setattr(self, x, TALESMethod(unicode(expression, encoding)))

        # Magic adding
        allowAdd  = kw.get('allowAdd', self.allowAdd)
        assert isinstance(allowAdd, int)
        self.allowAdd = allowAdd

        addMethod = kw.get('addMethod')
        if addMethod is not None:
            self.addMethod = TALESMethod(unicode(addMethod, encoding))

        # update CSS-Class
        usercss = kw.get('usercss')
        if usercss is not None:
            self.usercss = unicode(usercss, encoding)

    security.declareProtected('View', 'getOptionsValues')
    def getOptionsValues(self):
        """returns options values

            returns list of tuples: [(id, title), ...]
        """
        options = self.callMethod(self.source)
        if options is None:
            options = []
        else:
            options = makeListOfTuples(options,
                                       ("value", "title", "group"))
        return options

    security.declareProtected('View', 'getOptions')
    def getOptions(self):
        """returns list of tuples with all options

            returns [(id, title, selected, selectable, group), ...]
            whereby
                id is the raw id,
                title is the title,
                selected is true for all selected options,
                selectable is false for all non-selectable options,
                group is a string labelling a group or None if not
                    associated with a group
        """
        options = self.getOptionsValues()
        if self.providezero:
            zero_id = self.callMethod(self.zerodata)
            options.insert(0, (zero_id, self.zerotitle, None))

        selected = self.getSelected()
        # In general selected will be fairly small, thus this will be fast
        # enough.
        options = \
                map(lambda (id, title, group):
                    (id, title, id in selected, 1, group),
                    options)

        if not self.allowzero and self.providezero:
            id, title, selected, selectable, group = options[0]
            options[0] = id, title, selected, 0, group
        return options

    def _deserialize(self, data):
        options = self.getOptionsValues()
        zero_id = self.callMethod(self.zerodata)
        options.insert(0, (zero_id, self.zerotitle, None))
        s_data = {}
        for id, title, group in options:
            s_data[serializeValue(id)] = id
        return s_data.get(data, self)


    security.declareProtected('View', 'render')
    def render(self, parent, tabindex=None):
        if self.ismenu:
            widget = self._renderMenu(parent, tabindex)
        else:
            widget = self._renderButtons(parent, tabindex)
        return widget

    def _renderMenu(self, parent, tabindex=None):
        doc = parent.ownerDocument
        menu = parent.appendChild(doc.createElement('select'))
        set = menu.setAttribute
        set('size', str(self.size))
        set("class", "%s %s" % (self.css_class, self.usercss))
        if self.multiple:
            set('multiple', 'multiple')
            set('name', '%s_value:list' % (self.id, ))
        else:
            set('name', self.id+"_value")
        if tabindex is not None:
            set('tabindex', str(tabindex))
        set("onChange", "reportChange(this)")

        # Construct a hierarchy for the groups
        groups = {}
        for id, title, selected, selectable, group in self.getOptions():
            item = (id, title, selected, selectable)
            if groups.has_key(group):
                groups[group].append(item)
            else:
                groups[group] = [item]

        group_ids = groups.keys()
        group_ids.sort()
        for group in group_ids:
            if group is not None:
                optgroup = menu.appendChild(doc.createElement('optgroup'))
                optgroup.setAttribute("label", group)

            for id, title, selected, selectable in groups[group]:
                assert isinstance(title, (StringType, UnicodeType)), "The title-attribute of optionsource of %s is expected to be a (Unicode)String." % (self.__name__)
                option = menu.appendChild(doc.createElement('option'))
                set = option.setAttribute
                set('value', serializeValue(id))
                if selected:
                    set('selected', 'selected')
                if not selectable:
                    set('disabled', 'disabled')
                option.appendChild(doc.createTextNode(title))

        # Modify stuff if we are addable :) DOM forever!
        if self.allowAdd:
            hiddenContainer = doc.getElementById("hiddenContainer")

            # The optional input field
            addfield = hiddenContainer.appendChild(doc.createElement("input"))
            addfield.setAttribute("type", "text")
            addfield.setAttribute("name", self.getId()+"_add")
            addfield.setAttribute("id", self.getId()+"_add")

            # Add the switch link to the menu
            button = parent.appendChild(doc.createElement("button"))
            button.setAttribute("type", "button")
            button.setAttribute("id", self.getId()+"_button")
            button.setAttribute("onClick", "switchMenu('%s')" % self.getId())
            icon = button.appendChild(doc.createElement("img"))
            icon.setAttribute("src", "service_images/modules/controlling")

        return menu

    def _renderButtons(self, parent, tabindex=None):

        doc = parent.ownerDocument
        table = parent.appendChild(doc.createElement('table'))
        row = table.appendChild(doc.createElement('tr'))

        returnwidget = None
        buttons_rendered = 0
        for id, title, selected, selectable, group in self.getOptions():
            if buttons_rendered % self.buttonColumns == 0:
                row = table.appendChild(doc.createElement('tr'))
            widget = row.appendChild(doc.createElement('td')).appendChild(
                doc.createElement('input'))

            # The first one is representative
            if not returnwidget:
                returnwidget = widget

            widget_id = '%s_%s' % (self.id, buttons_rendered)
            set = widget.setAttribute
            if self.multiple:
                set('type', 'checkbox')
                set('name', '%s_value:list' % (self.id, ))
            else:
                set('type', 'radio')
                set('name', self.id+"_value")
            set('id', widget_id)
            set("class", "%s %s" % (self.css_class, self.usercss))
            set('value', serializeValue(id))
            if selected:
                set('checked', '1')
            if not selectable:
                set('disabled', 'disabled')
            if tabindex is not None:
                set('tabindex', str(tabindex))
            label = row.appendChild(doc.createElement('td')).appendChild(
                doc.createElement('label'))
            set = label.setAttribute
            set('for', widget_id)
            label.appendChild(doc.createTextNode(title))
            buttons_rendered += 1
        return returnwidget

    security.declareProtected('View', 'validate')
    def validate(self, value={}):
        """see IWidget

            value one or a list of serialized ids

            asserts that:
                - value is not None,
                - count == 1, if not multiple,
                - no unselectable item was selected
        """
        # XXX for now
        value = value.get("value", None)
        if value is None:
            value = []
        if not (isinstance(value, ListType) or
                isinstance(value, TupleType)):
            value = [value, ]
        required_selections = ((not self.multiple and 1) or
                               (self.multiple and self.required))
        if len(value) < required_selections:
            raise NotEnoughSelections(required_selections)
        d_value = \
            filter(lambda x: x is not self,
                   map(lambda x: self._deserialize(x),
                       value))

        # Hmm nothing here? This should be the same as selecting
        # a zero value
        if len(d_value) == 0 and self.providezero and self.allowzero:
            d_value = [self.callMethod(self.zerodata)]

        options = self.getOptions()
        for id, title, selected, selectable, group in options:
            if not selectable and id in d_value:
                raise ItemNotSelectable(id, title)
        if not self.multiple:
            try:
                return d_value[0]
            except IndexError:
                raise ItemNotSelectable(value[0], '<unknown>')
        return d_value


    security.declareProtected('View', 'height')
    def height(self):
        if self.ismenu:
            height = self.size - 1
            if height < 1:
                height = 1
        else:
            options = len(self.getOptions())
            height = int(math.ceil(options / float(self.buttonColumns)))
        return height

    security.declareProtected('View', 'getValue')
    def getValue(self):
        return self.getSelected()

    security.declareProtected('View', 'getSelected')
    def getSelected(self, REQUEST=None):
        """returns a list of ids of selected options
        """
        deserialize = 1
        if REQUEST is None:
            REQUEST = self.REQUEST
        marker = []
        selected = marker
        source_data = REQUEST.get('__source_data__', marker)
        if source_data is not marker:
            # Data comes from the data source
            selected = source_data.get(self.id, marker)
            deserialize = 0
        if selected is marker:
            # Stuff comes from the form
            selected = REQUEST.form.get(self.id+ "_value", marker)
            deserialize = 1
        if selected is marker:
            # We haven't got any data yet, so we retrieve the default values
            selected = self.callMethod(self.default)
            deserialize = 0
        if not (isinstance(selected, ListType) or
                isinstance(selected, TupleType)):
            selected = [selected]
        if deserialize:
            selected = map(lambda x: self._deserialize(x), selected)
        return selected

InitializeClass(HTMLMenu)

