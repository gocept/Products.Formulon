# Copyright (c) 2001-2010 gocept gmbh & co. kg.
# See also LICENSE.txt
"""Unit tests for textfield."""

import unittest

from Products.Formulon.HTMLForm import HTMLForm
from Products.Formulon.HTMLTextfield import HTMLTextfield
from Products.Formulon.IWidget import IWidget
from Products.Formulon.WidgetBase import ValidationError
from Testing.makerequest import makerequest


class PropertiesRequest(object):
    default = ""
    maxlength = 0
    regexp = 'string:.*'
    size = 20
    title = "no widget"
    hint = "string:no hint"
    colspan = 1
    aliases = []

    column = 1
    row = 1
    ispassword = 0

    def has_key(self, key):
        return hasattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)


class TestTextfield(unittest.TestCase):

    def testCreation(self):
        widget = HTMLTextfield("noname")
        self.failUnless(IWidget.isImplementedBy(widget))

    def testSimpleValidation(self):
        form = makerequest(HTMLForm('form'))
        widget = HTMLTextfield("noname")
        form._setObject('noname', widget)
        widget = form['noname']

        # Test everything passing
        props = PropertiesRequest()
        widget.changeProperties(props)

        text = "12345"
        newtext = widget.validate(dict(value=text))

        self.assertEqual(text, newtext)

    def testSimpleRegexp(self):
        form = makerequest(HTMLForm('form'))
        widget = HTMLTextfield("noname")
        form._setObject('noname', widget)
        widget = form['noname']

        # Test everything passing
        props = PropertiesRequest()
        props.regexp = 'string:^[0-9]{5}$$'
        widget.changeProperties(props)

        text = "12345"
        newtext = widget.validate(dict(value=text))

        self.assertEqual(text, newtext)

        text = "12345a"
        self.assertRaises(ValidationError, widget.validate, dict(value=text))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestTextfield))
    return suite
