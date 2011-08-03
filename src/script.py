#! /usr/local/bin/python
# scripts for laos
 
#==============================================================================
# Copyright (C) 2010 James Brooks (kerspoon)
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
#==============================================================================


#==============================================================================
# Imports:
#==============================================================================


from __future__ import with_statement 
from misc import grem, split_every
from copy import deepcopy
import math 
import subprocess
import sys 
import time 
from StringIO import StringIO
from contextlib import closing

from simulation_batch import SimulationBatch
from network_probability import NetworkProbability
from psat_data import PsatData
from psat_report import PsatReport
import os.path


#==============================================================================
# 
#==============================================================================


def clean_files():
    """func clean_files          :: ->
       ----
       remove all the files from previous calcluations
    """
    grem(".", r"psat_.*\.m")
    grem(".", r"psat_.*\.txt")
    grem(".", r"matlab_.*\.m")
    grem(".", r".*\.pyc")
    grem(".", r".*\.bch")
    grem(".", r".*\.csv")
    grem(".", r".*_[1234567890]{2}\.txt")
clean_files()


def make_outages(prob, count):
    """func make_outages         :: NetworkProbability, Int -> SimulationBatch
       ----
       Monte Carlo sample the network for it's expected condition. 
       e.g. existing outages, weather & load forcast, etc.
    """
    batch = SimulationBatch()
    for x in range(count):
        batch.add(prob.outages(str(x)))
    assert count == batch.size()
    return batch


def make_failures(prob, count):
    """func make_failures        :: NetworkProbability, Int -> SimulationBatch
       ----
       Monte Carlo sample the network for unexpected changes. 
       e.g. new outages (failures), actual weather, actual load level, etc.
    """
    batch = SimulationBatch()
    for x in range(count):
        batch.add(prob.failures(str(x)))
    assert count == batch.size()
    return batch


def make_outage_cases(prob, count):
    """func make_outage_cases         :: NetworkProbability, Int -> SimulationBatch
       ----
       like `make_outages` but makes `count` *after* reducing.
       
       Monte Carlo sample the network for it's expected condition. 
       e.g. existing outages, weather & load forcast, etc.
    """
    batch = SimulationBatch()
    current = 0
    while len(batch) < count:
        batch.add(prob.outages(str(current)))
        current += 1
    assert count == len(batch)
    return batch

def make_failure_cases(prob, count):
       
    """func make_failure_cases        :: NetworkProbability, Int -> SimulationBatch
       ----
       like `make_failures` but makes `count` *after* reducing.
       
       Monte Carlo sample the network for unexpected changes. 
       e.g. new outages (failures), actual weather, actual load level, etc.
    """
    batch = SimulationBatch()
    current = 0
    while len(batch) < count:
        batch.add(prob.failures(str(current)))
        current += 1
    assert count == len(batch)
    return batch


def read_file(filename, datatype):
    """func read_file            :: Str, x -> x
       ----
       read a generic file into it class 'datatype'.
    """

    if os.path.isfile(filename):
        newfilename = filename
    elif os.path.isfile("../" + filename):
        newfilename = "../" + filename
    else:
        print "error finding file '%s'" % filename
        
    with open(newfilename) as thefile:
        data = datatype()
        data.read(thefile)
        return data


def read_probabilities(filename):
    """func read_probabilities   :: Str -> NetworkProbability
       ----
       read a net_file into NetworkProbability.
    """
    return read_file(filename, NetworkProbability)
    

def read_psat(filename):
    """func read_psat         :: Str -> PsatData
       ----
       read a psat_file into PsatData.
    """
    return read_file(filename, PsatData)


def read_batch(filename):
    """func read_batch           :: Str -> SimulationBatch
       ----
       read a batch_file into SimulationBatch.
    """
    return read_file(filename, SimulationBatch)


def read_report(filename):
    """func read_report           :: Str -> PsatReport
       ----
       read a psat_report_file into PsatReport.
    """
    return read_file(filename, PsatReport)


def report_in_limits(report):
    """func report_in_limits          :: PsatReport -> Str
       ----
       is the results of the simulation in limits based on report
    """
    if report.in_limit():
        return "pass"
    elif not report.in_limit():
        return "fail"
    else:
        return "error"

