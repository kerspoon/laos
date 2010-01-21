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
from misc import grem
from psat import SimulationBatch, NetworkProbability, NetworkData
from psat_report import PsatReport
from copy import deepcopy
import subprocess

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
    grem(".", r"solve_.*\.m")
    grem(".", r".*\.pyc")
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
    """func read_probabilities   :: Str -> NetworkData
       ----
       read a net_file into NetworkProbability.
    """
    return read_file(filename, NetworkProbability)
    

def read_psat(filename):
    """func read_psat         :: Str -> NetworkData
       ----
       read a psat_file into NetworkData.
    """
    return read_file(filename, NetworkData)


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
    """report_in_limits          :: PsatReport -> Bool
       ----
       is the results of the simulation in limits based on report
    """
    # need to change the PsatReport class to get this working nicely
    return report.inlimit()


def report_to_psat(report, psat):
    """func report_to_psat       :: PsatReport, NetworkData -> NetworkData
       ----
       Make a new NetworkData based upon `psat` but contains the voltage,
       angle, and power values from `report`.
    """

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


def scenario_to_psat(scenario, psat):
    """func scenario_to_psat     :: Scenario, NetworkData -> NetworkData
       ----
       Make a new NetworkData based upon `psat` but contains the changes
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


def batch_simulate(batch, psat):
    """func batch_simulate       :: SimulationBatch, NetworkData -> 
       ----
       
       Note:: modify and return `batch` 
       Note:: should it clean up after its self (grem matalb_ etc.)
       Note:: should report_in_limits throw or return Str for failure
    """

    title = "000"

    # make the matlab_script
    matlab_filename = "matlab_" + title + ".m"
    batch_matlab_script(matlab_filename, batch)

    # write all the scenarios to file as psat_files
    for scenario in batch:
        new_psat = scenario_to_psat(scenario, psat)
        new_psat_filename = "psat_" + scenario.title + ".m"
        with open(new_psat_filename, "w") as new_psat_file:
            new_psat.write(new_psat_file)

    # run matlab 
    simulate(matlab_filename)

    # gather results
    for scenario in batch:
        report_filename = "psat_" + scenario.title + "_01.txt"
        with open(report_filename) as report_file:
            report = read_report(report_file)
            scenario.result = report_in_limits(report)


def single_simulate(psat, simtype):
    """func single_simulate      :: NetworkData, Str -> Bool
       ----
       run matlab with the NetworkData `psat` as either 
       power flow (pf) or optimal power flow (opf)
       return the results of the simulation.
    """

    title = "000"
    matlab_filename = "matlab_" + title + ".m"
    psat_filename = "psat_" + title + ".m"
    report_filename = "psat_" + title + "_01.txt"

    # make the matlab_script
    single_matlab_script(matlab_filename, psat_filename, simtype)

    # write the NetworkData to file
    with open(psat_filename, "w") as psat_file:
        psat.write(psat_file)

    # run matlab 
    simulate(matlab_filename)

    # return result
    with open(report_filename) as report_file:
        report = read_report(report_file)
        return report_in_limits(report)


def single_matlab_script(filename, psat_filename, simtype):
    """func single_matlab_script :: Str, Str, Str -> 
       ----
       create a matlab script file which simulates the psat_file specified
       either a a power flow (simtype='pf') or optimal power flow 
       (simtype='opf').
    """
    
    with open(filename) as matlab_stream:

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
    with open(filename) as matlab_stream:

        matlab_stream.write("initpsat;\n")
        matlab_stream.write("Settings.lfmit = 50;\n")
        matlab_stream.write("Settings.violations = 'on'\n")

        for scenario in batch:
            filename = "psat_" + scenario.title + ".m"
            matlab_stream.write("runpsat('" + filename + "','data');\n")

            if scenario.simtype == "pf":
                matlab_stream.write("runpsat pf;\n")
            elif scenario.simtype == "opf":
                matlab_stream.write("OPF.basepg = 0;\n")
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
    """

    proc = subprocess.Popen('matlab -nodisplay -nojvm -nosplash -r ' + matlab_filename,
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


