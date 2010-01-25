#! /usr/local/bin/python
# network_probability.py NetworkProbability - prob_file - prob

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

"""
by James Brooks 2010
network_probability.py NetworkProbability - prob_file - prob
"""

#------------------------------------------------------------------------------
#  Imports:
#------------------------------------------------------------------------------

from misc import struct, read_struct, as_csv
import random
import math

from simulation_batch import Scenario
import buslevel 

#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


def probability_failure(failrate):
    # probability_failure :: real(>0) -> real(0,1)
    """returns the probability of a component 
    failing given the failure rate"""
    assert(failrate >= 0), "failrate: " + str(failrate)
    time = 1.0
    res = math.exp(-failrate * time)
    assert(0 <= res <= 1), "probability: " + str(res)
    return res


def probability_outage(mttf, mttr):
    # probability_outage :: real(>0), real(>0) -> real(0,1)
    """returns the probability of a component 
    being on outage given the mean time to fail
    and restore"""
    assert(mttf >= 0), "mttf: " + str(mttf)
    assert(mttr >= 0), "failratemttr: " + str(mttr)
    res = mttf / (mttf + mttr)
    assert(0 <= res <= 1), "probability: " + str(res)
    return res


def fail(pfail):
    return random.random() < pfail

#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


class NetworkProbability(object):
    """
       np = psat.NetworkProbability(); np.read(open("rts.net"))
       np.outages().write(sys.stdout)

       A Data file containing the probability of failure of various components
       as well as joint failure of different components.

       e.g. 
           bus , 101 , 0.025 , 13 
           bus , 102 , 0.025 , 13 
           bus , 103 , 0.025 , 13 
           line , A7    , 103 , 124 , .02 ,   768 ,  0.0
           line , A8    , 104 , 109 , .36 ,    10 ,  1.4
           gen , G47 , 213 , 950  ,  50  ,   U197         
           gen , G48 , 214 , -1   ,  -1  , Sync Cond      
           crow , C25-2 , C25-1 , 0.075
           crow , C30   , C34   , 0.075
           crow , C34   , C30   , 0.075
    """

    class Bus(struct):
        entries = "bus_id fail_rate repair_rate".split()
        types = "int real real".split()

        def setup(self):
            failrate = self.fail_rate / (24.0 * 365.0)
            mttf = float((24.0 * 365.0) / self.fail_rate)
            mttr = float(self.repair_rate)
            self.pfail = 1-probability_failure(failrate)
            self.pout = 1-probability_outage(mttf, mttr)
            # print "Bus: %f %f" % (self.pfail, self.pout)

    class Line(struct):
        entries = "name fbus tbus fail_rate repair_rate trans_fail".split()
        types = "str int int real real real".split()

        def setup(self):
            failrate = self.fail_rate / (24.0 * 365.0)
            mttf = float((24.0 * 365.0) / self.fail_rate)
            mttr = float(self.repair_rate)
            self.pfail = 1-probability_failure(failrate)
            self.pout = 1-probability_outage(mttf, mttr)
            # print "Line: %f %f" % (self.pfail , self.pout)

    class Generator(struct):
        entries = "name bus_id mttf mttr gen_type".split()
        types = "str int int int str".split()

        def setup(self):
            if self.mttf == -1 or self.mttr == -1:
                self.pfail = 0 
                self.pout = 0 
            else:
                failrate = 1.0 / self.mttf
                mttf = float(self.mttf)
                mttr = float(self.mttr)
                self.pfail = 1-probability_failure(failrate)
                # print mttf, mttr 
                self.pout = 1-probability_outage(mttf, mttr)
            # print "Generator: %f %f" % (self.pfail, self.pout)

    class Crow(struct):
        entries = "line1 line2 probability".split()
        types = "str str real".split()
        
        def setup(self, lines):
            for line in lines:
                if line.name == self.line1:
                    self.line_1_id = line.fbus, line.tbus
                if line.name == self.line2:
                    self.line_2_id = line.fbus, line.tbus

    def __init__(self):
        self.busses = []
        self.lines = []
        self.generators = []
        self.crows = []

    def read(self, stream):
        for line in stream:
            cols = [x.lower() for x in line.split()]
            
            if len(cols) == 0 or cols[0].startswith("#"):
                continue
            elif cols[0] == "bus":
                self.busses.append(read_struct(self.Bus, cols[1:]))
                self.busses[-1].setup()
            elif cols[0] == "line":
                self.lines.append(read_struct(self.Line, cols[1:]))
                self.lines[-1].setup()
            elif cols[0] == "generator":
                self.generators.append(read_struct(self.Generator, cols[1:]))
                self.generators[-1].setup()
            elif cols[0] == "crow":
                self.crows.append(read_struct(self.Crow, cols[1:]))
            else:
                raise Exception("expected (bus, line, generator, crow) got " + cols[0])

        for crow in self.crows:
            crow.setup(self.lines)

    def write(self, stream):
        stream.write("# NetworkProbability data file\n")

        stream.write("# bus " + as_csv(self.Bus.entries," ") + "\n")
        for bus in self.busses:
            stream.write("bus " + str(bus) + "\n")
            
        stream.write("# line " + as_csv(self.Line.entries," ") + "\n")
        for line in self.lines:
            stream.write("line " + str(line) + "\n")

        stream.write("# generator " + as_csv(self.Generator.entries," ") + "\n")
        for generator in self.generators:
            stream.write("generator " + str(generator) + "\n")

        stream.write("# crow " + as_csv(self.Crow.entries," ") + "\n")
        for crow in self.crows:
            stream.write("crow " + str(crow) + "\n")

    def crow_fails(self, linekill):
        crowfails = []
        for kill in linekill:
            for crow in self.crows:
                if crow.line_1_id == kill:
                    if fail(crow.probability):
                        print "crow fail:", crow.line_1_id, kill
                        crowfails.append(crow.line_2_id)
        return crowfails

    def outages(self, name):
        scen = Scenario("outage" + name, "opf")
        scen.kill["bus"] = [bus.bus_id for bus in self.busses if fail(bus.pout)]
        scen.kill["line"] = [(line.fbus, line.tbus) for line in 
                             self.lines if fail(line.pout)]
        scen.kill["generator"] = [generator.bus_id for generator in 
                                  self.generators if fail(generator.pout)]
        scen.kill["line"] = scen.kill["line"] + self.crow_fails(scen.kill["line"])
        scen.all_demand = buslevel.random_bus_forecast()
        return scen

    def failures(self, name):
        scen = Scenario("failure" + name, "pf")
        scen.kill["bus"] = [bus.bus_id for bus in self.busses if fail(bus.pfail)]
        scen.kill["line"] = [(line.fbus, line.tbus) for line in 
                             self.lines if fail(line.pfail)]
        scen.kill["generator"] = [generator.bus_id for generator in 
                                  self.generators if fail(generator.pfail)]
        scen.kill["line"] = scen.kill["line"] + self.crow_fails(scen.kill["line"])

        # NOTE:: 1.0 should be the value of forcast load which will always
        #        be lower than 1, but it shouldn't make too much difference. 
        scen.all_demand = buslevel.actual_load2(1.0)
        return scen


#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------

