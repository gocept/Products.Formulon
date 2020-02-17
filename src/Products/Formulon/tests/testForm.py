##############################################################################
#
# Copyright (c) 2001-2003 gocept gmbh & co. kg.
#
# See also LICENSE.txt
#
##############################################################################
"""Unit tests for formulon in general.

$Id$"""

import unittest
import ZODB, OFS.Application

from Products.Formulon.HTMLForm import HTMLForm

class DummyRequest:

    def has_key(self, key):
        return hasattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)

class TestForm(unittest.TestCase):

    def testchangePropertiesRequest(self):
        form = HTMLForm("noname")

        update = DummyRequest()

        update.transferMethod = 'POST'
        update.actionmsg = 'actionmsg'
        update.callMethod = 'here/call'
        update.target = 'here/target'
        update.sourceMethod = 'here/source'
        update.cellpadding = 4
        update.cellspacing = 2
        update.taborder = 'topdown'
        update.historyMethod = 'here/history'

        form.changeProperties(REQUEST=update)

        self.assertEqual(form.transferMethod, update.transferMethod)
        self.assertEqual(form.actionmsg, update.actionmsg)
        self.assertEqual(form.callMethod.getExpression(), update.callMethod)
        self.assertEqual(form.target.getExpression(), update.target)
        self.assertEqual(form.sourceMethod.getExpression(), 
                         update.sourceMethod)
        self.assertEqual(form.cellpadding, update.cellpadding)
        self.assertEqual(form.cellspacing, update.cellspacing)
        self.assertEqual(form.taborder, update.taborder)
        self.assertEqual(form.historyMethod.getExpression(), 
                         update.historyMethod)

    def testchangePropertiesDirect(self):
        form = HTMLForm("noname")

        newtitle = "new"
        newtitle2 = "new2"
        newsource1 = "here/source"

        form.changeProperties(title=newtitle, sourceMethod=newsource1)
        self.assertEqual(form.sourceMethod.getExpression(), newsource1)

        form.changeProperties(title=newtitle2)
        self.assertEqual(form.sourceMethod.getExpression(), newsource1)

    # XXX this test currently borks, because of some error within the
    # unit testing framework. special acquisition wrappers don't allow
    # us to do "self.getPhysicalRoot" without it, i can't call the 
    # history method from within the unittest. as soon as this works
    # one should re-enable this test. i'll issue a warning for now.
    def testHistory(self):
        print "warning: this test relies on broken code. (testForm.testHistory)"
    #    form = HTMLForm("noname")
    #    form.changeProperties(historyMethod="""python:[ {"a":0},
    #                 {"a":1, b:"2"},
    #                 {"a":1, c:"1"} ]""")
    #                 
    #    import pdb; pdb.set_trace()
    #    diffed = form.getHistory()
        
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite(TestForm))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

