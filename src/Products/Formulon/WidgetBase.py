# Formulon - Lets you manage Forms on the http://www.zope.org Application Server
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
"""
Widget Base implementation and utility functions and classes

$Id$
"""

from __future__ import nested_scopes

from types import TupleType, ListType, DictType, NoneType

import Acquisition
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
import Shared.DC.ZRDB.Results
from Persistence import Persistent
from Products.PageTemplates.Expressions import getEngine

class ValidationError(Exception):
    """Raised by validate methods of IWidget"""

    def getHint(self):
        if self.args:
            return self.args[0]
        else:
            return None

class HiddenField:

    def __nonzero__(self):
        return False

    def __str__(self):
        return ""

class TALESMethod(Persistent, Acquisition.Implicit):
    """A method object; calls method name in acquisition context.

        Taken from Formulator.
    """

    def __init__(self, text):
        self.setExpression(text)

    def __call__(self, **kw):
        if self._text == "":
            return None
        expr = getEngine().compile(self._text)
        return getEngine().getContext(kw).evaluate(expr)

    def getExpression(self):
        return self._text

    def setExpression(self, text):
        if isinstance(text, str):
            text = unicode(text, 'UTF-8')
        assert isinstance(text, unicode), 'Expression must be a unicode '\
               'type (%r)' % (text, )
        self._text = text

    def __str__(self):
        return self.getExpression().encode('UTF-8')


class WidgetBase:

    site_encoding = "UTF-8"

    security = ClassSecurityInfo()

    condition = TALESMethod("python:True")
    taltitle = TALESMethod("")

    security.declareProtected('View', 'callMethod')
    def callMethod(self, method):
        """returns value returned by method

            method: TALESMethod instance to be evaluated, if None, None is
                returned.
        """
        try:
            if not method.__class__.__name__ == 'TALESMethod':
                return None
        except AttributeError:
            return None
        __traceback_info__ = (self.__class__, self.id)
        value = method.__of__(self.aq_parent)(here=self.aq_parent,
                                              request=self.REQUEST,
                                              form=self.aq_parent)
        if callable(value):
            value = value.__of__(self)
        return value

    def getName(self):
        return self.id

    def getAliases(self):
        return self.aliases

    def getTitle(self):
        "Get taltitle or title."
        if not self.getMethodExpression(self.taltitle):
            return self.title
        return self.callMethod(self.taltitle) or ''

    def render(self, parent, tabindex=None):
        raise NotImplementedError, "Implemented in subclasses"

    security.declareProtected('View management screens',
        'getMethodExpression')
    def getMethodExpression(self, method):
        try:
            if method.__class__.__name__ == 'TALESMethod':
                return method.getExpression()
        except AttributeError:
            pass
        return ''

    security.declarePrivate("testCondition")
    def testCondition(self):
        """Tests if the widget should be displayed."""
        if hasattr(self, 'condition'):
            return bool(self.callMethod(self.condition))
        else:
            return True

    security.declarePrivate("changeBaseProperties")
    def changeBaseProperties(self, kw, encoding='iso-8859-1'):
        """Updates the base properties for this instance."""
        condition = kw.get('condition')
        if condition is not None:
            self.condition = TALESMethod(unicode(condition, encoding))

        taltitle = kw.get('taltitle')
        if taltitle is not None:
            self.taltitle = TALESMethod(unicode(taltitle, encoding))


InitializeClass(WidgetBase)

def makeDict(data):
    """tries to convert data to a dictionary

        data: none, dictionary, list of tuples or SQL result set
        returns dictionary

        raises ValueError if data is not convertible
    """
    if isinstance(data, NoneType):
        return {}
    if isinstance(data, DictType):
        return data
    if isinstance(data, ListType):
        try:
            return dict(data)
        except NameError:
            raise NotImplementedError, "List of tuples is not supported in " \
                "python 2.1 yet"
    if isinstance(data, Shared.DC.ZRDB.Results.Results):
        dicts = data.dictionaries()
        if len(dicts) == 0:
            return {}
        if len(dicts) > 1:
            raise ValueError, "The database query returned more than one "\
                "result"
        return dicts[0]
    try:
        # SQL result
        keys =  data.__record_schema__.keys()
    except AttributeError:
        pass
    else:
        result = {}
        for key in keys:
            result[key] = getattr(data, key)
        return result

    raise ValueError, '%r is not convertible to a dict' % (data, )

def makeTuple(data, order=("value", "title")):
    if isinstance(data, TupleType):
        return data
    if isinstance(data, ListType):
        return tuple(data)
    try:
        d = makeDict(data)
        new_list = []
        for key in order:
            new_list.append(d.get(key, None))
        return tuple(new_list)
    except:
        # That's bold ... *G
        return (data, data)

def makeListOfDicts(data):
    """convers a list of something into a list of dictionaries

        every item is passed to makeDict
        raises ValueError if an item is not convertible
    """
    return map(lambda x: makeDict(x), data)

def makeListOfTuples(data, order=("value", "title")):
    return map(lambda x: makeTuple(x, order), data)

