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

import unittest
from modifiedtestcase import ModifiedTestCase
from StringIO import StringIO
from misc import as_csv

#------------------------------------------------------------------------------
#  eBNF
#------------------------------------------------------------------------------

#
# S        ::= entry+ 
# entry    ::= head newline (infoline newline)* 
# head     ::= '[' title ']' simtype
# simtype  ::= 'pf' | 'opf'
# infoline ::= 'remove bus' BusNo 
# infoline ::= 'remove line' Cid
# infoline ::= 'remove generator' Cid
# infoline ::= 'set all demand' Real
# infoline ::= 'result' ('pass' | 'fail' | 'error')
# 
# type BusNo -> PInt
# type Cid   -> Str
#

#------------------------------------------------------------------------------
# Example File 
#------------------------------------------------------------------------------
 
#  
# [abc]
#     remove bus 1
#     remove line A3
#     remove line A54
# [def]
# [ghi]
#     remove generator G65
# [jkl]
#     set all demand 1.25
#

#------------------------------------------------------------------------------
#  
#------------------------------------------------------------------------------


class Scenario(object):

    def __init__(self, title, simtype="pf"):
        self.title = title
        self.simtype = simtype
        self.kill_bus = []
        self.kill_gen = []
        self.kill_line = []
        self.all_demand = None
        self.result = None

    def invariant(self):
        assert len(self.title) > 0
        assert self.simtype in set(["pf", "opf"])
        if self.result:
            assert self.result in set(["pass", "fail", "error"])

    def write(self, stream):
        self.invariant()
        stream.write("[" + self.title + "] " + self.simtype + "\n")
        for kill in self.kill_bus:
            stream.write("  remove bus " + str(kill) + "\n")
        for kill in self.kill_line:
            stream.write("  remove line " + kill + "\n")
        for kill in self.kill_gen:
            stream.write("  remove generator " + kill + "\n")
        if self.all_demand:
            stream.write("  set all demand " + str(self.all_demand) + "\n")
        if self.result:
            stream.write("  result " + self.result + "\n")

    def csv_write(self, stream):
        self.invariant()
        infoline = [self.title, self.simtype, self.all_demand, self.result]
        kills = self.kill_bus + self.kill_line + self.kill_gen
        stream.write(as_csv(infoline + kills)  + "\n")
        


#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


class SimulationBatch(object):
    """
       not really sure if this class is needed at all
       it's basically just scenario_file_read/write 
       nothing else is useful in it. 
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

    def csv_write(self, stream):
        for scenario in self.scenarios:
            scenario.csv_write(stream)

    def read(self, stream):

        def add_kill(component, name):
            # add the kill to the current contingency
            self.scenarios[-1].kill[component].append(name)

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
                    self.scenarios[-1].kill_bus.append(int(line[2]))
                elif line[1] == "line":
                    self.scenarios[-1].kill_line.append(line[2])
                elif line[1] == "generator":
                    self.scenarios[-1].kill_gen.append(line[2])
                else:
                    raise Exception("got %s expected (line, generator, bus)" 
                                    % line[1])
            
            # set
            elif line[0] == "set":
                if line[1:3] == ["all","demand"]:
                    self.scenarios[-1].all_demand = float(line[3])
                else:
                    raise Exception("got %s expected 'demand'" % line[1])
                
            # results 
            elif line[0] == "result":
                assert line[1] in set("pass fail error".split())
                self.scenarios[-1].result = line[1]

            # nothing else allowed
            else:
                raise Exception("got %s expected (remove, set, result, [])" 
                                % line[0])

        self.scenarios[-1].invariant()


#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


class Test_read(ModifiedTestCase):

    def util_readwrite_match(self, inp):
        sb = SimulationBatch()        
        sb.read(StringIO(inp))
        stream = StringIO()
        sb.write(stream)
        self.assertEqual(stream.getvalue(), inp)
        
    def test_1(self):
        self.util_readwrite_match("""[name123] pf\n""")
        self.util_readwrite_match("""[name123] opf\n""")
        self.util_readwrite_match(
            """[name123] pf
  remove bus 1
""")
        self.util_readwrite_match(
            """[name123] pf
  remove bus 10
""")
        self.util_readwrite_match(
            """[name123] pf
  remove line a4
""")
        self.util_readwrite_match(
            """[name123] pf
  remove generator g10
""")
        self.util_readwrite_match(
            """[name123] pf
  remove line a9
  remove generator g11
""")
        self.util_readwrite_match(
            """[name123] pf
  set all demand 0.86
  result fail
""")


#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


if __name__ == '__main__':
    unittest.main()


#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------

