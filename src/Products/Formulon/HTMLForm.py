#) Formulon - Let's you manage Forms on the ZOPE Application Server
# Copyright (C) gocept gmbh & co. kg, http://www.gocept.com
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
# Product for Forms
#
# $Id$

__doc__="""HTMLForm product module"""
__version__='2.1'

DEBUG = 1

from Globals import DTMLFile, MessageDialog
from Globals import InitializeClass
import Globals

# python imports
import sys
import traceback
import urllib
import copy
from xml.dom.minidom import Document
from types import ClassType, UnicodeType
import transaction

#zope imports
import DateTime
import AccessControl
from AccessControl import getSecurityManager
from OFS.Folder import Folder
from OFS.Application import Application
from Products.SiteErrorLog.SiteErrorLog import SiteErrorLog

# local imports
from Products.Formulon.WidgetBase import \
    TALESMethod, ValidationError, makeDict, makeListOfDicts, \
    HiddenField
from Products.Formulon.IWidget import IWidget
from Products.Formulon import permissions, ErrorTranslator
from Products.Formulon.HTMLLabel import HTMLLabel
from Products.Formulon.HTMLDisplay import HTMLDisplay
from Products.Formulon.HTMLMenu import HTMLMenu

converters = {
    'str'       : str,
    'int'       : int,
    'string'    : str,
    'integer'   : int,
    'float'     : float,
    }

manage_addHTMLFormForm=DTMLFile('dtml/HTMLFormAdd', globals())
def manage_addHTMLForm(self, id, REQUEST=None):
    """Adds a new HTML Form to the ZODB"""
    self._setObject(id, HTMLForm(id, REQUEST))
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(
                self.absolute_url()+"/%s/manage_visualEdit" % id)

