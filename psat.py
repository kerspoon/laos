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

#------------------------------------------------------------------------------
#  Imports:
#------------------------------------------------------------------------------

import sys
import logging
from copy import deepcopy
from misc import *
import math
import random

#------------------------------------------------------------------------------
#  Logging:
#------------------------------------------------------------------------------

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
    format="%(levelname)s: %(message)s")

logger = logging.getLogger(__name__)

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

        return scen

    def failures(self, name):
        
        scen = Scenario("failure" + name, "pf")
        scen.kill["bus"] = [bus.bus_id for bus in self.busses if fail(bus.pfail)]
        scen.kill["line"] = [(line.fbus, line.tbus) for line in 
                             self.lines if fail(line.pfail)]
        scen.kill["generator"] = [generator.bus_id for generator in 
                                  self.generators if fail(generator.pfail)]
        scen.kill["line"] = scen.kill["line"] + self.crow_fails(scen.kill["line"])

        return scen

#------------------------------------------------------------------------------
#  NetworkData:
#------------------------------------------------------------------------------

def write_section(stream, items, title):
    """write one section of a Matlab file"""
    stream.write(title + ".con = [ ... \n")
    for item in items:
        stream.write("  " + str(item) + "\n")
    stream.write(" ];\n")

def read_section(stream, items, classtype):
    """read one section of Matlab file, assuming the header is done.
       and assuming that each line is one row ended by a semicolon. 
    """

    for line in stream:
        line = line.strip()

        if re.match("\A *\] *; *\Z", line): # if line == "];"
            break

        if len(line) == 0 or line.startswith("#"):
            continue

        cols = [x.lower() for x in line.replace(";"," ").split()]
        items.append(read_struct(classtype, cols))

