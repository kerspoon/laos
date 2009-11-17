#! /usr/local/bin/python
# template for python programs
 
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

Simulate all contingencies in the batch file using the psat file as a base. Process the results and output. 
"""
 
#------------------------------------------------------------------------------
# Imports:
#------------------------------------------------------------------------------
 
import sys
import optparse
import logging
import os
from os.path import basename, splitext
from psat import read_psat, read_contingency
from parselog import SimInLimits
 
#------------------------------------------------------------------------------
# Logging:
#------------------------------------------------------------------------------
 
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
    format="%(levelname)s: %(message)s")
 
logger = logging.getLogger(__name__)

#------------------------------------------------------------------------------
# Grem: regexp file deleter
#------------------------------------------------------------------------------

def grem(path, pattern):
	pattern = re.compile(pattern)
	for each in os.listdir(path):
		if pattern.search(each):
			name = os.path.join(path, each)
			try: os.remove(name)
			except:
				grem(name, '')
				os.rmdir(name)

#------------------------------------------------------------------------------
# 
#------------------------------------------------------------------------------

def remove_files(regexp):
    grem(".", regexp)
    raise Exception("not implemented")

def make_matlab_script(title):
    raise Exception("not implemented")

def write_contingency(contingency, psat, outfile):
    raise Exception("not implemented")

def simulate(title):
    raise Exception("not implemented")

def parselog(title):
    return SimInLimits(open(title + "_01.txt"))
 
#------------------------------------------------------------------------------
# "main2" function:
#------------------------------------------------------------------------------
 
def main2(psat_file, batch_file, outfile):

    psat = read_psat(psat_file)
    contingencies = read_contingency(batch_file)

    for contingency in contingencies:
        remove_files(contingency.title + "_.*\.txt")
        make_matlab_script(contingency.title)
        write_contingency(contingency, psat, open("test.m","w"))
        simulate(contingency.title)
        contingency.result = parselog(contingency.title)
        print contingency.result
    
 
#------------------------------------------------------------------------------
# "main" function:
#------------------------------------------------------------------------------
 
def main():
    """ Parses the command line and call with the correct data.
"""
    parser = optparse.OptionParser("usage: program [options] psat_file batch_file")
 
    parser.add_option("-o", "--output", dest="output", metavar="FILE",
        help="Write the solution report to FILE.")
 
    parser.add_option("-q", "--quiet", action="store_true", dest="quiet",
        default=False, help="Print less information.")
 
    parser.add_option("-d", "--debug", action="store_true", dest="debug",
        default=False, help="Print debug information.")
 
    (options, args) = parser.parse_args()
 
    if options.quiet:
        logger.info("setting logger level to critical")
        logger.setLevel(logging.CRITICAL)
    elif options.debug:
        logger.info("setting logger level to debug")
        logger.setLevel(logging.DEBUG)
    else:
        logger.info("setting logger level to info")
        logger.setLevel(logging.INFO)
 
    # Output.
    if options.output:
        outfile = options.output
        if outfile == "-":
            outfile = sys.stdout
    else:
        outfile = sys.stdout
 
    # Input.
    if len(args) != 2:
        parser.print_help()
        sys.exit(1)
    else:
        psat_file = open(args[0])
        batch_file = open(args[1])
 
    logger.info("Processing %s with %s" % (args[0], args[1]))
    logger.info("===================")
    main2(psat_file, batch_file, outfile)
    logger.info("===================")
 
if __name__ == "__main__":
    main()
 
 
# EOF -------------------------------------------------------------------------
 
