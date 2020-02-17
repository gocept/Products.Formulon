# Formulon - Lets you manage Forms on the http://www.zope.org Application Server
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
## Zope initialisation
#
# $Id$

import HTMLForm, HTMLDisplay, HTMLButton, HTMLLabel, HTMLTextfield
import HTMLTextarea, HTMLMenu, HTMLFileupload
import ErrorTranslator
import permissions

from HTMLMenu import serializeValue
from WidgetBase import HiddenField

#to use icons for form buttons
from App.ImageFile import ImageFile
from Globals import DTMLFile, HTMLFile, HTML

# zope imports
from AccessControl.Permission import registerPermissions

misc_={
    'up.png':ImageFile('www/up.png', globals()),
    'left.png':ImageFile('www/left.png', globals()),
    'right.png':ImageFile('www/right.png', globals()),
    'down.png':ImageFile('www/down.png', globals()),
    'customup.png':ImageFile('www/customup.png',globals()),
    'customleft.png':ImageFile('www/customleft.png', globals()),
    'customright.png':ImageFile('www/customright.png', globals()),
    'custombottom.png':ImageFile('www/custombottom.png', globals()),
    'top.png':ImageFile('www/top.png', globals()),
    'bottom.png':ImageFile('www/bottom.png', globals()),
    'leftend.png':ImageFile('www/leftend.png', globals()),
    'rightend.png':ImageFile('www/rightend.png', globals()),
    'style.css':ImageFile('dtml/style.dtml',globals()),
    'edit.png':ImageFile('www/edit.png',globals()),
    'formulon.js':ImageFile('www/formulon.js',globals())
}

def initialize(context):
    try:
        context.registerClass(
            ErrorTranslator.ErrorTranslator,
            constructors = (
            ErrorTranslator.createErrorTranslator, ),
            icon = 'www/TranslationRegistry.gif'
        )
        context.registerClass(
            ErrorTranslator.ErrorTranslationRule,
            constructors = (
            ErrorTranslator.manage_addErrorTranslationRule,
            ErrorTranslator.createErrorTranslationRule),
            icon = 'www/translationrule.gif',
            container_filter = ErrorTranslatorFilter
        )
        context.registerClass(
            ErrorTranslator.ErrorTranslationRuleGroup,
            constructors = (
                ErrorTranslator.manage_addETRG,
                ErrorTranslator.createETRG),
            icon = 'www/TranslationRegistry.gif',
            container_filter = ErrorTranslatorFilter)



        context.registerClass(
            HTMLForm.HTMLForm,
            constructors = (
                HTMLForm.manage_addHTMLFormForm,
                HTMLForm.manage_addHTMLForm)
             , icon = 'www/HTMLForm.png'
            )

        context.registerClass(
            HTMLButton.HTMLButton,
            constructors = (
                HTMLButton.manage_addHTMLButtonForm,
                HTMLButton.manage_addHTMLButton)
             , icon = 'www/HTMLButton.png',
            container_filter = HTMLFormFilter
            )

        context.registerClass(
            HTMLLabel.HTMLLabel,
            constructors = (
                HTMLLabel.manage_addHTMLLabelForm,
                HTMLLabel.manage_addHTMLLabel)
             , icon = 'www/HTMLLabel.png',
            container_filter = HTMLFormFilter
            )

        context.registerClass(
            HTMLTextfield.HTMLTextfield,
            constructors = (
                HTMLTextfield.manage_addHTMLTextfieldForm,
                HTMLTextfield.manage_addHTMLTextfield)
             , icon = 'www/HTMLTextfield.png',
            container_filter = HTMLFormFilter
            )

        context.registerClass(
            HTMLTextarea.HTMLTextarea,
            constructors = (
                HTMLTextarea.manage_addHTMLTextareaForm,
                HTMLTextarea.manage_addHTMLTextarea)
             , icon = 'www/HTMLTextarea.png',
            container_filter = HTMLFormFilter
            )

        context.registerClass(
            HTMLMenu.HTMLMenu,
            constructors = (
                HTMLMenu.manage_addHTMLMenuForm,
                HTMLMenu.manage_addHTMLMenu)
             , icon = 'www/HTMLMenu.png',
            container_filter = HTMLFormFilter
            )

        context.registerClass(
            HTMLDisplay.HTMLDisplay,
            constructors = (
                HTMLDisplay.manage_addHTMLDisplayForm,
                HTMLDisplay.manage_addHTMLDisplay)
             , icon = 'www/HTMLDisplay.png',
            container_filter = HTMLFormFilter
            )

        context.registerClass(
            HTMLFileupload.HTMLFileupload,
            constructors = (
                HTMLFileupload.manage_addHTMLFileuploadForm,
                HTMLFileupload.manage_addHTMLFileupload,
                ),
            icon = 'www/HTMLFileupload.png',
            container_filter = HTMLFormFilter
            )


        # Register help documents
        context.registerHelp()

        # Register permissions
        registerPermissions([ (permissions.READFIELD, ()),
                              (permissions.WRITEFIELD, ()) ])

    except:
        import sys, traceback, string
        type, val, tb = sys.exc_info()
        sys.stderr.write(string.join(traceback.format_exception(type, val, \
                                 tb), ''))
        del type, val, tb


def HTMLFormFilter(objectManager):
    """Widgets now only show up in HTMLForm Objects."""
    if objectManager.meta_type == "HTMLForm":
        return True
    return False

def ErrorTranslatorFilter(objectManager):
    """ErrorTranslatorRules should only show up in ErrorTranslators."""
    if objectManager.meta_type in ["Error Translator", "Error Translation Rule Group"]:
        return True
    return False
