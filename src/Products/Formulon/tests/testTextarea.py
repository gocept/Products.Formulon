# Copyright (c) 2001-2010 gocept gmbh & co. kg.
# See also LICENSE.txt
"""Unit tests for textarea."""

import unittest
from Products.Formulon.HTMLForm import HTMLForm
from Products.Formulon.HTMLTextarea import HTMLTextarea
from Products.Formulon.WidgetBase import TALESMethod
from Testing.makerequest import makerequest


class TestTextarea(unittest.TestCase):

    def testRegexCache(self):
        form = makerequest(HTMLForm('form'))
        widget = HTMLTextarea('noname')
        form._setObject('noname', widget)
        widget = form['noname']

        import re
        old = re.compile("asdf")
        widget._v_regex = old

        pattern2 = TALESMethod("string:asdf2")
        widget.regexp = pattern2
        widget._update_cache()

        self.failIf(widget._v_regex is old)
        self.assertEqual(
            'string:'+widget._v_regex.pattern, pattern2.getExpression())


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestTextarea))
    return suite
