#! /usr/local/bin/python
# network_probability.py NetworkProbability - prob_file - prob

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

"""
by James Brooks 2010
network_probability.py NetworkProbability - prob_file - prob
"""

#==============================================================================
#  Imports:
#==============================================================================

from misc import struct, read_struct, as_csv, Ensure, Error
import random
import math
import sys
import collections
from StringIO import StringIO

from simulation_batch import Scenario
import buslevel 

#==============================================================================
# eBNF
#==============================================================================

# See classdef.cls for the datatypes of the line elements.

#
# S        ::= cmtline* (infoline comment? nl cmtline* )*
# infoline ::= (busline | lineline | genline | crowline)
# busline  ::= 'bus' bus_id fail_rate repair_rate
# lineline ::= 'line' name fbus tbus fail_rate repair_rate trans_fail 
# genline  ::= 'generator' name bus_id mttf mttr gen_type
# crowline ::= 'crow' line1 line2 probability
# comments ::= '#' [A-Za-z0-9]*
# cmtline  ::= comments nl
# nl       ::= newline
#

#==============================================================================
# Example
#==============================================================================

# bus    101    0.025   13 
# bus    102    0.025   13 
# bus    103    0.025   13 
# line   A7     103     124   .02   768       0.0
# line   A8     104     109   .36   10        1.4
# generator    G47    213     950   50    U197         
# generator    G48    214     -1    -1    Sync Cond      
# crow   C25-2  C25-1   0.075
# crow   C30    C34     0.075
# crow   C34    C30     0.075

#==============================================================================
#
#==============================================================================

def probability_failure(failrate):
    # probability_failure :: real(>0) -> real(0,1)
    """returns the probability of a component 
    failing given the failure rate"""
    Ensure(failrate >= 0, "failrate: " + str(failrate))
    time = 1.0
    res = math.exp(-failrate * time)
    Ensure(0 <= res <= 1, "probability: " + str(res))
    return res


def probability_outage(mttf, mttr):
    # probability_outage :: real(>0), real(>0) -> real(0,1)
    """returns the probability of a component 
    being on outage given the mean time to fail
    and restore"""
    Ensure(mttf >= 0, "mttf: " + str(mttf))
    Ensure(mttr >= 0, "failratemttr: " + str(mttr))
    res = mttf / (mttf + mttr)
    Ensure(0 <= res <= 1, "probability: " + str(res))
    return res


def fail(pfail):
    return random.random() < pfail

#==============================================================================
#
#==============================================================================


class NetworkProbability(object):
    """
       np = psat.NetworkProbability(); np.read(open("rts.net"))
       np.outages().write(sys.stdout)

       A Data file containing the probability of failure of various components
       as well as joint failure of different components.

    """

    class Bus(struct):
        entries = "bus_id fail_rate repair_rate".split()
        types = "int real real".split()

        def setup(self):
            if self.fail_rate != 0.0:    
                failrate = self.fail_rate / (24.0 * 365.0)
                mttf = float((24.0 * 365.0) / self.fail_rate)
                mttr = float(self.repair_rate)
                self.pfail = 1 - probability_failure(failrate)
                self.pout = 1 - probability_outage(mttf, mttr)
            else:
                self.pfail = 0
                self.pout = 0
            # print "Bus: %f %f" % (self.pfail, self.pout)

    class Line(struct):
        entries = "name fbus tbus fail_rate repair_rate trans_fail".split()
        types = "str int int real real real".split()

        def setup(self):
            if self.fail_rate != 0.0:    
                failrate = self.fail_rate / (24.0 * 365.0)
                mttf = float((24.0 * 365.0) / self.fail_rate)
                mttr = float(self.repair_rate)
                self.pfail = 1 - probability_failure(failrate)
                self.pout = 1 - probability_outage(mttf, mttr)
            else:
                self.pfail = 0
                self.pout = 0
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
                self.pfail = 1 - probability_failure(failrate)
                # print mttf, mttr 
                self.pout = 1 - probability_outage(mttf, mttr)
            # print "Generator: %f %f" % (self.pfail, self.pout)

    class Crow(struct):
        entries = "line1 line2 probability".split()
        types = "str str real".split()

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
                raise Error("expected (bus, line, generator, crow) got " + cols[0])

    def write(self, stream):
        stream.write("# NetworkProbability data file\n")

        stream.write("# bus " + as_csv(self.Bus.entries, " ") + "\n")
        for bus in self.busses:
            stream.write("bus " + str(bus) + "\n")
            
        stream.write("# line " + as_csv(self.Line.entries, " ") + "\n")
        for line in self.lines:
            stream.write("line " + str(line) + "\n")

        stream.write("# generator " + as_csv(self.Generator.entries, " ") + "\n")
        for generator in self.generators:
            stream.write("generator " + str(generator) + "\n")

        stream.write("# crow " + as_csv(self.Crow.entries, " ") + "\n")
        for crow in self.crows:
            stream.write("crow " + str(crow) + "\n")

    def crow_fails(self, linekill):
        crowfails = []
        for kill in linekill:
            for crow in self.crows:
                if crow.line1 == kill:
                    if fail(crow.probability):
                        # print "crow fail:", crow.line1, kill
                        crowfails.append(crow.line2)
        return crowfails

    def outages(self, name):
        scen = Scenario("outage" + name, "opf")
        scen.kill_bus = [bus.bus_id for bus in self.busses if fail(bus.pout)]
        scen.kill_line = [line.name for line in 
                          self.lines if fail(line.pout)]
        scen.kill_gen = [generator.name for generator in 
                         self.generators if fail(generator.pout)]
        scen.kill_line = scen.kill_line + self.crow_fails(scen.kill_line)

        # quantize the forecast
        scen.all_demand = buslevel.quantised_05(buslevel.random_bus_forecast())
        return scen

    def failures(self, name):
        scen = Scenario("failure" + name, "pf")
        scen.kill_bus = [bus.bus_id for bus in self.busses if fail(bus.pfail)]
        scen.kill_line = [line.name for line in 
                          self.lines if fail(line.pfail)]
        scen.kill_gen = [generator.name for generator in 
                         self.generators if fail(generator.pfail)]
        scen.kill_line = scen.kill_line + self.crow_fails(scen.kill_line)

        # NOTE:: 1.0 should be the value of forcast load which will always
        #        be lower than 1, but it shouldn't make too much difference. 
        scen.all_demand = buslevel.quantised_05(buslevel.actual_load2(1.0))

        # mx = [g.pfail for g in self.generators]
        # print "%s\t%f\t%f\t%f\t%d\n" % (name, min(mx), max(mx), avg(mx), len(mx))

        return scen

    def write_stats(self, stream):
        
        Ensure(len(self.busses), "There must be more than one bus. Got %d" % len(self.busses))
        Ensure(len(self.lines), "There must be more than one line. Got %d" % len(self.lines))
        Ensure(len(self.generators), "There must be more than one generator. Got %d" % len(self.generators))
        Ensure(len(self.crows), "There must be more than one crow. Got %d" % len(self.crows))

        bus_pout = [x.pout for x in self.busses]
        bus_pfail = [x.pfail for x in self.busses]

        lines_pout = [x.pout for x in self.lines]
        lines_pfail = [x.pfail for x in self.lines]

        generators_pout = [x.pout for x in self.generators]
        generators_pfail = [x.pfail for x in self.generators]

        crows_prob = [x.probability for x in self.crows]


        def avg(x):
            return sum(x) / len(x)

        def helper(name, mx):
            if len(mx) == 0:
                stream.write("%s\t\t\t\t\n" % (name))
            stream.write("%s\t%f\t%f\t%f\t%d\n" % (name, min(mx), max(mx), avg(mx), len(mx)))
        
        stream.write("name\tmin\tmax\tavg\tlen\n")
        helper("Bus pout", bus_pout)
        helper("Bus pfail", bus_pfail)
        helper("Lin pout", lines_pout)
        helper("Lin pfail", lines_pfail)
        helper("Gen pout", generators_pout)
        helper("Gen pfail", generators_pfail)
        helper("Crow prob", crows_prob)

        


