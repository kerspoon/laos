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

from StringIO import StringIO
from misc import as_csv
from modifiedtestcase import ModifiedTestCase
import collections
import hashlib
import unittest

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

    def __init__(self, title, simtype="pf", count=1):
        self.title = title
        self.simtype = simtype
        self.count = count
        self.kill_bus = []
        self.kill_gen = []
        self.kill_line = []
        self.all_demand = None
        self.result = None

    def invariant(self):
        assert len(self.title) > 0
        assert self.count > 0
        assert self.simtype in set(["pf", "opf"])
        if self.result:
            assert self.result in set(["pass", "fail", "error"])

    def write(self, stream):
        self.invariant()

        if self.count != 1:
            stream.write("[%s] %s %d\n" % (self.title, self.simtype, self.count))
        else:
            stream.write("[%s] %s\n" % (self.title, self.simtype))
            
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
        infoline = [self.title, self.simtype, self.count, self.all_demand, self.result]
        kills = self.kill_bus + self.kill_line + self.kill_gen
        stream.write(as_csv(infoline + kills,"\t")  + "\n")

    def num_kills(self):
        return len(self.kill_bus) + len(self.kill_gen) + len(self.kill_line)

    def dicthash(self):
        """returns a text of the csv value *without* the count title or 
           result. To be used to store a Scenario in a dict"""
        self.invariant()
        infoline = [self.simtype, self.all_demand]
        kills = self.kill_bus + self.kill_line + self.kill_gen
        return as_csv(infoline + kills,"\t")

    def equal(self, other):
        """doesn't compare: count, result, or title"""
        self.invariant()
        other.invariant()
        if self.simtype != other.simtype: return False
        if self.all_demand != other.all_demand: return False
        if self.kill_bus != other.kill_bus: return False
        if self.kill_line != other.kill_line: return False
        if self.kill_gen != other.kill_gen: return False
        return True

    def increment(self, val=1):
        self.count += val


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
        self.scenarios = {}

    def __iter__(self):
        return iter(self.scenarios.values())

    def __len__(self):
        return len(self.scenarios)

    def size(self):
        return sum(x.count for x in self)

    def add(self, scenario):

        # if already added increment count rather than append.

        scenario.invariant()
        dicthash = scenario.dicthash()

        if dicthash in self.scenarios:
            
            # print "Updated [%d] = %s" % (self.scenarios[dicthash].count+1, 
            #                              dicthash)

            # make sure we don't have hash collision
            assert self.scenarios[dicthash].equal(scenario)

            # make sure we keep result info
            if scenario.result:
                if self.scenarios[dicthash].result:
                    assert scenario.result == self.scenarios[dicthash].result
                else:
                    self.scenarios[dicthash].result = scenario.result

            self.scenarios[dicthash].increment(scenario.count)
        else:
            # print "New [1]", dicthash
            self.scenarios[dicthash] = scenario

    def write(self, stream):
        for scenario in self:
            scenario.write(stream)

    def csv_write(self, stream):
        for scenario in self:
            scenario.csv_write(stream)

    def read(self, stream):

        current_scen = None

        for line in stream:

            line = [x.lower() for x in line.split()]
        
            # comments
            if len(line) == 0 or line[0].startswith("#"):
                continue

            # title
            elif line[0].startswith("["):
                if current_scen is not None:
                    # logger.debug("Added Scenario: %s" % title)
                    self.add(current_scen)

                title = line[0][1:-1]
                simtype = line[1]

                if len(line) == 3:
                    count = int(line[2])
                else:
                    assert len(line) == 2
                    count = 1

                assert simtype == "pf" or simtype == "opf"
                current_scen = Scenario(title, simtype, count)

            # remove 
            elif line[0] == "remove":
                if line[1] == "bus":
                    current_scen.kill_bus.append(int(line[2]))
                elif line[1] == "line":
                    current_scen.kill_line.append(line[2])
                elif line[1] == "generator":
                    current_scen.kill_gen.append(line[2])
                else:
                    raise Exception("got %s expected (line, generator, bus)" 
                                    % line[1])
            
            # set
            elif line[0] == "set":
                if line[1:3] == ["all","demand"]:
                    current_scen.all_demand = float(line[3])
                else:
                    raise Exception("got %s expected 'demand'" % line[1])
                
            # results 
            elif line[0] == "result":
                assert line[1] in set("pass fail error".split())
                current_scen.result = line[1]

            # nothing else allowed
            else:
                raise Exception("got %s expected (remove, set, result, [])" 
                                % line[0])


        if current_scen is not None:
            # logger.debug("Added Scenario: %s" % title)
            self.add(current_scen)

    def write_stats(self, stream):

        stream.write("batch\t%d\t%d\n" % (self.size(), len(self)))
        
        result_count = collections.defaultdict(int)
        fail_count = collections.defaultdict(int)

        bus_count = collections.defaultdict(int)
        line_count = collections.defaultdict(int)
        gen_count = collections.defaultdict(int)

        for scen in self:
            fail_count[scen.num_kills()] += scen.count
            result_count[str(scen.result)] += scen.count
            bus_count[len(scen.kill_bus)] += scen.count
            line_count[len(scen.kill_line)] += scen.count
            gen_count[len(scen.kill_gen)] += scen.count

        stream.write("Failures\tOccurance\n")
        map(lambda x: stream.write("%d\t%d\n" % x), fail_count.items())
        stream.write("\n")
        stream.write("Result\tOccurance\n")
        map(lambda x: stream.write("%s\t%d\n" % x), result_count.items())
        stream.write("\n")
        stream.write("Bus\tOccurance\n")
        map(lambda x: stream.write("%d\t%d\n" % x), bus_count.items())
        stream.write("\n")
        stream.write("Line\tOccurance\n")
        map(lambda x: stream.write("%d\t%d\n" % x), line_count.items())
        stream.write("\n")
        stream.write("Gen\tOccurance\n")
        map(lambda x: stream.write("%d\t%d\n" % x), gen_count.items())
        stream.write("-"*80 + "\n")        
        

