# Formulon - Let's you manage Forms on the http://www.zope.org Application Server
# Copyright (C) 2001 - 2010 Christian Theune, gocept gmbh & co. kg
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
## Module for the Error Translation Service
#
# $Id$

__doc__="""Error Translation Service module"""
__version__='0.1'

from OFS import SimpleItem, Folder
from types import StringType
import Globals
import IErrorTranslator, IWidget
import Persistence, OFS.SimpleItem, Acquisition, AccessControl
import re, exceptions
import zLOG
import zope.cachedescriptors.property

# Some exceptions ...

class TranslationError(exceptions.Exception):
    pass

class ResponsibilityError(TranslationError):
    pass

class RuleConfigurationError(TranslationError):
    pass


ERROR_FIELD_BLANK = '_'

def createErrorTranslator(context, REQUEST=None):
    """A factor for creating a new ErrorTranslator."""
    context._setObject("ErrorTranslator", ErrorTranslator())
    if REQUEST is not None:
        return context.manage_main(context, REQUEST)

class ErrorTranslator(Folder.Folder, Persistence.Persistent, Acquisition.Implicit, AccessControl.Role.RoleManager):

    __implements__ = IErrorTranslator.IErrorTranslator

    security = AccessControl.ClassSecurityInfo()

    id = 'ErrorTranslator'
    title = "Error Translation registry"

    meta_type = "Error Translator"

    security.declareProtected('View management screens', 'manage_debug')
    manage_debug = Globals.HTMLFile('dtml/ErrorTranslatorDebug', globals())

    manage_options = Folder.Folder.manage_options + \
                     ( {'label':'Debug', 'action':'manage_debug'}, )

    manage_options = filter(lambda x: x['label'] not in ['View', 'Properties', 'Find'], manage_options)

    ##### Here comes the ZOPE management stuff

    def __init__(self):
        self.__version__ = __version__

    def all_meta_types(self):
        """We only want to add Error Translation Rules here."""
        allowedMetaTypes = ["Error Translation Rule", "Error Translation Rule Group"]
        result = []
        import Products
        for metaType in Products.meta_types:
            if metaType['name'] in allowedMetaTypes:
                result.append(metaType)
        return result

    security.declarePublic("translateEasy")
    def translateEasy(self, type=None, value=None, description=None):
        """
            Try a translation when we only got a type and a value.
        """
        hint = ErrorTranslationHint(None, None, type, value, None, description)
        translated = self.translate(hint)
        return translated

    security.declarePublic("translate")
    def translate(self, error):
        """Translate the given error.

            error: ErrorTranslationHint
            returns: ErrorTranslationHint instance

            This means the hint will be set to a value useful for the user.

            The actual work is done by the rules. We only try to find the
            actual rule that matches this error. Then the rule has to do the
            work.
        """
        assert IErrorTranslator.IErrorTranslationHint.isImplementedBy(error), \
                "ErrorTranslator interface not satisfied"


        rules = self.discoverRules()

        is_translated = 0
        for rule in rules:
            if (IErrorTranslator.IErrorTranslationRule.isImplementedBy(rule)
                    and rule.isResponsible(error)):
                rule.translate(error)
                is_translated = 1
                break

        if not is_translated and not error.field:
            zLOG.LOG('ErrorTranslator', zLOG.INFO, 'Untranslated exception occured', str(error))
            error.field = ERROR_FIELD_BLANK
            error.description = error.hint

        return error

    security.declarePrivate('discoverRules')
    def discoverRules(self):
        stack = self.objectValues()
        rules = []
        while stack:
            element = stack.pop()
            # Append rule to the list
            if isinstance(element, ErrorTranslationRule):
                rules.append(element)
            # Check if it could be a container that holds more rules
            try:
                new = element.objectValues()
                stack.extend(new)
            except AttributeError:
                pass

        rules.sort(lambda x,y: cmp(x.getPriority(), y.getPriority()))
        return rules


Globals.InitializeClass(ErrorTranslator)


manage_addErrorTranslationRule = Globals.HTMLFile('dtml/ErrorTranslationRuleAdd', globals())
def createErrorTranslationRule(context, id, REQUEST=None):
    """A factory for creating a new translation rule."""
    context._setObject(id, ErrorTranslationRule(id, REQUEST))
    if REQUEST is not None:
        return context.manage_main(context, REQUEST)