#==============================================================================
#
#==============================================================================



def example():
    
    text = """# NetworkProbability data file
# bus bus_id fail_rate repair_rate
bus 101 0.025 13.0
bus 102 0.025 13.0
bus 103 0.025 13.0
# line name fbus tbus fail_rate repair_rate trans_fail
line a7 103 124 0.02 768.0 0.0
line a8 104 109 0.36 10.0 1.4
# generator name bus_id mttf mttr gen_type
generator g47 213 950 50 u197
generator g48 214 -1 -1 synccond
# crow line1 line2 probability
crow c25-2 c25-1 0.075
crow c30 c34 0.075
crow c34 c30 0.075
"""

    np = NetworkProbability(); 
    np.read(StringIO(text))
    out = StringIO()
    np.write(out)

    assert out.getvalue() == text

    for _ in range(10000):
        scen = np.outages("test")
        scen2 = np.failures("test")

        scen.csv_write(sys.stdout)
        scen2.csv_write(sys.stdout)
# example()

def example2():

    np = NetworkProbability()
    np.read(open("rts.net"))
    np.write_stats(sys.stdout)
    print np.failures("bob")
# example2()


def TEST_crowfail():
       
    from simulation_batch import SimulationBatch

    text = """# NetworkProbability data file
# bus bus_id fail_rate repair_rate
bus 101 0.0 10.0
bus 102 0.0 10.0
bus 103 0.0 10.0
# line name fbus tbus fail_rate repair_rate trans_fail
line a1 101 102 100000000000.0 10.0 0.0
line a2 102 103 0.0 10.0 0.0
# crow line1 line2 probability
crow a1 a2 0.5
"""

    count = 100000

    prob = NetworkProbability() 
    prob.read(StringIO(text))

    batch = SimulationBatch()
    for x in range(count):
        batch.add(prob.outages(str(x)))
    assert count == len(batch)

    batch.write_stats(sys.stdout)

# TEST_crowfail()


def TEST_bus_level_quantise():
    
    count = 1000000

    prob = NetworkProbability()
    prob.read(StringIO(""))

    out_set_count = collections.defaultdict(int)
    fail_set_count = collections.defaultdict(int)
    for _ in range(count):
        out_set_count[str(prob.outages("x").all_demand)] += 1
        fail_set_count[str(prob.failures("x").all_demand)] += 1
    
    stream = sys.stdout
    print "-" * 80
    for x in out_set_count.items():
        stream.write("%s\t%d\n" % x)
    print "-" * 80
    for x in fail_set_count.items():
        stream.write("%s\t%d\n" % x)
    print "-" * 80

# TEST_bus_level_quantise()