class NetworkData(object):
    """matlab psat data file"""
 
    class Bus(struct):
        entries = "bus_no v_base v_magnitude_guess v_angle_guess area region".split()
        types = "int int real real int int".split()
 
    class Line(struct):
        entries = "fbus tbus s_rating v_rating f_rating length v_ratio r x b tap shift i_limit p_limit s_limit status".split()
        types = "int int int int int real real real real real real real real real real int".split()
 
    class Slack(struct):
        entries = "bus_no s_rating v_rating v_magnitude ref_angle q_max q_min v_max v_min p_guess lp_coeff ref_bus status".split()
        types = "int int int real real real real real real real real real int".split()

    class Generator(struct):
        entries = "bus_no s_rating v_rating p v q_max q_min v_max v_min lp_coeff status".split()
        types = "int int int real real real real real real real int".split()

    class Load(struct):
        entries = "bus_no s_rating v_rating p q v_max v_min z_conv status".split()
        types = "int int int real real real real real int".split()

    class Shunt(struct):
        entries = "bus_no s_rating v_rating f_rating g b status".split()
        types = "int int int int real real int".split()

    class Demand(struct):
        entries = "bus_no s_rating p_direction q_direction p_bid_max p_bid_min p_optimal_bid p_fixed p_proportional p_quadratic q_fixed q_proportional q_quadratic commitment cost_tie_break cost_cong_up cost_cong_down status".split()
        types = "int int real real real real real real real real real real real real real real real int".split()

    class Supply(struct):
        entries = "bus_no s_rating p_direction p_bid_max p_bid_min p_bid_actual p_fixed p_proportional p_quadratic q_fixed q_proportional q_quadratic commitment cost_tie_break lp_factor q_max q_min cost_cong_up cost_cong_down status".split()
        types = "int int real real real real real real real real real real real real real real real real real int".split()

    def __init__(self):
        self.busses = []
        self.lines = []
        self.slack = []
        self.generators = []
        self.loads = []
        self.shunts = []
        self.demand = []
        self.supply = []

    def read(self, stream):
        """might be easier to use the working one!"""

        def title_matches(line, title):
            #todo: replace with regexp
            return line.startswith(title)

        for line in stream:
            line = line.strip()

            if len(line) == 0 or line.startswith("#"):
                continue
            elif title_matches(line, "Bus.con"):
                read_section(stream, self.busses, self.Bus)
                assert len(self.busses) >= 1
            elif title_matches(line, "Line.con"):
                read_section(stream, self.lines, self.Line)
                assert len(self.lines) >= 1
            elif title_matches(line, "SW.con"):
                read_section(stream, self.slack, self.Slack)
                assert len(self.slack) == 1
            elif title_matches(line, "PV.con"):
                read_section(stream, self.generators, self.Generator)
                assert len(self.generators) >= 0
            elif title_matches(line, "PQ.con"):
                read_section(stream, self.loads, self.Load)
                assert len(self.loads) >= 1
            elif title_matches(line, "Shunt.con"):
                read_section(stream, self.shunts, self.Shunt)
                assert len(self.shunts) >= 0
            elif title_matches(line, "Demand.con"):
                read_section(stream, self.demand, self.Demand)
                assert len(self.demand) >= 0 
            elif title_matches(line, "Supply.con"):
                read_section(stream, self.supply, self.Supply)
                assert len(self.supply) >= 0
            else:
                raise Exception("expected matlab section, got " + line)
            
    def write(self, stream):
        write_section(stream, self.busses, "Bus")
        write_section(stream, self.lines, "Line")
        write_section(stream, self.slack, "SW")
        write_section(stream, self.generators, "PV")
        write_section(stream, self.loads, "PQ")
        write_section(stream, self.shunts, "Shunt")
        write_section(stream, self.demand, "Demand")
        write_section(stream, self.supply, "Supply")

    def remove_bus(self, bus_no):

        # list all matches
        matches = [x for x in self.busses if x.bus_no == bus_no]

        if len(matches) == 0:
            logger.info("Unable to find bus: " + str(bus_no))
            return

        # bus names must be unique
        assert len(matches) == 1
        
        # remove it 
        thebus = matches[0].bus_no
        self.busses.remove(matches[0])

        # kill all connecting items
        self.lines = filter(lambda x: x.fbus != thebus and x.tbus != thebus, self.lines)
        
        self.slack = filter(lambda x: x.bus_no != thebus, self.slack) 
        if len(self.slack) == 0:
            logger.info("todo: deal with deleting slack bus")

        self.generators = filter(lambda x: x.bus_no != thebus, self.generators)
        self.loads = filter(lambda x: x.bus_no != thebus, self.loads)
        self.shunts = filter(lambda x: x.bus_no != thebus, self.shunts)
        self.demand = filter(lambda x: x.bus_no != thebus, self.demand)
        self.supply = filter(lambda x: x.bus_no != thebus, self.supply)

    def remove_line(self, fbus, tbus, line_no=None):

        # does the given line (x) match the one we are looking for
        test = lambda x: (x.fbus == fbus and x.tbus == tbus) or (x.fbus == tbus and x.tbus == fbus)

        # list all matches
        matches = [x for x in self.lines if test(x)]

        # remove it 
        self.remove_item(matches, self.lines, line_no, (fbus, tbus))
            
    def remove_generator(self, bus_no, gen_no=None):
        
        # todo: deal with only deleting part of generators but 
        #       all of one supply 

        # list all matches
        gen_matches = [x for x in self.generators if x.bus_no == bus_no]
        supply_matches = [x for x in self.supply if x.bus_no == bus_no]

        # remove it 
        self.remove_item(gen_matches, self.generators, gen_no, bus_no)
        self.remove_item(supply_matches, self.supply, gen_no, bus_no)
        
    def remove_item(self, matches, iterable, item_no, bus_no):

        # error if no matches 
        if len(matches) == 0:
            logger.info("Unable to find item: " + str(bus_no))
        # simple if one match 
        elif len(matches) == 1:
            iterable.remove(matches[0])
        # remove only one if there is more
        elif len(matches) > 1:
            # if line number specified use that
            if item_no:
                assert item_no < len(matches)
                iterable.remove(matches[item_no])
            # otherwise remove first
            else:
                iterable.remove(matches[0])
        else:
            raise Exception("can't happen")

#------------------------------------------------------------------------------
#  SimulationBatch:
#------------------------------------------------------------------------------

