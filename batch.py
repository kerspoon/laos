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
 
""" Package info:
James Brooks (kerspoon)

creates samples and outages batch files

"""
 
#------------------------------------------------------------------------------
# Imports:
#------------------------------------------------------------------------------
 
import sys
import optparse
import time
import logging
from os.path import basename, splitext
import psat

#------------------------------------------------------------------------------
# Logging:
#------------------------------------------------------------------------------
 
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
    format="%(levelname)s: %(message)s")
 
logger = logging.getLogger(__name__)
 
#------------------------------------------------------------------------------
# "main2" function:
#------------------------------------------------------------------------------
 
def main2(infile, outfile, iteratios, simtype):
    np = psat.NetworkProbability()
    np.read(infile)
    if simtype == "outages":
        for x in range(iteratios):
            np.outages(str(x)).write(outfile)
    elif simtype == "failures":
        for x in range(iteratios):
            np.failures(str(x)).write(outfile)
    elif simtype == "n1":
        raise Exception("Not Implemented")
    else:
        raise Exception("Expected outages, failures got " + simtype)

#------------------------------------------------------------------------------
# "main" function:
#------------------------------------------------------------------------------
 
def main():
    """ Parses the command line and call with the correct data.
    """
    parser = optparse.OptionParser("usage: program [options] input_file")
 
    parser.add_option("-o", "--output", dest="output", metavar="FILE",
        help="Write the solution report to FILE.")
 
    parser.add_option("-q", "--quiet", action="store_true", dest="quiet",
        default=False, help="Print less information.")
 
    parser.add_option("-d", "--debug", action="store_true", dest="debug",
        default=False, help="Print debug information.")
 
    parser.add_option("-i", "--iteratios", dest="iteratios",
        default="100", help="Number of iteratios to perform")

    parser.add_option("-t", "--simtype", dest="simtype",
        default="outages", help="Type of sim: 'outages' or 'failures'")

    (options, args) = parser.parse_args()

    if options.quiet:
        logger.setLevel(logging.CRITICAL)
    elif options.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
 
    # Output.
    if options.output:
        if options.output == "-":
            outfile = sys.stdout
            logger.setLevel(logging.CRITICAL) # we must stay quiet
        else:
            outfile = open(options.output,"w")
    else:
        outfile = sys.stdout
        logger.setLevel(logging.CRITICAL) # we must stay quiet
 
    # Input.
    if len(args) > 1:
        parser.print_help()
        sys.exit(1)
    elif len(args) == 0 or args[0] == "-":
        infilename = ""
        if sys.stdin.isatty():
            # True if the file is connected to a tty device, and False
            # otherwise (pipeline or file redirection).
            parser.print_help()
            sys.exit(1)
        else:
            # Handle piped input ($ cat ehv3.raw | pylon | rst2pdf -o ans.pdf).
            infile = sys.stdin
    else:
        infilename = args[0]
        infile = open(infilename)
 
    t0 = time.time()
    logger.info("Running Program with: %s" % infilename)
    logger.info("  %s %s" % (options.iteratios, options.simtype))
    logger.info("===================")
    main2(infile, outfile, int(options.iteratios), options.simtype)
    logger.info("===================")
 
    elapsed = time.time() - t0
    logger.info("Completed in %.3fs." % elapsed)

if __name__ == "__main__":
    main()
 
 
# EOF -------------------------------------------------------------------------

