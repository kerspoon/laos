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
import re 
import time 
import copy 
import subprocess
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

def grem(path, pattern, test=False):
    pattern = re.compile(pattern)
    for each in os.listdir(path):
        if pattern.search(each):
            name = os.path.join(path, each)
            try:
                if not test: os.remove(name)
                logger.info("Grem removed " + name)
            except:
                if not test: 
                    grem(name, '')
                    os.rmdir(name)
                logger.info("Grem removed dir " + name)

def test_grem():
    grem(".", ".*\.pyc", True)
    grem(".", "rts_[1234567890]{2}\.txt", True)
# test_grem()        
        
#------------------------------------------------------------------------------
# 
#------------------------------------------------------------------------------

def remove_files(title):
    grem(".", title + "_[1234567890]{2}\.txt")
    grem(".", "solve_" + title + "\.m")
    grem(".", "psat_" + title + "\.m")
    
def make_matlab_script(title, simtype):

    if simtype == "powerflow":
        base_file = "pf_solve.m"
    elif simtype == "optimalpowerflow":
        base_file = "opf_solve.m"

    new_text = open(base_file).read().replace('psatfilename', "psat_" + title)
    open("solve_" + title + ".m","w").write(new_text)
    #todo: do i need to close these files? 

def write_contingency(contingency, psat):

    newpsat = copy.deepcopy(psat)

    for kill in contingency.kill["bus"]:
        newpsat.remove_bus(kill)
    for kill in contingency.kill["line"]:
        newpsat.remove_line(kill[0], kill[1])
    for kill in contingency.kill["generator"]:
        newpsat.remove_generator(kill)

    if not(len(contingency.supply) == 0 and len(contingency.demand) == 0):
        raise Exception("not implemented")
    
    newpsat.write(open("psat_" + contingency.title + ".m","w"))

def simulate(title):
    proc = subprocess.Popen('matlab -nodesktop -nodisplay -nojvm -nosplash -r solve_' + title,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            stdin=subprocess.PIPE)
    so, se = proc.communicate()

#     print "\n\nSE\n\n"
#     print se 

#     print "\n\nSO\n\n"
#     print so 

def parselog(title, simtype):
    return SimInLimits(open("psat_" + title + "_01.txt"), simtype)
 
#------------------------------------------------------------------------------
# "main2" function:
#------------------------------------------------------------------------------
 
def main2(psat_file, batch_file, outfile):

    psat = read_psat(psat_file)
    contingencies = read_contingency(batch_file)

    for contingency in contingencies:
        remove_files(contingency.title)
        make_matlab_script(contingency.title, contingency.simtype)
        write_contingency(contingency, psat)
        simulate(contingency.title)
        contingency.result = parselog(contingency.title, contingency.simtype)
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
        print "Error: expected 2 arguments got", len(args)
        parser.print_help()
        sys.exit(1)
    else:
        psat_file = open(args[0])
        batch_file = open(args[1])
 
    t0 = time.time()
    logger.info("Processing %s with %s" % (args[0], args[1]))
    logger.info("===================")
    main2(psat_file, batch_file, outfile)
    logger.info("===================")
 
    elapsed = time.time() - t0
    logger.info("Completed in %.3fs." % elapsed)

if __name__ == "__main__":
    main()
 
 
# EOF -------------------------------------------------------------------------
 