def report_to_psat(report, psat):
    """func report_to_psat       :: PsatReport, PsatData -> PsatData
       ----
       Make a new PsatData based upon `psat` but contains the voltage,
       angle, and power values from `report`.
    """

    # TODO: if we can work out why PSAT has discrepencies in the 
    #       number of items in input and output then add these line back

    # assert len(psat.lines) == report.num_line
    # assert len(psat.slack) == 1
    # assert len(psat.generators) == report.num_generator
    # assert len(psat.busses) == report.num_bus
    # assert len(psat.loads) == report.num_load
    # assert len(psat.demand) == 0
    # assert len(psat.supply) == len(psat.loads)

    new_psat = deepcopy(psat)
    pf = report.power_flow

    assert len(new_psat.slack) == 1
    slack = new_psat.slack.values()[0]
    slack.v_magnitude = float(pf[slack.bus_no].v)
    slack.ref_angle = float(pf[slack.bus_no].phase)
    slack.p_guess = float(pf[slack.bus_no].pg)

    for gen in new_psat.generators.values():
        if gen.bus_no in pf:
            gen.p = float(pf[gen.bus_no].pg)
            gen.v = float(pf[gen.bus_no].v)
        else:
            print "ERROR:", gen.bus_no

    for load in new_psat.loads.values():
        if load.bus_no in pf:
            load.p = float(pf[load.bus_no].pl)
            load.q = float(pf[load.bus_no].ql)
        else:
            print "ERROR:", load.bus_no

    # fix for reactive power on bus 39-43
    # for x in range(39,44):
        # assert str(new_psat.generators[x].v) == "1.014"
        # new_psat.generators[x].v = "1.01401"

    # assert len(new_psat.shunts) == 0
    # assert new_psat.loads[6].q == "1.299"

    if not new_psat.in_limits():
        print "not in limits"
         
    assert new_psat.in_limits(), "new file is invalid. It hits static limits."
    
    return new_psat


def text_to_scenario(text):
    """func text_to_scenario     :: Str -> Scenario
       ----
       make `text` into a Scenario by reading as if a 
       single element batch file
    """
    
    with closing(StringIO(text)) as batch_stream:
        batch = SimulationBatch()
        batch.read(batch_stream)

    assert len(batch) == 1
    return list(batch)[0]


def scenario_to_psat(scenario, psat):
    """func scenario_to_psat     :: Scenario, PsatData -> PsatData
       ----
       Make a new PsatData based upon `psat` but contains the changes
       specified in the scenario.
    """

    new_psat = deepcopy(psat)

    for kill in scenario.kill_bus:
        new_psat.remove_bus(kill)
    for kill in scenario.kill_line:
        new_psat.remove_line(kill)
    for kill in scenario.kill_gen:
        new_psat.remove_generator(kill)
    if scenario.all_demand:
        new_psat.set_all_demand(scenario.all_demand)

    new_psat.fix_mismatch()
    return new_psat


def batch_simulate(batch, psat, size=10, clean=True):
    """func batch_simulate       :: SimulationBatch, PsatData, Int -> 
       ----
       Simulate all Scenarios in `batch` (with a base of `psat`) in groups
       of size `size`. Modify `batch` in place. delete all temp files
       if it succedes 

       TODO: simulate can throw so we want each batch in a try/except block
    """

    print "batch simulate %d cases" % len(batch)
    for n, group in enumerate(split_every(size, batch)):
        timer_start = time.clock()
        print "simulating batch", n + 1, "of", int(math.ceil(len(batch) / size)) + 1
        sys.stdout.flush()
     
        # make the matlab_script
        matlab_filename = "matlab_" + str(n)
        batch_matlab_script(matlab_filename + ".m", group)
        
        # write all the scenarios to file as psat_files
        for scenario in group:
            scenario.result = None

            try:
                new_psat = scenario_to_psat(scenario, psat)
            except Exception as ex:
                print "exception in scenario_to_psat",
                print scenario.title, ex
                scenario.result = "error"
                new_psat = deepcopy(psat)

            new_psat_filename = "psat_" + scenario.title + ".m"
            with open(new_psat_filename, "w") as new_psat_file:
                new_psat.write(new_psat_file)
        
        # run matlab 
        res = simulate(matlab_filename, False)
        assert len(res) == len(group)
        for r, scenario in zip(res, group):
            if not(r):
                print "did not converge", scenario.title
                scenario.result = "fail"
        
        # gather results
        for scenario in group:
            if not scenario.result:
                report_filename = "psat_" + scenario.title + "_01.txt"
                try:
                    report = read_report(report_filename)
                    scenario.result = report_in_limits(report)
                except Exception as ex:
                    print "exception in parsing/checking report",
                    print scenario.title, ex
                    scenario.result = "error"
                

        timer_end = time.clock()
        timer_time = (timer_end - timer_start)
        print "batch time of", int(math.ceil(timer_time)), "seconds"

    if clean:
        clean_files()


def single_simulate(psat, simtype, title, clean=True):
    """func single_simulate      :: PsatData, Str, Bool -> PsatReport
       ----
       run matlab with the PsatData `psat` as either 
       power flow (pf) or optimal power flow (opf)
       return the results of the simulation.
       remove temp files if specified
    """

    matlab_filename = "matlab_" + title
    psat_filename = "psat_" + title + ".m"
    report_filename = "psat_" + title + "_01.txt"

    # make the matlab_script
    single_matlab_script(matlab_filename + ".m", psat_filename, simtype)

    # write the PsatData to file
    assert(psat.in_limits())
    with open(psat_filename, "w") as psat_file:
        psat.write(psat_file)

    # run matlab 
    simulate(matlab_filename)

    # return the parsed report
    report = read_report(report_filename)
    if clean: 
        clean_files()
    return report


