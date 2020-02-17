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
# Product for Forms
#
# $Id$

from Interface import Interface

class IWidget(Interface):
    """Interface for HTML Widgets integrated in Formulon."""

    def render(parent, tabindex=None):
        """Render widget. Append elements to parent.

            parent: Element node implementing DOM
            tabindex: tabindex of that widget, None means no tabindex
                
            returns None
        """

    def height():
        """Calculate the height in HTML table rows."""

    def validate(value):
        """assures value is valid

            returns validated value, i.e. you could convert a string 
                containing a date to a real DateTime object.
            
            raises ValidationError if no validation is possible
            
        """

    def getName():
        """Returns the name of the widget."""

    def getAliases():
        """Returns a list of aliases of the widget."""

    def getValue():
        """Represents the current state of the widget."""
