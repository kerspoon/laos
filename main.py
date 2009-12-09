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

Simulate all contingencies in the batch file using the psat file as a 
base. Process the results and output.
"""
 
#------------------------------------------------------------------------------
# Imports:
#------------------------------------------------------------------------------
 
import sys
import optparse
import logging
import time 
import subprocess
from parselog import SimInLimits
from psat import write_scenario, SimulationBatch, NetworkData
from misc import *
 
#------------------------------------------------------------------------------
# Logging:
#------------------------------------------------------------------------------
 
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
    format="%(levelname)s: %(message)s")
 
logger = logging.getLogger(__name__)

#------------------------------------------------------------------------------
# 
#------------------------------------------------------------------------------

def remove_files(title):
    grem(".", title + "_[1234567890]{2}\.txt")
    grem(".", "solve_" + title + "\.m")
    grem(".", "psat_" + title + "\.m")

def make_matlab_script(stream, title, simtype):

    if simtype == "pf":
        base_file = "pf_solve.m"
    elif simtype == "opf":
        base_file = "opf_solve.m"
    else:
        raise Exception()

    new_text = open(base_file).read().replace('psatfilename', "psat_" + title)
    stream.write(new_text)
    #todo: do i need to close these files? 

def simulate(title):

    print "simulate 'solve_" + title + "'"

    proc = subprocess.Popen('matlab -nodisplay -nojvm -nosplash -r solve_' + title,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            stdin=subprocess.PIPE)

    so, se = proc.communicate()

    # print "SE"
    # print "================================="
    # print se 
    # print "================================="

    # print "SO"
    # print "================================="
    # print so 
    # print "================================="

def parselog(title, simtype):
    return SimInLimits(open("psat_" + title + "_01.txt"), simtype)
 
#------------------------------------------------------------------------------
# "main2" function:
#------------------------------------------------------------------------------
 
def main2(psat_file, batch_file, outfile):

    network = NetworkData()
    network.read(psat_file)

    batch = SimulationBatch()
    batch.read(batch_file)

    for scenario in batch:
        print scenario.simtype

        remove_files(scenario.title)

        matlab_file = open("solve_" + scenario.title + ".m","w")
        make_matlab_script(matlab_file, scenario.title, scenario.simtype)
        matlab_file.close()

        scenario_file = open("psat_" + scenario.title + ".m","w")
        write_scenario(scenario_file, scenario, network)
        scenario_file.close()

        simulate(scenario.title)

        scenario.result = parselog(scenario.title, scenario.simtype)

        print "RESULT:", scenario.result
        scenario.write(outfile)
        outfile.flush()

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
        if options.output == "-":
            outfile = sys.stdout
        else:
            outfile = open(options.output,"w")
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
 