def simulate_scenario(psat, scenario, clean=True):
    """func simulate_scenario   :: PsatData, Scenario, Bool -> PsatReport
       ----
       make PsatData with `scenario` and `psat`. simulate it and 
       return the report. 
       remove temp files if specified
    """

    new_psat = scenario_to_psat(scenario, psat)
    return single_simulate(new_psat, scenario.simtype, scenario.title, clean)


def single_matlab_script(filename, psat_filename, simtype):
    """func single_matlab_script :: Str, Str, Str -> 
       ----
       create a matlab script file which simulates the psat_file specified
       either a a power flow (simtype='pf') or optimal power flow 
       (simtype='opf').
    """
    
    with open(filename, "w") as matlab_stream:

        matlab_stream.write("initpsat;\n")
        matlab_stream.write("Settings.lfmit = 50;\n")
        matlab_stream.write("Settings.violations = 'on'\n")
        matlab_stream.write("runpsat('" + psat_filename + "','data');\n")

        if simtype == "pf":
            matlab_stream.write("runpsat pf;\n")
        elif simtype == "opf":
            matlab_stream.write("OPF.basepg = 0;\n")
            matlab_stream.write("OPF.basepl = 0;\n")
            matlab_stream.write("runpsat opf;\n")
        else:
            raise Exception("expected pf or opf got: " + simtype)
        matlab_stream.write("runpsat pfrep;\n")
        matlab_stream.write("closepsat;\n")
        matlab_stream.write("exit;\n")


def batch_matlab_script(filename, batch):
    """func batch_matlab_script  :: Str, SimulationBatch -> 
       ----
       create a matlab script file which simulates all the Scenarios
       in the batch assuming their filename is 
           "psat_" + scenario.title + ".m"
    """


    assert len(batch) != 0
    with open(filename, "w") as matlab_stream:

        matlab_stream.write("initpsat;\n")
        matlab_stream.write("Settings.lfmit = 50;\n")
        matlab_stream.write("Settings.violations = 'on'\n")
        matlab_stream.write("OPF.basepg = 0;\n")
        matlab_stream.write("OPF.basepl = 0;\n")

        simtype = batch[0].simtype

        for scenario in batch:
            filename = "psat_" + scenario.title + ".m"
            matlab_stream.write("runpsat('" + filename + "','data');\n")

            assert simtype == scenario.simtype

            if simtype == "pf":
                matlab_stream.write("runpsat pf;\n")
            elif simtype == "opf":
                matlab_stream.write("runpsat opf;\n")
            else:
                raise Exception("expected pf or opf got: " + scenario.simtype)
            matlab_stream.write("runpsat pfrep;\n")

        matlab_stream.write("closepsat;\n")
        matlab_stream.write("exit\n")

def parse_matlab_output(text):

    def found(msg, in_text):
        return in_text.find(msg) != -1
    
    result = []
    split_by_sim = text.split("Newton-Raphson Method for Power Flow")
    for n, sim_text in enumerate(split_by_sim[1:]):

        passed = True

        if found("IPM-OPF", sim_text):
            if not found("IPM-OPF completed in", sim_text):
                print "opf not completed", n
                passed = False
        else:
            # we don't cae if the PF before the OPF fails. 
            if found("Warning: Matrix is singular", sim_text):
                print "singular matrix warning", n
                passed = False

            if found("Warning: Matrix is close to singular", sim_text):
                print "near singular matrix warning", n
                passed = False
                
            if found("The error is increasing too much", sim_text):
                print "large error", n
                passed = False

            if found("Convergence is likely not reachable", sim_text):
                print "non-convergence", n
                passed = False

            if not found("Power Flow completed in", sim_text):
                print "power flow not completed", n
                passed = False



        result.append(passed)

    assert len(result) >= 1, str(result)
    return result


def simulate(matlab_filename, single_item=True):
    """func simulate             :: Str -> [Bool]
       ----
       call matlab with the specified script.
    """

    try:

        # print "simulate", matlab_filename
        parameters = '-nodisplay -nojvm -nosplash -minimize -r '
        # parameters = '-automation -r '
        proc = subprocess.Popen('matlab ' + parameters + matlab_filename,
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE)

        so, se = proc.communicate()
     
        if (False):
            print "SE"
            print "================================="
            print se 
            print "================================="
            print "SO"
            print "================================="
            print so 
            print "================================="

        assert se == "", "sim-error: " + se

        result = parse_matlab_output(so)
        assert len(result) >= 1, str(result)

        if single_item:
            assert len(result) == 1
            if result[0]:
                print "simulate passed"
            else:
                print "did not converge (in simulate)"

        return result

    except:
        print "simulate failed"
        raise

#==============================================================================
# 
#==============================================================================

