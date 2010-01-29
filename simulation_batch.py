#! /usr/local/bin/python
# simulation_batch.py - SimulationBatch - batch_file - batch

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
simulation_batch.py - SimulationBatch - batch_file - batch
"""

#------------------------------------------------------------------------------
#  Imports:
#------------------------------------------------------------------------------

from misc import as_csv 

#------------------------------------------------------------------------------
#  
#------------------------------------------------------------------------------

class Scenario(object):

    def __init__(self, title, simtype="pf"):
        self.title = title
        self.simtype = simtype
        self.kill = {'bus':[], 'generator':[], 'line':[]}
        self.all_supply = None 
        self.all_demand = None
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
        if self.all_supply:
            stream.write("  set all supply " + str(self.all_supply) + "\n")
        if self.all_demand:
            stream.write("  set all demand " + str(self.all_demand) + "\n")
        for item in self.supply.items():
            stream.write("  set supply " + as_csv(item, " ") + "\n")
        for item in self.demand.items():
            stream.write("  set demand " + as_csv(item, " ") + "\n")
        if self.result != None:
            stream.write("  result " + self.result + "\n")


#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


class SimulationBatch(object):
    """
       not really sure if this class is needed at all
       it's basically just scenario_file_read/write 
       nothing else is useful in it. 

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

    def __iter__(self):
        return iter(self.scenarios)

    def __len__(self):
        return len(self.scenarios)

    def __getitem__(self, key):
        return self.scenarios[key]

    def add(self, scenario):
        self.scenarios.append(scenario)

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

        def set_all_demand(value):
            self.scenarios[-1].all_demand = value

        def set_all_supply(value):
            self.scenarios[-1].all_supply = value

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
                elif line[1:3] == ["all","supply"]:
                    value = float(line[3])
                    set_all_supply(value)
                elif line[1:3] == ["all","demand"]:
                    value = float(line[3])
                    set_all_demand(value)
                else:
                    raise Exception("got %s expected (all?, supply, demand)" % line[1])
           
            # results 
            elif line[0] == "result":
                assert line[1] in set("pass fail error".split())
                self.scenarios[-1].result = line[1]

            # nothing else allowed
            else:
                raise Exception("got %s expected (remove, set, result, [...], #)" % line[0])


#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------

