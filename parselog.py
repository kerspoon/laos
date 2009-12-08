#! /usr/local/bin/python

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

"""
A program to parse a PSAT results file and say if it's in limits.
"""

#------------------------------------------------------------------------------
#  Imports:
#------------------------------------------------------------------------------

import sys 
import logging

#------------------------------------------------------------------------------
#  Logging:
#------------------------------------------------------------------------------

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
    format="%(levelname)s: %(message)s")

logger = logging.getLogger(__name__)

#------------------------------------------------------------------------------
#  
#------------------------------------------------------------------------------
class EndofFile(Exception):
    pass

def nextline(stream):
    return stream.next()

def forward_to_line(stream, line):
    for stline in stream:
        if line == stline:
            return
    logger.info("fail: missing section")
    raise EndofFile()

def SimInLimits(stream, simtype):
    import psat_report
    psat_report.PSATreport().parse_stream(stream)
    return None

def SimInLimits2(stream, simtype):

    if simtype == "pf":
        if nextline(stream) != "POWER FLOW REPORT\n":
            logger.info("fail: incorrect title")
            return False
    elif simtype == "opf":
        if nextline(stream) != "OPTIMAL POWER FLOW REPORT\n":
            logger.info("fail: incorrect title")
            return False
    else:
        raise Exception("bad call to function 'check'")

    forward_to_line(stream, 'LIMIT VIOLATION STATISTICS\n')

    inlimits = True

    if simtype == "pf":
        inlimits &= nextline(stream).startswith("ALL VOLTAGES WITHIN LIMITS")
        inlimits &= nextline(stream).startswith("ALL REACTIVE POWER WITHIN LIMITS")
        inlimits &= nextline(stream).startswith("ALL CURRENT FLOWS WITHIN LIMITS")
        inlimits &= nextline(stream).startswith("ALL REAL POWER FLOWS WITHIN LIMITS")
        inlimits &= nextline(stream).startswith("ALL APPARENT POWER FLOWS WITHIN LIMITS")
    elif simtype == "opf":
        inlimits &= nextline(stream).startswith("ALL VOLTAGES WITHIN LIMITS")
        inlimits &= nextline(stream).startswith("ALL REACTIVE POWERS WITHIN LIMITS")
        inlimits &= nextline(stream).startswith("ALL CURRENT FLOWS WITHIN LIMITS")
        inlimits &= nextline(stream).startswith("ALL REAL POWER FLOWS WITHIN LIMITS")
        inlimits &= nextline(stream).startswith("ALL APPARENT POWER FLOWS WITHIN LIMITS")
    else:
        raise Exception("bad call to function 'check'")
        
    if not inlimits:
        logger.info("fail: out of limits")
        return False

    logger.info("pass")
    return True

# EOF -------------------------------------------------------------------------
