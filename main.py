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

clean_files :: None -> None
read_network :: Str -> NetworkData
read_batch :: Str -> SimulationBatch
write_matlab_script :: [Scenario], Stream -> None
write_scenario :: Scenario, Stream -> None
simulate_matlab_script :: Str -> None
parse_log :: Scenario, Stream -> Bool

"""
 
#------------------------------------------------------------------------------
# Imports:
#------------------------------------------------------------------------------
 
import sys
import optparse
import logging
import time 
import subprocess
import StringIO
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

def clean_files():
    grem(".", r"psat_.*\.m")
    grem(".", r"psat_.*\.txt")
    grem(".", r"solve_.*\.m")
    grem(".", r".*\.pyc")

def remove_files(title):
    grem(".", title + "_[1234567890]{2}\.txt")
    grem(".", "solve_" + title + "\.m")
    grem(".", "psat_" + title + "\.m")

def basic_matlab_script(matlab_stream, filename, simtype):
    matlab_stream.write("""
initpsat;
Settings.lfmit = 50;
Settings.violations = 'on'
OPF.basepg = 0;
""")
    matlab_stream.write("runpsat('" + filename + "','data');\n")
    if simtype == "pf":
        matlab_stream.write("runpsat pf;\n")
    elif simtype == "opf":
        matlab_stream.write("runpsat pf;\n")
        matlab_stream.write("runpsat opf;\n")
    else:
        raise Exception("expected pf or opf got: " + simtype)
    matlab_stream.write("runpsat pfrep;\n")
    matlab_stream.write("closepsat;\nexit")

def make_matlab_script(matlab_file, scenario_group):
    str_setup = """
initpsat;
Settings.lfmit = 50;
Settings.violations = 'on'
OPF.basepg = 0;
"""

    matlab_file.write(str_setup)

    assert len(scenario_group) != 0

    for scenario in scenario_group:
        filename = "psat_" + scenario.title + ".m"
        matlab_file.write("runpsat('" + filename + "','data');\n")
        if scenario.simtype == "pf":
            matlab_file.write("runpsat pf;\n")
        elif scenario.simtype == "opf":
            matlab_file.write("runpsat pf;\n")
            matlab_file.write("runpsat opf;\n")
        else:
            raise Exception("expected pf or opf got: " + scenario.simtype)
        matlab_file.write("runpsat pfrep;\n")
        
    str_teardown = """closepsat;
exit
"""
    matlab_file.write(str_teardown)

def TEST_make_matlab_script():
    fakefile = StringIO.StringIO()
    class MockScenario:
        pass 
    fakescenario = MockScenario()
    fakescenario.title = "title"
    fakescenario.simtype = "pf"
    make_matlab_script(fakefile, [fakescenario])

    text = fakefile.getvalue()
    # print text 
    assert text == """
initpsat;
Settings.lfmit = 50;
Settings.violations = 'on'
OPF.basepg = 0;
runpsat('psat_title.m','data');
runpsat pf;
runpsat pfrep;
closepsat;
exit
"""
TEST_make_matlab_script()

def simulate(title):

    print "simulate '" + title + "'"

    proc = subprocess.Popen('matlab -nodisplay -nojvm -nosplash -r ' + title,
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

    split_value = 10

    network = NetworkData()
    network.read(psat_file)

    batch = SimulationBatch()
    batch.read(batch_file)

    clean_files()

    for n, scenario_group in enumerate(splitEvery(split_value, batch)):

        matlab_file = open("matlab_" + str(n) + ".m","w")
        make_matlab_script(matlab_file, scenario_group)
        matlab_file.close()
        
        for scenario in scenario_group:
            scenario_file = open("psat_" + scenario.title + ".m","w")
            write_scenario(scenario_file, scenario, network)
            scenario_file.close()

        simulate("matlab_" + str(n))

        for scenario in scenario_group:
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

def test():
    """
    create 100 outage samples then saves to a batchfile. 
    then read them back in, and write once more. 
    The files should be the same (though this isn't auto-checked)
    """
    import psat 
    np = psat.NetworkProbability()
    np.read(open("rts.net"))

    ofile = open("rts.bch","w")
    for x in range(100):
        np.outages(str(x)).write(ofile)
    ofile.close()

    sb = psat.SimulationBatch()
    sb.read(open("rts.bch"))
    assert len(list(iter(sb))) == 100

    f2 = open("test.bch","w")
    sb.write(f2)
    f2.close()

def test2():
    """
    optimal power flow the system with half load power 
    """

    from psat import Scenario
    from psat_report import PSATreport

    grem(".", r".*\.pyc")
    grem(".", r"psatfile.*\.txt")
    grem(".", r"psatfile.*\.m")
    grem(".", r"matlabfile.*\.m")

    # read the base psatfile 
    nd = NetworkData()
    nd.read(open("rts.m"))

    # make a scenario 
    sc = Scenario("001", "opf")
    sc.all_demand = 0.5

    # combine to make a new psatfile
    scenario_file = open("psatfile_001.m","w")
    write_scenario(scenario_file, sc, nd)
    scenario_file.close()

    # create the matlab script
    matlab_script = open("matlabfile_001.m","w")
    basic_matlab_script(matlab_script, "psatfile_001.m", "pf")
    matlab_script.close()
    
    # simulate and read result
    simulate("matlabfile_001")
    try:
        sc.result = PSATreport().parse_stream(open("psatfile_001_01.txt"))
    except:
        pass

    # print out the scenario with the result
    sc.write(sys.stdout)

def test3():
    
    from psat_report import generate_scenario

    grem(".", r".*\.pyc")
    grem(".", r"rts.*\.txt")
    grem(".", r"matlabfile.*\.m")

    # read the base psatfile 
    psat_data = NetworkData()
    psat_data.read(open("rts.m"))

    # create the matlab script
    matlab_script = open("matlabfile.m","w")
    basic_matlab_script(matlab_script, "rts.m", "opf")
    matlab_script.close()
    
    # simulate
    simulate("matlabfile")

    # generate new psat class instance
    report_stream = open("rts_01.txt")
    new_psat = generate_scenario(report_stream, psat_data)
    report_stream.close()

    # write the new file to disk
    new_file = open("rts_02.m")
    new_psat.write(new_file)
    new_file.close()

if __name__ == "__main__":
    test3()
    # main()
 
 
# EOF -------------------------------------------------------------------------

