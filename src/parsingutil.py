#! /usr/local/bin/python
# Utilities for pyparsing

#------------------------------------------------------------------------------
# Copyright (C) 2009 James Brooks (kerspoon)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This software is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANDABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#------------------------------------------------------------------------------

""" Package info:
James Brooks (kerspoon)

Utilities for pyparsing
"""

#------------------------------------------------------------------------------
# Imports:
#------------------------------------------------------------------------------

from pyparsing import *
import string
from decimal import Decimal

#------------------------------------------------------------------------------
# PyParsing Util:
#------------------------------------------------------------------------------

class ToBoolean(TokenConverter):
    """ Converter to make token boolean """

    def postParse(self, instring, loc, tokenlist):
        """ Converts the first token to boolean """
        tok = string.lower(tokenlist[0])
        if tok in ["t", "true", "1"]:
            return True
        elif tok in ["f", "false", "0"]:
            return False
        else:
            raise Exception

class ToInteger(TokenConverter):
    """ Converter to make token into an integer """

    def postParse(self, instring, loc, tokenlist):
        """ Converts the first token to an integer """

        return int(tokenlist[0])

class ToDecimal(TokenConverter):
    """ Converter to make token into a float """

    def postParse(self, instring, loc, tokenlist):
        """ Converts the first token into a float """

        return Decimal(tokenlist[0])

decimal_sep = "."
sign = oneOf("+ -")
symbols = "_-."

bool_true = Or([CaselessLiteral("true"), CaselessLiteral("t"), Literal("1")])
bool_false = Or([CaselessLiteral("false"), CaselessLiteral("f"), Literal("0")])

boolean = ToBoolean(Or([bool_true, bool_false]))

integer = ToInteger(
    Combine(Optional(sign) + Word(nums))
)

decimal = ToDecimal(
    Combine(
        Optional(sign) + 
        Word(nums) + 
        Optional(decimal_sep + Word(nums)) + 
        Optional(oneOf("E e") + Optional(sign) + Word(nums))
    )
)

word = Word(alphanums, alphanums + symbols)
qstring = (sglQuotedString | dblQuotedString)

# don't care about having extra spaces in the literal
stringtolits = lambda x: And([Literal(y) for y in x.split()])

# a space seperated line of decimal values that have a column name
decimaltable = lambda x: And([decimal.setResultsName(y) for y in x])


slit = lambda x: Suppress(Literal(x))
