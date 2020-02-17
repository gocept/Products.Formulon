# Formulon - Let's you manage Forms on the http://www.zope.org Application Server$
# Copyright (C) 2001 Christian Theune, gocept gmbh & co. kg$
#$
# This program is free software; you can redistribute it and/or$
# modify it under the terms of the GNU General Public License$
# as published by the Free Software Foundation; either version 2$
# of the License, or (at your option) any later version.$
#$
# This program is distributed in the hope that it will be useful,$
# but WITHOUT ANY WARRANTY; without even the implied warranty of$
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the$
# GNU General Public License for more details.$
#$
# You should have received a copy of the GNU General Public License$
# along with this program; if not, write to the Free Software$
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.$
#$
## Interface of the error translation service
#$
# $Id$

from Interface import Interface, Attribute

class IErrorTranslator(Interface):
	"""Provides translation Service between system error Messages and
		userfriendly ones."""

	def translate(error):
		"""Translate the given error with a known Rule."""

class IErrorTranslationRule(Interface):

	def isResponsible(error):
		"""Check if this rule is a rule for that type of error"""

	def translate(error): 
		"""Translate the given error."""

	def getPriority():
		"""Returns the priority of the rule."""

class IErrorTranslationHint(Interface):

    field = Attribute("The field that failed.")

    form = Attribute("The form that failed.")
    
    errortype = Attribute("The kind of error that happened.")
    
    value = Attribute("The value that failed.")
    
    hint = Attribute("Some kind of hint of what happend. May be translated into any of the other attributes.")

    description = Attribute("A user readable error description. Should contain a hint how to repair the error.")