#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


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
        self.util_readwrite_match("""[name123] pf 436\n""")
        self.util_readwrite_match("""[name123] opf 243\n""")
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
            """[name123] pf 7
  set all demand 0.86
  result fail
""")


class Test_add(ModifiedTestCase):

    def test_001(self):
        sb = SimulationBatch()

        a = Scenario("a")
        a.kill_bus.append(12)
        sb.add(a)
      
        b = Scenario("b")
        b.kill_bus.append(12)
        sb.add(b)
      
        self.assertEqual(len(sb), 1)
        self.assertEqual(sb.size(), 2)
      
    def test_002(self):
        sb = SimulationBatch()

        a = Scenario("a")
        a.kill_bus.append(12)
        sb.add(a)
      
        b = Scenario("b")
        b.kill_bus.append(13)
        sb.add(b)
      
        self.assertEqual(len(sb), 2)
        self.assertEqual(sb.size(), 2)
      
    def test_003(self):
        sb = SimulationBatch()

        a = Scenario("a")
        a.kill_bus.append(12)
        sb.add(a)
      
        c = Scenario("c")
        c.kill_bus.append(12)
        sb.add(c)

        b = Scenario("b")
        b.kill_bus.append(13)
        sb.add(b)

        d = Scenario("d")
        d.kill_bus.append(12)
        sb.add(d)
      
        self.assertEqual(len(sb), 2)
        self.assertEqual(sb.size(), 4)
      
    def test_004(self):
        sb = SimulationBatch()

        a = Scenario("a", "pf")
        a.kill_bus.append(12)
        sb.add(a)
      
        b = Scenario("b", "opf")
        b.kill_bus.append(12)
        sb.add(b)
      
        self.assertEqual(len(sb), 2)
        self.assertEqual(sb.size(), 2)
      
    def test_005(self):
        sb = SimulationBatch()

        a = Scenario("a", "pf", 23)
        a.kill_bus.append(12)
        sb.add(a)
      
        b = Scenario("b", "pf", 100)
        b.kill_bus.append(12)
        sb.add(b)
      
        self.assertEqual(len(sb), 1)
        self.assertEqual(sb.size(), 123)
        


#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


if __name__ == '__main__':
    unittest.main()


#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------

