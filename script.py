#! /usr/local/bin/python
# scripts for laos
 
#------------------------------------------------------------------------------
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
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
# Imports:
#------------------------------------------------------------------------------


from __future__ import with_statement 
from misc import grem, split_every
from copy import deepcopy
import subprocess
from StringIO import StringIO
from contextlib import closing

from simulation_batch import SimulationBatch
from network_probability import NetworkProbability
from psat_data import PsatData
from psat_report import PsatReport


#------------------------------------------------------------------------------
# 
#------------------------------------------------------------------------------


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
    grem(".", r".*_[1234567890]{2}\.txt")


def make_outages(prob, count):
    """func make_outages         :: NetworkProbability, Int -> SimulationBatch
       ----
       Monte Carlo sample the network for it's expected condition. 
       e.g. existing outages, weather & load forcast, etc.
    """
    batch = SimulationBatch()
    for x in range(count):
        batch.add(prob.outages(str(x)))
    assert count == len(batch)
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
    return batch


def read_file(filename, datatype):
    """func read_file            :: Str, x -> x
       ----
       read a generic file into it class 'datatype'.
    """
    with open(filename) as thefile:
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
    """report_in_limits          :: PsatReport -> Str
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

    assert len(psat.lines) == report.num_line
    assert len(psat.slack) == 1
    assert len(psat.generators) == report.num_generator
    assert len(psat.busses) == report.num_bus
    assert len(psat.loads) == report.num_load
    assert len(psat.demand) == 0
    assert len(psat.supply) == len(psat.loads)    

    new_psat = deepcopy(psat)
    pf = report.power_flow

    slack = new_psat.slack[0]
    slack.v_magnitude = pf[slack.bus_no].v
    slack.ref_angle = pf[slack.bus_no].phase
    # slack.p_guess = pf[slack.bus_no].pg

    for gen in new_psat.generators:
        assert pf[gen.bus_no] != None
        gen.p = pf[gen.bus_no].pg
        gen.v = pf[gen.bus_no].v

    for load in new_psat.loads:
        assert pf[load.bus_no] != None
        load.p = pf[load.bus_no].pg
        load.q = pf[load.bus_no].q

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
    return batch[0]


def scenario_to_psat(scenario, psat):
    """func scenario_to_psat     :: Scenario, PsatData -> PsatData
       ----
       Make a new PsatData based upon `psat` but contains the changes
       specified in the scenario.
    """

    new_psat = deepcopy(psat)

    for kill in scenario.kill["bus"]:
        new_psat.remove_bus(kill)
    for kill in scenario.kill["line"]:
        new_psat.remove_line(kill[0], kill[1])
    for kill in scenario.kill["generator"]:
        new_psat.remove_generator(kill)
    if scenario.all_supply:
        new_psat.set_all_supply(scenario.all_supply)
    if scenario.all_demand:
        new_psat.set_all_demand(scenario.all_demand)
    if not(len(scenario.supply) == 0 and len(scenario.demand) == 0):
        raise Exception("not implemented")

    return new_psat


def batch_simulate(batch, psat, size=10):
    """func batch_simulate       :: SimulationBatch, PsatData, Int -> 
       ----
       Simulate all Scenarios in `batch` (with a base of `psat`) in groups
       of size `size`. Modify `batch` in place. delete all temp files
       if it succedes 

       Note:: what should we do on parsing error for report 
    """

    for n, group in enumerate(split_every(size, batch)):
     
        # make the matlab_script
        matlab_filename = "matlab_" + str(n)
        batch_matlab_script(matlab_filename + ".m", group)
        
        # write all the scenarios to file as psat_files
        for scenario in group:
            new_psat = scenario_to_psat(scenario, psat)
            new_psat_filename = "psat_" + scenario.title + ".m"
            with open(new_psat_filename, "w") as new_psat_file:
                new_psat.write(new_psat_file)
        
        # run matlab 
        simulate(matlab_filename)
        
        # gather results
        for scenario in group:
            report_filename = "psat_" + scenario.title + "_01.txt"
            try:
                report = read_report(report_filename)
                scenario.result = report_in_limits(report)
            except:
                scenario.result = "error"
    clean_files()

def single_simulate(psat, simtype):
    """func single_simulate      :: PsatData, Str -> PsatReport
       ----
       run matlab with the PsatData `psat` as either 
       power flow (pf) or optimal power flow (opf)
       return the results of the simulation.
    """

    title = "000"
    matlab_filename = "matlab_" + title
    psat_filename = "psat_" + title + ".m"
    report_filename = "psat_" + title + "_01.txt"

    # make the matlab_script
    single_matlab_script(matlab_filename + ".m", psat_filename, simtype)

    # write the PsatData to file
    with open(psat_filename, "w") as psat_file:
        psat.write(psat_file)

    # run matlab 
    res = simulate(matlab_filename)

    # return the parsed report
    report = read_report(report_filename)
    clean_files()
    return report


def simulate_scenario(psat, scenario):
    """func simulate_scenario   :: PsatData, Scenario -> PsatReport
       ----
       make PsatData with `scenario` and `psat`. simulate it and 
       return the report.
    """

    new_psat = scenario_to_psat(scenario, psat)
    return single_simulate(new_psat, scenario.simtype)


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
            matlab_stream.write("runpsat pf;\n")
            matlab_stream.write("runpsat opf;\n")
        else:
            raise Exception("expected pf or opf got: " + simtype)
        matlab_stream.write("runpsat pfrep;\n")
        matlab_stream.write("closepsat;\n")
        matlab_stream.write("exit\n")


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

        for scenario in batch:
            filename = "psat_" + scenario.title + ".m"
            matlab_stream.write("runpsat('" + filename + "','data');\n")

            if scenario.simtype == "pf":
                matlab_stream.write("runpsat pf;\n")
            elif scenario.simtype == "opf":
                matlab_stream.write("runpsat pf;\n")
                matlab_stream.write("runpsat opf;\n")
            else:
                raise Exception("expected pf or opf got: " + scenario.simtype)
            matlab_stream.write("runpsat pfrep;\n")

        matlab_stream.write("closepsat;\n")
        matlab_stream.write("exit\n")


def simulate(matlab_filename):
    """func simulate             :: Str -> Bool
       ----
       call matlab with the specified script.

       TODO:: parse the so and se for errors! 
       TODO:: do something with the return value or exception
    """

    try:

        print "simulate", matlab_filename
        parameters = '-nodisplay -nojvm -nosplash -r '
        proc = subprocess.Popen('matlab ' + parameters + matlab_filename,
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE)

        so, se = proc.communicate()
     
        assert se == "", "sim-error: " + se

        # print "SE"
        # print "================================="
        # print se 
        # print "================================="
     
        print "SO"
        print "================================="
        print so 
        print "================================="

        return True

    except:
        print "simulate failed"
        raise

#------------------------------------------------------------------------------
# 
#------------------------------------------------------------------------------


def example1(n = 30):
    """make `n` outages, simulate them, and save the resulting batch"""

    psat = read_psat("rts.m")
    prob = read_probabilities("rts.net")
    batch = make_outages(prob, n)

    batch_simulate(batch, psat)

    with open("rts.bch", "w") as result_file:
        batch.write(result_file)


# example1()


def example2(report_filename = "tmp_01.txt"):
    """test a report and actually see why if fails"""
    
    with open(report_filename) as report_file:
        report = PsatReport()
        res = report.read(report_file)
        print "result =", res, "."


# example2()


def example3():
    """one random failure"""
    
    psat = read_psat("rts.m")
    prob = read_probabilities("rts.net")
    batch = make_failures(prob, 1)
    scenario = batch[0]
    report = simulate_scenario(psat, scenario)
    print "result =", report_in_limits(report), "."


# example3()


def example4():
    """one specified scenario, simulated"""


    data = """
      [outage28] opf
        remove line 6 10
        remove generator 1
        remove generator 1
        set all demand 0.5192
        result fail
          """

    scenario = text_to_scenario(data)
    psat = read_psat("rts.m")
    report = simulate_scenario(psat, scenario)

    print "result =", report_in_limits(report), "."


# example4()


def create_base(scenario, psat):
    """take a scenario, sim it. get the results 
       use results to make new PsatData, return it
    """
    assert scenario.simtype == "opf"
    report = simulate_scenario(psat, scenario)
    assert report_in_limits(report)

    # NOTE:: do I have to use the new_psat in simulate_scenario
    #        as this might have certain things removed properly
    #        best yet would be for report_to_psat to fail if 
    #        the component numbers don't match. 

    return report_to_psat(report, psat)
    

def example5():
    prob = read_probabilities("rts.net")
    scenario = prob.outages("000")
    psat = read_psat("rts.m")
    new_psat = create_base(scenario, psat)

    report = single_simulate(new_psat, "pf")
    assert report_in_limits(report)


example5()