class HTMLForm(Folder):
    """HTMLForm is a Folder for Widgets"""

    security = AccessControl.ClassSecurityInfo()

    meta_type = 'HTMLForm'
    dontAllowCopyAndPaste = 0

    security.declareProtected('View management screens', 'manage_properties')
    manage_properties = DTMLFile('dtml/HTMLFormEdit', globals())


    security.declareProtected('View management screens', 'manage_hidden')
    manage_hidden = DTMLFile('dtml/HTMLFormHiddenEdit', globals())

    security.declareProtected('View management screens', 'manage_visualEdit')
    manage_visualEdit = DTMLFile('dtml/HTMLFormVisualEdit', globals())

    security.declareProtected('View', 'viewHistory')
    viewHistory = DTMLFile('dtml/viewHistory', globals())

    manage_options=(
        {'label':'Contents', 'action':'manage_main', 'help':('Formulon', 'HTML-FORM.stx')},
        {'label':'Properties', 'action':'manage_properties' },
        {'label':'Hidden Values', 'action':'manage_hidden' },
        {'label':'Visual Editor', 'action':'manage_visualEdit'},

        {'label':'Security', 'action':'manage_access'}
        )

    site_encoding = "UTF-8"

    def __init__(self, id=None, REQUEST=None):

        self.__created_version__ = self.__version__ = __version__
        self.id = id
        self.transferMethod = 'POST'
        self.actionmsg = ''
        self.title = ''
        self.callMethod  =  ''
        self.target = None
        self.sourceMethod = None
        self.cellpadding = 2
        self.cellspacing = 0
        self.taborder = 'leftright'
        self.historyMethod  = ''

        self.hiddenValues = ()

        if REQUEST is not None:
            self.changeProperties(REQUEST)

    def _getMethodExpression(self, method):
        """returns expression of method or '' if method is not a TALESMethod
        """
        # Uh.. this is ugly, but Python2.1's isinstance does not work with
        # extension classes
        try:
            if method.__class__.__name__ == 'TALESMethod':
                return method.getExpression()
        except AttributeError:
            pass
        return ''

    security.declareProtected('View management screens',
        'getTargetMethodExpression')
    def getTargetMethodExpression(self):
        return self._getMethodExpression(self.target)

    security.declareProtected('View management screens',
        'getSourceMethodExpression')
    def getSourceMethodExpression(self):
        """returns the TALES expression given as source method"""
        return self._getMethodExpression(self.sourceMethod)

    security.declareProtected('View management screens',
        'getCallMethodExpression')
    def getCallMethodExpression(self):
        """returns the TALES expression given as call method"""
        return self._getMethodExpression(self.callMethod)

    security.declareProtected('View management screens',
        'getHistoryMethodExpression')
    def getHistoryMethodExpression(self):
        """returns the TALES expression given as history method"""
        return self._getMethodExpression(self.historyMethod)

    security.declareProtected('Access contents information', 'getValue')
    def getValue(self, method, context=None):
        """returns value returned by method

            method: TALESMethod instance to be evaluated, if None, None is
                returned.
        """
        if not isinstance(method, TALESMethod):
            return None

        if not context:
            context = self
        root = self.getPhysicalRoot()
        value = method.__of__(self)(here=context,
            request=getattr(root, 'REQUEST', None),
            root=self.getPhysicalRoot())
        if callable(value):
            value = value.__of__(self)
        return value

    def _getContext(self, context):
        if isinstance(context, Application):
            return ('', )
        path = (context.__name__, )
        p = context.aq_parent
        if p is not None:
            path = self._getContext(p) + path
        return path

    def _prepareRequest(self):
        """prepares the REQUEST, i.e. sets the source_data"""
        REQUEST = self.REQUEST
        if not REQUEST.has_key('error_info'):
            source_data = self.getValue(self.sourceMethod)
            try:
                source_data = makeDict(source_data)
            except ValueError:
                if DEBUG: raise
                else: source_data = {}
            REQUEST.set('__source_data__', source_data)

    security.declareProtected('View', 'getFormEncoding')
    def getFormEncoding(self):
        """returns the form encoding"""
        if self.transferMethod=="POST":
            return "multipart/form-data"
        else:
            return "application/x-www-form-urlencoded"

    security.declareProtected('View', 'getFormDOM')
    def getFormDOM(self):
        """returns a DOM representing the html rendered form"""
        request = self.REQUEST
        doc = Document()
        form = doc.appendChild(doc.createElement("form"))
        set = form.setAttribute
        set('name', self.id)
        set('action', self.getAction())
        set('method', self.transferMethod)
        set('enctype', self.getFormEncoding())

        invisible = form.appendChild(doc.createElement("div"))
        invisible.setAttribute("id", "hiddenContainer")
        invisible.setAttribute("style", "visibility:hidden;")
        invisible.appendChild(doc.createTextNode(" "))

        appendHidden(form, '%s_process' % self.getId(), 1)
        self._appendHiddenFields(form)
        self._appendHistoryLink(form)
        table = form.appendChild(doc.createElement('table'))
        set = table.setAttribute
        set('class', 'form-table')
        set('cellspacing', str(self.cellspacing))
        set('cellpadding', str(self.cellpadding))

        self._appendErrorInfo(table)

        first_widget = True

        maxcolumn, maxrow = self.getAreaSize()
        physicalGrid = self.getPhysicalGrid()
        for row in physicalGrid:
            form_row = table.appendChild(doc.createElement('tr'))
            form_row.setAttribute('class', 'form-row')
            for cell in row:
                form_cell = doc.createElement('td')
                cell_type = cell['type']
                widget = cell.get('widget')
                css_class = 'form-'
                try:
                    a = request['error_info'][cell['widget'].id]
                    del(a)
                    css_class += 'error-'
                except KeyError:
                    pass
                if cell_type == 'space':
                    css_class += 'spacingcell'
                elif cell_type == 'title':
                    css_class += 'titlecell'
                    text = ''
                    if not isinstance(cell['widget'], HTMLLabel):
                        text = cell['widget'].getTitle()
                    form_cell.appendChild(doc.createTextNode(text))
                elif cell_type == 'widget':
                    if widget.css_class is None:
                        css_class += 'widgetcell'
                    else:
                        css_class += widget.css_class
                    height = widget.height()
                    if height > 1: form_cell.setAttribute('rowspan',
                        str(height))
                    if cell['colspan'] > 1:
                        form_cell.setAttribute('colspan', str(cell['colspan']))
                    if self.taborder == 'topdown':
                        tabindex = (widget.column - 1) * maxrow + widget.row
                    else:
                        tabindex = (widget.row - 1) * maxcolumn + \
                            widget.column

                    node = widget.render(form_cell, tabindex)
                    if first_widget and \
                           not (isinstance(widget, (HTMLLabel, HTMLDisplay))):
                        first_widget = False
                        formulon_first_widget_id = node.getAttribute('id')
                        if not formulon_first_widget_id:
                            formulon_first_widget_id = "formulon_first_widget"
                            node.setAttribute("id", formulon_first_widget_id)
                elif cell_type == 'hint':
                    try:
                        hint = request['error_info'][widget.id]
                    except:
                        hint = ""
                    css_class += 'hintcell'
                    form_cell.appendChild(doc.createTextNode(hint))
                    if cell['colspan'] > 1:
                        form_cell.setAttribute('colspan', str(cell['colspan']))
                elif cell_type == 'span':
                    continue
                form_cell.setAttribute('class', css_class)
                form_row.appendChild(form_cell)
        return form, formulon_first_widget_id

    def _appendHistoryLink(self, elem):
        if self.getHistoryMethodExpression() == '':
            return
        link = elem.appendChild(elem.ownerDocument.createElement('a'))
        set = link.setAttribute
        set('href', '%s/viewHistory?%s' % (self.absolute_url(),
            self.REQUEST['QUERY_STRING']))
        set('target', 'history')
        # XXX: make `Verlauf' configurable
        link.appendChild(link.ownerDocument.createTextNode('Verlauf'))
        return link

    def _appendHiddenFields(self, elem):
        fields = []
        request = self.REQUEST
        source_data = request.get('__source_data__', {})
        for name, value, type in self.hiddenValues:
            value = source_data.get(name, request.get(name, value))
            name = "hidden_form_%s" % name
            field = appendHidden(elem, name, value)

    def _appendErrorInfo(self, elem):
        request = self.REQUEST
        error_info = request.get('error_info', {ErrorTranslator.ERROR_FIELD_BLANK: []})
        if len(error_info.get(ErrorTranslator.ERROR_FIELD_BLANK, [])) == 0:
            return
        doc = elem.ownerDocument
        row = elem.appendChild(doc.createElement('tr'))
        cell = row.appendChild(doc.createElement('td'))
        cell.setAttribute('colspan', str(len(self.getPhysicalGrid()[0])))

        for error in error_info[ErrorTranslator.ERROR_FIELD_BLANK]:
            # append a span for each error. class: error-info
            error_node = doc.createElement('span')
            error_node.setAttribute('class', 'error-info')
            cell.appendChild(error_node)

            text = doc.createTextNode(error)
            error_node.appendChild(text)

        return row


    security.declareProtected('View', 'getHistory')
    def getHistory(self):
        """fetches the list of historic entries and returns in a diffed manner

            beware: fields called "rv_*" are for internal revision purposes
        """

        if self.getHistoryMethodExpression() == '':
            return []

        history = []
        data = self.getValue(self.historyMethod)
        try:
            data = makeListOfDicts(data)
        except ValueError:
            return None

        if len(data) == 0:
            return []
        data_ = data[:]

        # here starts the diffing
        while len(data_)>1:
            diff = {}                # the actual different values
            revision = {}        # the metadata extracted from the diff (all rc_* values)

            new = data_.pop()        # the newer values are at the end
            old = data_[-1]        # after that there are the old values
            for field in new.keys():        # compare all keys of the new
                if field[:3] == "rv_":        # these are internal values like rv_tag and rv_rev
                    revision[field] = new[field]
                elif new[field] != old[field]: # these are the values that are diffed
                    diff[field] = (new[field], old[field])

            if len(diff.keys()):
                    revision['rv_data'] = diff
                    history.append(revision)

        # this makes a "faked" diff for the first record which actually has no
        # real changes, so we make it diff to "None"
        diff = {}
        revision = {}
        for key in data[0].keys():
                if key[:3]=="rv_":
                        revision[key] = data[0][key]
                else:
                        diff[key] = (data[0][key], None)
        revision['rv_data'] = diff
        history.append(revision)

        return history

    security.declareProtected('View management screens', 'visualEdit')
    def visualEdit(self, client=None, REQUEST=None):
        """ Provides the visual Editor """

        widgetList=self.__make__getWidgetList(hide_false_condition=False)
        area=self.__make__getAreaSize(widgetList)
        maxcolumn, maxrow=area
        #virtualGrid=self.__make__getAlternateVirtualGrid(widgetList,area)

        if REQUEST is not None:
            if REQUEST.get('newField', '---') != '---':
                REQUEST.RESPONSE.redirect(self.absolute_url()+'/manage_addProduct/Formulon/HTML%sAdd' % REQUEST.get('newField'))
                return

            if REQUEST.has_key('vis_command') and REQUEST.has_key('vis_object'):
                for objId in REQUEST['vis_object']:
                    obj=self.aq_acquire(objId)
                    if REQUEST['vis_command']=='up' and obj.row>1:
                        obj.row=obj.row-1
                    elif REQUEST['vis_command']=='down':
                        obj.row=obj.row+1
                    elif REQUEST['vis_command']=='left' and obj.column>1:
                        obj.column=obj.column-1
                    elif REQUEST['vis_command']=='right':
                        obj.column=obj.column+1
                    elif REQUEST['vis_command']=='bottom':
                        obj.row = maxrow
                    elif REQUEST['vis_command']=='top':
                        obj.row = maxrow - (maxrow - 1)
                    elif REQUEST['vis_command']=='|left':
                        obj.column = maxcolumn - (maxcolumn - 1)
                    elif REQUEST['vis_command']=='right|':
                        obj.column = maxcolumn
                    elif REQUEST['vis_command']=='down rows':
                        obj.row=obj.row + int(REQUEST['downrows'])
                    elif REQUEST['vis_command']=='up rows' and int(REQUEST['uprows']):
                        obj.row=obj.row - int(REQUEST['uprows'])
                    elif REQUEST['vis_command']=='right columns':
                        obj.column=obj.column + int(REQUEST['rightcolumns'])
                    elif REQUEST['vis_command']=='left columns' and obj.column > int(REQUEST['leftcolumns']):
                        obj.column=obj.column - int(REQUEST['leftcolumns'])


        area=self.__make__getAreaSize(widgetList)
        virtualGrid=self.__make__getAlternateVirtualGrid(widgetList,area)

        htmltext=""
        x=y=0
        for row in virtualGrid:
            x=0
            y+=1
            #htmltext=htmltext+'<tr>\n'
            columnbase=0
            for cell in row:
                localUsed=[]
                x+=1
                color="#DDDDDD"
                if len(cell) > 1:         # Mark colliding widgets
                    color="#FFDDDD"
                htmltext=htmltext+'<td bgcolor="%s">&nbsp;'%color
                if len(cell)>0:
                    for widget in cell:
                        selected=" "
                        try:
                            if widget.id in REQUEST['vis_object']:
                                selected="checked"
                        except:
                            pass
                        localUsed.append(widget)
                        htmltext=htmltext+'<label><img src="%s"> <input type="checkbox" value="%s" name="vis_object:list" %s> %s </label><a href="%s"><img src="/misc_/Formulon/edit.png" border="0"/></a><br/>' % (REQUEST['BASEPATH1']+widget.icon, widget.id, selected, widget.title_or_id() or widget.getId(), widget.absolute_url()+'/manage_workspace')
                for widget in widgetList:
                    if widget.located(x,y,maxcolumn) and (widget not in localUsed):
                        htmltext=htmltext+' ... %s ... cell: %i <br> ' %(widget.title_or_id() or widget.getId(), len(cell))
                columnbase+=1
            htmltext=htmltext+'</tr>\n'

        return htmltext

    def __make__getWidgetList(self, hide_false_condition=True):
        """Returns a list of all widgets readable by the user (references)"""
        user = getSecurityManager().getUser()
        lst=[]
        for object in self.objectValues():
            if not IWidget.isImplementedBy(object):
                continue

            if hide_false_condition and not object.testCondition():
                continue

            lst.append(object)
        return lst

    def __make__getAreaSize(self, widgetList):
        maxcolumn=maxrow=1
        if widgetList is not None:
            for widget in widgetList:
                colspan=0
                if widget.colspan>1:
                    colspan=widget.colspan-1
                if (widget.column+colspan)>maxcolumn:
                    maxcolumn=widget.column+colspan
                if widget.row>maxrow:
                    maxrow=widget.row
        return (maxcolumn, maxrow)

    security.declareProtected('View', 'getAreaSize')
    def getAreaSize(self):
        """return area size

            returns tuple (max_columns, max_rows)
        """
        return self.__make__getAreaSize(self.__make__getWidgetList())

    def __make__getVirtualGrid(self, widgetList, area):
        """Move the widgets into a 2D Matrix from where
           you can access them via their coordinates."""
        virtualGrid=[]
        (maxcolumn, maxrow)=area
        for y in range(int(maxrow)):
            line=[]
            for x in range(int(maxcolumn)):
                line.append(None)
            virtualGrid.append(line)
        for widget in widgetList:
            virtualGrid[widget.row-1][widget.column-1]=widget
        return virtualGrid

    def __make__getAlternateVirtualGrid(self, widgetList, area):
        """Move the widgets into a 2D Matrix from where
           you can access them via their coordinates, but
           cares to have overlapping widgets in one cell. """
        virtualGrid=[]
        (maxcolumn, maxrow)=area
        for y in range(int(maxrow)):
            line=[]
            for x in range(int(maxcolumn)):
                line.append([])
            virtualGrid.append(line)
        for widget in widgetList:
            virtualGrid[widget.row-1][widget.column-1].append(widget)
        return virtualGrid

    def __make__getPhysicalGrid(self, virtualGrid, area):
        """Returns the physical grid corresponding to the
           passed virtual grid."""
        (maxcolumn, maxrow)=area
        rowheights=[]
        for row in virtualGrid:
            highest=0
            for widget in row:
                if widget is not None:
                    _height=widget.height()+1
                    if _height > highest:
                        highest=_height
            rowheights.append(highest)

        productmatrix=[]
        arow=[]
        for column in range(maxcolumn*3):        # Every widget uses three cols
            arow.append({'type':'space'})
        for height in rowheights:
            for row in range(height):             # This row is 'height' tall
                productmatrix.append(copy.deepcopy(arow))
            if not height:
                productmatrix.append([])

        rowbase=0
        for row in virtualGrid:
            columnbase=0
            maxheight=1
            for widget in row:
                if widget is not None:
                    _height=widget.height()
                    # HINT: This should be done in a different way: by using
                    # automatic spanning of the VIRTUAL grid.
                    # I will do this if I have some time for a version 2
                    spanwidth=0
                    if hasattr(widget, 'colspan'):
                        maxspan=(maxcolumn*3)-columnbase-1
                        if widget.colspan>1:
                            spanwidth=(widget.colspan*3)-columnbase-1
                        if (widget.colspan==-1) or (spanwidth > maxspan):
                            spanwidth=maxspan
                        if (widget.colspan in [0,1]) and _height>1:
                            spanwidth=1
                        spanheight=_height
                        if spanheight<1:
                            spanheight=1
                        for y in range(spanheight+1):
                            for x in range(spanwidth):
                                productmatrix[rowbase+y][columnbase+x+1].update(
                                    {'type':'span'})
                    productmatrix[rowbase][columnbase].update( \
                        {'type':'title', 'widget':widget},)
                    productmatrix[rowbase][columnbase+1].update( \
                            {'type':'widget', 'widget':widget, \
                             'colspan':spanwidth})
                    productmatrix[rowbase+_height][columnbase+1].\
                            update({'type':'hint', 'widget':widget,
                                    'colspan':spanwidth})
                    if (_height+1) > maxheight:
                        maxheight=(_height+1)
                columnbase=columnbase+3
            rowbase=rowbase+maxheight
        return productmatrix

    security.declareProtected('View', 'getVirtualGrid')
    def getVirtualGrid(self):
        """return the physical grid"""
        widgetList=self.__make__getWidgetList()
        area=self.__make__getAreaSize(widgetList)
        virtualGrid=self.__make__getVirtualGrid(widgetList,area)
        return virtualGrid

    security.declareProtected('View', 'getPhysicalGrid')
    def getPhysicalGrid(self):
        """return the physical grid"""
        widgetList=self.__make__getWidgetList()
        area=self.__make__getAreaSize(widgetList)
        virtualGrid=self.__make__getVirtualGrid(widgetList,area)
        physicalGrid=self.__make__getPhysicalGrid(virtualGrid,area)
        return physicalGrid

    security.declareProtected('View', '__call__')
    def __call__(self):
        """ Renders the complete Form and returns the corresponding HTML code
        """
        REQUEST = self.REQUEST
        data_is_valid = False
        is_processed  = False
        if REQUEST.form.has_key(self.getId()+'_process'):
            data_is_valid = self.processData()
            is_processed  = True

        if is_processed:
            if data_is_valid:
                self.redirect()
                return
            else:
                # Formulon handles the errors itself, so Zope commits the
                # transaction even in error-case. So e.g. Session variables
                # are not rolled back. That's why we have to do it by hand.
                transaction.abort()
                transaction.begin()

        # (re)display form when not processed or not validreturn
        self._prepareRequest()
        form, formulon_first_widget = self.getFormDOM()
        xml = form.toxml()
        # manually append javascript here
        xml += """<script language="JavaScript">
            document.getElementById("%s").focus();
            </script>""" % formulon_first_widget
        return xml

    security.declareProtected('Change Formulon instances', 'manage_edit')
    def manage_edit(self, REQUEST=None):
        """Sets new properties"""
        if REQUEST is not None:
            self.changeProperties(REQUEST)
            REQUEST.RESPONSE.redirect('%s/manage_properties' % (
                self.absolute_url(), ))

    security.declareProtected('Change Formulon instances', 'manage_edithidden')
    def manage_edithidden(self, REQUEST=None):
        """Sets new properties for the hidden fields"""

        if REQUEST is None:
            return
        if REQUEST.submit == 'add':
            self.hiddenValues = self.hiddenValues + (
                (REQUEST.id, REQUEST.value, REQUEST.type), )
        elif REQUEST.submit == 'edit':
            hidden_values = []
            i = 0
            for id in REQUEST.hidden_ids:
                if id != '':
                    hidden_values.append((REQUEST.hidden_ids[i],
                        REQUEST.hidden_values[i], REQUEST.hidden_types[i]))
                i += 1
            self.hiddenValues = tuple(hidden_values)
        REQUEST.RESPONSE.redirect('%s/manage_hidden' %
            (self.absolute_url(), ))

    security.declareProtected('Change Formulon instances', 'changeProperties')
    def changeProperties(self, REQUEST=None, encoding='iso-8859-1', **kw):
        if REQUEST is None:
            REQUEST = kw
        if REQUEST == {}:
            return

        self.transferMethod = REQUEST.get("transferMethod", self.transferMethod)

        actionmsg = REQUEST.get("actionmsg")
        if actionmsg is not None:
            self.actionmsg = unicode(actionmsg, encoding)

        title = REQUEST.get('title')
        if title is not None:
            self.title = unicode(title, encoding)

        # Update TALES Methods
        tales = ["target", "sourceMethod", "callMethod", "historyMethod"]
        for x in tales:
            expression = REQUEST.get(x)
            if expression is None:
                continue
            setattr(self, x, TALESMethod(unicode(expression, encoding)))

        self.cellpadding = REQUEST.get("cellpadding", self.cellpadding)
        self.cellspacing = REQUEST.get("cellspacing", self.cellspacing)
        self.taborder = REQUEST.get("taborder", self.taborder)

    security.declareProtected('View', 'getAction')
    def getAction(self):
        """Finds out, where this form should be submitted to."""
        return self.REQUEST.URL

    security.declareProtected('View', 'title_or_id')
    def title_or_id(self):          # XXX awkward. This shouldn't be needed anymore.
        return self.aq_parent.title

    security.declareProtected('View', 'validate')
    def validate(self, input_data):
        """Validate form

           input_data: {widget_id: value_of_widget, ...}

           Returns tuple (valid, error) whereby
               valid is dictionary of validated widget_id:value
               error is a list, containing IErrorTranslationHint objects
        """
        user = getSecurityManager().getUser()
        error_information = []
        validated_values = {}

        # Loop through all hidden fields
        for name, value, type in self.hiddenValues:
            value = input_data.get('hidden_form_%s' % name, value)
            validated_values[name] = converters[type](value)

        # Loop through all objects of the form. If it is a widget and the user
        # has write permission, then assign a value to it.
        for widget in self.objectValues():
            if not IWidget.isImplementedBy(widget):
                continue

            if not widget.testCondition():
                validated_values[widget.id] = HiddenField()
                continue

            formValue = u''
            id        = widget.id+"_value"
            data      = {}
            # Gather all id_<option> for the widget
            for key in input_data.keys():
                if key.startswith(id):
                    key_ = "value"
                    data[key_] = input_data[key]
                    if isinstance(data[key_], str):
                        formValue = unicode(data[key_], self.site_encoding)
                        break
            try:
                dataValue = widget.validate(data)
            except ValidationError, e:
                if isinstance(widget.hint, TALESMethod):
                    descr = widget.callMethod(widget.hint)
                else:
                    descr = widget.hint
                error = ErrorTranslator.ErrorTranslationHint(widget.getName(),
                    self, ValidationError, e.getHint(), formValue,
                    description=descr)
                error_information.append( error )
                dataValue = formValue

            validated_values[widget.id] = dataValue

        return (validated_values, error_information)

    security.declarePrivate('processData')
    def processData(self):
        """Checks the input for format mistakes etc.

            First the data is validated by the widgets.  Then the `callMethod'
            is called to actually do something.  If the callMethod raises an
            exception the original form context is called again.  The form
            displays an error then, but all data put in is preserved.
        """
        REQUEST = self.REQUEST

        translated_errors = {}
        old_values = REQUEST.form
        REQUEST['__source_data__'] = REQUEST.form

        validated_values, error_information = self.validate(REQUEST)
        if len(error_information) == 0:
            for key, value in validated_values.items():
                REQUEST.set(key, value)
            # Now go on with actually saving the data
            try:
                # call the `callMethod' which should save the data
                self.getValue(self.callMethod)
            except:
                # All exceptions are caught.  This is intended as they will be
                # either translated and displayed or just displayed.  But we
                # really want to catch everything to preserve the form's input
                # state.
                ee, ev, et = sys.exc_info()
                message = str(ev)
                type = str(ee)

                error = ErrorTranslator.ErrorTranslationHint(None, self, type,
                    message)
                error_information.append(error)

                # If there is an error, we want to put it in the error log
                # (if present)
                error_log = self.aq_acquire('error_log')
                if isinstance(error_log, SiteErrorLog):
                    error_log.raising((ee, ev, et))

        if error_information:
            # We have errors to translate
            error_translator = None
            translated = None

            # We don't catch attribute errors anymore. ErrorTranslator is
            # somewhat a service we simply rely on beeing there. We don't
            # have a strategy what to do without it.
            error_translator = self.aq_acquire("ErrorTranslator")

            translated_errors = {ErrorTranslator.ERROR_FIELD_BLANK:[]}
            # Translate all errors found.
            for error in error_information:
                error_translator.translate(error)

                if error.field == ErrorTranslator.ERROR_FIELD_BLANK:
                    translated_errors[ErrorTranslator.ERROR_FIELD_BLANK].append(
                        error.description)
                else:
                    translated_errors[error.field] = error.description

        if len(error_information) > 0:
            # Validation didn't happen successfully
            REQUEST.set('__source_data__', validated_values)
            REQUEST['error_info'] = translated_errors
            return False

        # Validation was successfull.
        return True

    security.declarePrivate('redirect')
    def redirect(self):
        """Executes the redirect a form is designated to go to after
           validating successfuly."""
        target_default = self.REQUEST.URL
        target = self.getValue(self.target) or target_default

        actionmsg = self.actionmsg % {
            'datetime': DateTime.DateTime().strftime("%c")}
        if actionmsg:
            actionmsg = 'actionmsg=' + urllib.quote(actionmsg)
        if '?' in target:
            first_separator = '&'
        else:
            first_separator = '?'
        target = '%s%s%s' % (target, first_separator, actionmsg)
        self.REQUEST.RESPONSE.redirect(target)

InitializeClass(HTMLForm)

def appendHidden(parent, name, value):
    field = parent.appendChild(parent.ownerDocument.createElement('input'))
    set = field.setAttribute
    set('type', 'hidden')
    set('name', name)
    set('value', str(value))
    return field