class Scenario(object):
    def __init__(self, title, simtype="pf"):
        self.title = title
        self.simtype = simtype
        self.kill = {'bus':[], 'generator':[], 'line':[]}
        self.supply = {}
        self.demand = {}
        self.result = None

    def write(self, stream):

        stream.write("[" + self.title + "] " + self.simtype + "\n")
        for kill in self.kill["bus"]:
            stream.write("  remove bus " + str(kill) + "\n")
        for kill in self.kill["line"]:
            stream.write("  remove line " + as_csv(kill, " ") + "\n")
        for kill in self.kill["generator"]:
            stream.write("  remove generator " + str(kill) + "\n")
        for item in self.supply.items():
            stream.write("  set supply " + as_csv(item, " ") + "\n")
        for item in self.demand.items():
            stream.write("  set demand " + as_csv(item, " ") + "\n")
        
        if self.result != None: # damn python's multiple true values
            if self.result == True:
                stream.write("  result pass\n")
            else:
                stream.write("  result fail\n")

class SimulationBatch(object):
    """
       e.g. 
           [abc]
               remove bus 1
               remove bus 1 
               remove line 1 3
               remove generator 4
               set demand 1 1.27
           [def]
               set supply 58 0.41
           [ghi]
           [jkl]
               remove generator 2 
    """

    def __init__(self):
        self.scenarios = []

    def write(self, stream):
        for scenario in self.scenarios:
            scenario.write(stream)

    def read(self, stream):

        def add_kill(component, name):
            # add the kill to the current contingency
            self.scenarios[-1].kill[component].append(name)
            # logger.debug("Kill: %s[%s]" % (component, name))
        
        def set_supply(bus_no, value):
            self.scenarios[-1].supply[bus_no] = value
            # logger.debug("Set supply: bus[%s]=%f" % (bus_no, value))
        
        def set_demand(bus_no, value):
            self.scenarios[-1].demand[bus_no] = value
            # logger.debug("Set demand: bus[%s]=%f" % (bus_no, value))

        for line in stream:

            line = [x.lower() for x in line.split()]
        
            # comments
            if len(line) == 0 or line[0].startswith("#"):
                continue

            # title
            elif line[0].startswith("["):
                title = line[0][1:-1]
                simtype = line[1]
                assert simtype == "pf" or simtype == "opf"
                # logger.debug("Added Scenario: %s" % title)
                self.scenarios.append(Scenario(title, simtype))

            # remove 
            elif line[0] == "remove":
                if line[1] == "bus":
                    bus_no = int(line[2])
                    add_kill("bus",bus_no)
                elif line[1] == "line":
                    fbus = int(line[2])
                    tbus = int(line[3])
                    add_kill("line", (fbus, tbus))
                elif line[1] == "generator":
                    bus_no = int(line[2])
                    add_kill("generator",bus_no)
                else:
                    raise Exception("got %s expected (line, generator, bus)" % line[1])
            
            # set
            elif line[0] == "set":
                if line[1] == "supply":
                    bus_no = int(line[2])
                    value = float(line[3])
                    set_supply(bus_no, value)
                elif line[1] == "demand":
                    bus_no = int(line[2])
                    value = float(line[3])
                    set_demand(bus_no, value)
                else:
                    raise Exception("got %s expected (supply, demand)" % line[1])
           
            # ignore results 
            elif line[0] == "result":
                if line[1] == "pass":
                    self.scenarios[-1].result = True
                    # logger.debug("result pass")
                elif line[1] == "fail":
                    self.scenarios[-1].result = False
                    # logger.debug("result fail")
                else:
                    raise Exception("got %s expected (pass, fail)" % line[1])
                    
            # nothing else allowed
            else:
                raise Exception("got %s expected (remove, set, result, [...], #)" % line[0])

    def __iter__(self):
        return iter(self.scenarios)

#------------------------------------------------------------------------------
#  
#------------------------------------------------------------------------------

def write_scenario(stream, scenario, network):
    """write the network to the file with the changes specified in scenario
    """

    newpsat = deepcopy(network)

    for kill in scenario.kill["bus"]:
        newpsat.remove_bus(kill)
    for kill in scenario.kill["line"]:
        newpsat.remove_line(kill[0], kill[1])
    for kill in scenario.kill["generator"]:
        newpsat.remove_generator(kill)

    if not(len(scenario.supply) == 0 and len(scenario.demand) == 0):
        raise Exception("not implemented")
    
    newpsat.write(stream)