class ErrorTranslationRule(SimpleItem.SimpleItem):

    __implements__ = IErrorTranslator.IErrorTranslationRule

    security    = AccessControl.ClassSecurityInfo()
    meta_type   = "Error Translation Rule"

    manage_properties = Globals.HTMLFile('dtml/ErrorTranslationRuleEdit',
        globals())

    title = ""

    # Regexp to match the error type
    typeMatch = None

    # Regexp to match the error value
    errorMatch = None

    # Regexp with backreferences to errorMatch for creating the user message
    msgRule = None

    # Number of group in errorMatch for the Fielis dname
    # SPECIAL CASE: if no number, you can write the fieldname in here
    # (or its alias)
    brField = None

    # Number of group in errorMatch for the Value
    brValue = None

    # Priority for sorting the rules (0 = lowest, >0 = higher Priority)
    priority = 100

    manage_options = (
        {'label':'Properties', 'action':'manage_properties'},
        )

    # Here comes the Zope specific code
    def __init__(self, id, REQUEST=None):
        self.id = id
        if REQUEST is not None:
            self.update(REQUEST)

    security.declareProtected("Change Translation Rules", "manage_edit")
    def manage_edit(self, REQUEST=None):
        """ZMI data save method"""
        if REQUEST is not None:
            self.update(REQUEST)
            return Globals.MessageDialog(title="Edited",
                message="Properties for %s changed." % self.id,
                action="./manage_properties")

    security.declareProtected("Change Translation Rules", "update")
    def update(self, REQUEST):
        if REQUEST is None:
            return
        self.title = REQUEST.title
        self.typeMatch = REQUEST.typeMatch
        self.errorMatch = REQUEST.errorMatch
        self.msgRule = unicode(REQUEST.msgRule, 'iso-8859-1')
        self.brField = REQUEST.brField or None
        try:
            self.brValue = int(REQUEST.brValue)
        except ValueError:
            self.brValue = None
        self.priority = REQUEST.priority

    def re_typeMatch(self):
        return re.compile(self.typeMatch, re.MULTILINE + re.DOTALL)

    re_typeMatch = zope.cachedescriptors.property.CachedProperty(
        re_typeMatch, 'typeMatch')

    def re_errorMatch(self):
        return re.compile(self.errorMatch, re.MULTILINE + re.DOTALL)

    re_errorMatch = zope.cachedescriptors.property.CachedProperty(
        re_errorMatch, 'errorMatch')

    security.declarePublic("isResponsible")
    def isResponsible(self, error):
        """returns whether this rule can translate given error

            error: uhm.. what is error? XXX
            returns True if rule would be appropriate to use for the
                translation, False otherwise
        """
        if self.re_typeMatch.search(unicode(error.errortype)) is None:
            return False
        if self.re_errorMatch.search(unicode(error.hint)) is None:
            return False
        return True

    security.declarePublic("translate")
    def translate(self, error):
        if not self.isResponsible(error):
            raise ResponsibilityError, "%s is not responsible for this error." % self.id
        # XXX check for IErrorTranslationHint here
        brFieldString = ''
        try:
            brFieldNo = int(self.brField)
        except (TypeError, ValueError):
            brFieldNo = 0
            brFieldString = self.brField


        match = self.re_errorMatch.search(unicode(error.hint))
        groups = match.groups()

        # If the groupcount from the regexp doesn't match,
        # we don't check for a regexp translation.
        # XXX probably a debugging note on the server would
        # be appropriate here.
        regex_value = (self.brValue <= len(groups)) and self.brValue
        regex_field = (brFieldNo <= len(groups)) and brFieldNo

        # Find the Fieldname:
        if error.field:
            # The error already knew it's field
            pass
        elif regex_field:
            # We knew how to handle it with a reg. exp.
            error.field = groups[regex_field-1]
        elif brFieldString:
            error.field = brFieldString
        else:
            # We need to find the field by Value.

            if error.value:
                pass
            elif regex_value:
                error.value = groups[regex_value-1]

        # try to find a field matching the fieldname or alias of the error
        if error.field is not None and error.form is not None:
            field_translated = None
            for item in error.form.objectValues():
                if not IWidget.IWidget.isImplementedBy(item):
                    continue
                if not item.testCondition():
                    # do not show errors on hidden fields
                    continue

                name_candidates = (tuple(item.getAliases()) +
                                   tuple([item.getName()]) )
                if error.field in name_candidates :
                    field_translated = item.getName()
                    break
            if field_translated:
                error.field = field_translated
            else:
                error.field = ERROR_FIELD_BLANK # Fieldname not existing in form
        elif error.value is None:
            error.field = ERROR_FIELD_BLANK

        # try to find a field matching the fieldvalue
        if (error.field is None and error.value is not None and
                error.form is not None):
            candidate = None
            for item in error.form.objectValues():
                if IWidget.IWidget.isImplementedBy(item) and \
                   error.value == item.getValue() and not candidate:
                   candidate = item.getName()

            error.field = candidate

        # create the translated error message
        if not error.description:
            error.description = self.re_errorMatch.sub(self.msgRule,
                        error.hint, 1)

    security.declareProtected("Access contents information", "getPriority")
    def getPriority(self):
        return self.priority
Globals.InitializeClass(ErrorTranslationRule)

manage_addETRG = Globals.HTMLFile('dtml/ETRGAdd', globals())
def createETRG(context, id, title='', REQUEST=None):
    """A factory for creating a new Error Translation Rule Group"""
    ob = ErrorTranslationRuleGroup(id)
    ob.title = title
    context._setObject(id, ob)
    if REQUEST is not None:
        return context.manage_main(context, REQUEST, update_menu=1)


class ErrorTranslationRuleGroup(Folder.Folder):

    meta_type = "Error Translation Rule Group"

    def all_meta_types(self):
        """We only want to add Error Translation Rules here."""
        allowedMetaTypes = ["Error Translation Rule", "Error Translation Rule Group"]
        result = []
        import Products
        for metaType in Products.meta_types:
            if metaType['name'] in allowedMetaTypes:
                result.append(metaType)
        return result



class ErrorTranslationHint:

    __implements__ = (IErrorTranslator.IErrorTranslationHint,)
    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, field, form, errortype, hint, value=None,
            description=None):
        assert isinstance(hint, (str, unicode, Exception)), "Invalid hint type"

        if isinstance(hint, Exception):
            hint = str(hint)
        if isinstance(hint, StringType):
            hint = unicode(hint, "utf-8", "replace")

        if isinstance(description, Exception):
            description = str(description)
        if isinstance(description, StringType):
            description = unicode(description, "utf-8", "replace")

        self.field = field
        self.form = form
        self.errortype = str(errortype)
        self.hint = hint
        self.value = value
        self.description = description

    def __str__(self):
        return "Field: %s\nForm: %s\nErrorType: %s\nHint: %s\nValue: %s\n" \
            "Description: %s" % (self.field, self.form, self.errortype,
            repr(self.hint), self.value, self.description)

