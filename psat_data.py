#! /usr/local/bin/python
# psat_data.py - PsatData - psat_file - psat

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
psat_data.py - PsatData - psat_file - psat
"""

#------------------------------------------------------------------------------
#  Imports:
#------------------------------------------------------------------------------

from misc import struct, read_struct, as_csv
import re
import unittest
from StringIO import StringIO
from modifiedtestcase import ModifiedTestCase

#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


def write_section(stream, items, title):
    """write one section of a Matlab file"""

    if len(items) == 0:
        return

    stream.write(title + ".con = [ ... \n")
    for key, value in sorted(items.items()):
        if "cid" == value.entries[-1]:
            tmp = as_csv([value.__dict__[x] for x in value.entries[:-1]], " ")
            stream.write("  " + tmp + "; %" + value.cid + "\n")
        else:
            stream.write("  " + str(value) + ";\n")
    stream.write("];\n\n")


def read_section(stream, classtype):
    """read one section of Matlab file, assuming the header is done.
       and assuming that each line is one row ended by a semicolon. 
       In addition to the matlab spec a compoent can have an ID specified 
       by adding %XX to the end of its line where XX is the id. 
    """

    items = []

    for n,line in enumerate(stream):
        line = line.strip()

        # check if we are done 
        if re.match("\A *\] *; *\Z", line): # if line == "];"
            break

        # skip comments
        if len(line) == 0 or line.startswith("%"):
            continue

        # everything should be lowercase, we don't care about the ';'
        cols = [x.lower() for x in line.replace(";"," ").split()]

        # strip comment delimiter from component ID
        # e.g. change '%a1' to 'a1' if it exists
        if cols[-1].startswith("%"):
            cols[-1] = cols[-1][1:]

        items.append(read_struct(classtype, cols))

    return items

#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


class PsatData(object):
    """matlab psat data file"""
 
    class Bus(struct):
        entries = "bus_no v_base v_magnitude_guess v_angle_guess area region".split()
        types = "int int real real int int".split()
 
    class Line(struct):
        entries = "fbus tbus s_rating v_rating f_rating length v_ratio r x b tap shift i_limit p_limit s_limit status cid".split()
        types = "int int int int int real real real real real real real real real real int str".split()
 
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
        entries = "bus_no s_rating p_direction p_bid_max p_bid_min p_bid_actual p_fixed p_proportional p_quadratic q_fixed q_proportional q_quadratic commitment cost_tie_break lp_factor q_max q_min cost_cong_up cost_cong_down status cid".split()
        types = "int int real real real real real real real real real real real real real real real real real int str".split()

    def __init__(self):
        self.busses = {}
        self.lines = {}
        self.slack = {}
        self.generators = {}
        self.loads = {}
        self.shunts = {}
        self.demand = {}
        self.supply = {}
        self.mismatch = 0.0

    def read(self, stream):
     
        def title_matches(line, title):
            #todo: replace with regexp
            return line.startswith(title)
     
        def read_as_cid(storage, classtype):
            assert len(storage) == 0
            for item in read_section(stream, classtype):
                storage[item.cid] = item
            assert len(storage) >= 0
     
        def read_as_bus_no(storage, classtype):
            assert len(storage) == 0
            for item in read_section(stream, classtype):
                storage[item.bus_no] = item
            assert len(storage) >= 0
            
        for line in stream:
            line = line.strip()
     
            if len(line) == 0 or line.startswith("%"):
                continue
            elif title_matches(line, "Bus.con"):
                read_as_bus_no(self.busses, self.Bus)
            elif title_matches(line, "Line.con"):
                read_as_cid(self.lines, self.Line)
            elif title_matches(line, "SW.con"):
                read_as_bus_no(self.slack, self.Slack)
            elif title_matches(line, "PV.con"):
                read_as_bus_no(self.generators, self.Generator)
            elif title_matches(line, "PQ.con"):
                read_as_bus_no(self.loads, self.Load)
            elif title_matches(line, "Shunt.con"):
                read_as_bus_no(self.shunts, self.Shunt)
            elif title_matches(line, "Supply.con"):
                read_as_cid(self.supply, self.Supply)
            else:
                raise Exception("expected matlab section, got '" + line + "'")
            
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

        assert self.busses[bus_no].bus_no == bus_no
        del self.busses[bus_no]

        # kill all connecting items
        for idx, shunt in self.shunts.items():
            if shunt.bus_no == bus_no:
                del self.shunts[idx]

        for idx, item in self.demand.items():
            if item.bus_no == bus_no:
                del self.demand[idx]

        for idx, item in self.supply.items():
            if item.bus_no == bus_no:
                del self.supply[idx]

        for idx, line in self.lines.items():
            if line.fbus == bus_no or line.tbus == bus_no:
                self.remove_line(idx)

        for idx, gen in self.generators.items():
            if gen.bus_no == bus_no:
                self.mismatch -= gen.p
                del self.generators[idx]

        for idx, load in self.loads.items():
            if load.bus_no == bus_no:
                self.mismatch += load.p
                del self.loads[idx]

        # really should be an 'assert' not an 'if' but make testing easier
        if len(self.slack) == 1:
            assert self.slack[0].bus_no != bus_no, "todo: deal with deleting slack bus"

    def remove_line(self, line_id):
        del self.lines[line_id]
        # TODO:: deal with islanding

    def remove_generator(self, supply_id):
        """kill the specified supply and reduce the corosponding 
           PV element (self.generators) by the correct amount"""

        bus_no = self.supply[supply_id].bus_no

        # TODO set-up mini pool system for deciding power of each gen 
        # for now assume they distributed power equally.
        num_units = len([x for x in self.supply.values() if x.bus_no == bus_no])
        assert num_units >= 1

        unit_power = self.generators[bus_no].p / num_units

        # if we remove the last gen on the bus, remember to delete it 
        if num_units == 1:
            del self.generators[bus_no]
        else:
            self.generators[bus_no].p -= unit_power

        del self.supply[supply_id]
        self.mismatch -= unit_power

    def set_all_demand(self, value):
        # todo: might need to set mismatch
        # todo: test
        for load in self.loads.values():
            # Note:: should I change P, Q or both. 
            load.p *= value

    def fix_mismatch(self):
        """
        Changes the generators power to compensate for the imbalance caused 
        by remove_* or set_*. It sets each generator proportionally based 
        upon it's current generating power (though it respects generator 
        limits). 

        It does this by using `self.mismatch`
        TODO: Not sure what to do with reactive power
        TODO: make this only count scheduleable generators
              i.e. not wind farms
        """

        if self.mismatch == 0:
            return

        res = fix_mismatch(
            self.mismatch, 
            [g.p for g in self.generators], 
            [g.s_rating for g in self.generators])

        for n in range(len(self.generators)):
            self.generators[n].p = res[n]


#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


def fix_mismatch(mismatch, gen_power, gen_limit):
    """
    func fix_mismatch :: Real, [Real], [Real] -> [Real]
    
    change the total generated power by `mismatch`.
    Do this based upon current power of each generator
    taking into account its limits.
    Returns a list of new generator powers

    """

    assert(len(gen_power) == len(gen_limit))

    if mismatch == 0:
        return gen_power

    done = [False for _ in range(len(gen_power))]
    result = [0.0 for _ in range(len(gen_power))]

    def find_limit(m):
        """find the index of the first generator that will
           be limited. or None """
        for n,(gp,gr) in enumerate(zip(gen_power,gen_limit)):
            if (not done[n]) and (gp * m > gr):
                    return n
        return None
  
    # deal with each generator that will be limited
    while True:
        assert(not all(done))
  
        total_gen = sum(gen_power[i] for i in range(len(done)) if not done[i])
        assert(total_gen != 0)
  
        multiplier = 1.0 + (mismatch / total_gen)
        assert(0 <= multiplier <= 2)
        # print "multiplier", multiplier
  
        idx_gen = find_limit(multiplier)
        if idx_gen is None:
            break
  
        # print "generator hit limit:", idx_gen
        result[idx_gen] = gen_limit[idx_gen]
        mismatch -= result[idx_gen] - gen_power[idx_gen]
        done[idx_gen] = True
  
    # deal with all the other generators 
    # knowing that none of them will limit
    for idx in range(len(gen_power)):
        if not done[idx]:
            # print "set generator", idx
            result[idx] = gen_power[idx] * multiplier
            mismatch -= result[idx] - gen_power[idx]
            done[idx] = True
  
    # check nothing is out of limits 
    for idx in range(len(gen_power)):
        assert(gen_power[idx] <= gen_limit[idx])
    assert mismatch < 0.001
    assert all(done)
    
    return result

#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


class Test_fix_mismatch(ModifiedTestCase):

    def test_1(self):
        p_list = [1, 1, 1, 1, 1]
        r_list = [2, 2, 2, 2, 2]

        res = fix_mismatch(0, p_list, r_list)
        self.assertAlmostEqualList(res, p_list)
      
    def test_2(self):
        p_list = [1, 1]
        r_list = [2, 2]
        res = fix_mismatch(1.0, p_list, r_list)
        self.assertAlmostEqualList(res, [1.5, 1.5])

    def test_3(self):
        p_list = [1, 0, 1]
        r_list = [2, 2, 2]
        res = fix_mismatch(1.0, p_list, r_list)
        self.assertAlmostEqualList(res, [1.5, 0, 1.5])

    def test_4(self):
        p_list = [2, 4]
        r_list = [8, 8]
        res = fix_mismatch(3.0, p_list, r_list)
        self.assertAlmostEqualList(res, [3, 6])

    def test_5(self):
        p_list = [2, 4]
        r_list = [8, 5]
        res = fix_mismatch(3.0, p_list, r_list)
        self.assertAlmostEqualList(res, [4, 5])


#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


class Test_kill_lines(ModifiedTestCase):

    def setUp(self):
        self.pd = PsatData()
        self.stream = StringIO("""Line.con = [ ... 
1 2 100 138 60 0.0 0.0 0.0026 0.0139 0.4611 0.0 0.0 1.93 0.0 2.0 1; %a1
1 3 100 138 60 0.0 0.0 0.0546 0.2112 0.0572 0.0 0.0 2.08 0.0 2.2 1; %a2
1 3 100 138 60 0.0 0.0 0.0268 0.1037 0.0281 0.0 0.0 2.08 0.0 2.2 1; %a3
1 5 100 138 60 0.0 0.0 0.0218 0.0845 0.0229 0.0 0.0 2.08 0.0 2.2 1; %a4
2 4 100 138 60 0.0 0.0 0.0328 0.1267 0.0343 0.0 0.0 2.08 0.0 2.2 1; %a5
];""")
        self.pd.read(self.stream)

    def test_remove_none(self):
        self.assertEqual(
            set("a1 a2 a3 a4 a5".split()), 
            set(self.pd.lines))

    def test_remove_first(self):
        self.pd.remove_line("a1")
        self.assertEqual(
            set("a2 a3 a4 a5".split()), 
            set(self.pd.lines))
        
    def test_remove_last(self):
        self.pd.remove_line("a5")
        self.assertEqual(
            set("a1 a2 a3 a4".split()), 
            set(self.pd.lines))

    def test_remove_middle(self):
        self.pd.remove_line("a3")
        self.assertEqual(
            set("a1 a2 a4 a5".split()), 
            set(self.pd.lines))

    def test_remove_double(self):
        self.pd.remove_line("a3")
        self.pd.remove_line("a4")
        self.assertEqual(
            set("a1 a2 a5".split()), 
            set(self.pd.lines))


#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


class Test_kill_bus(ModifiedTestCase):
    """note: doesn't check cascade killing"""

    def setUp(self):
        self.pd = PsatData()
        self.stream = StringIO("""Bus.con = [ ... 
1 138 1 0 2 1;
2 138 1 0 2 1;
3 138 1 0 2 1;
4 138 1 0 2 1;
];""")
        self.pd.read(self.stream)

    def test_remove_none(self):
        self.assertEqual(
            set([1, 2, 3, 4]),
            set(self.pd.busses))
        
    def test_remove_first(self):
        self.pd.remove_bus(1)
        self.assertEqual(
            set([2, 3, 4]),
            set(self.pd.busses))

    def test_remove_last(self):
        self.pd.remove_bus(4)
        self.assertEqual(
            set([1, 2, 3]),
            set(self.pd.busses))

    def test_remove_middle(self):
        self.pd.remove_bus(3)
        self.assertEqual(
            set([1, 2, 4]),
            set(self.pd.busses))

    def test_remove_double(self):
        self.pd.remove_bus(3)
        self.pd.remove_bus(2)
        self.assertEqual(
            set([1, 4]),
            set(self.pd.busses))


#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


class Test_kill_generator(ModifiedTestCase):

    def setUp(self):
        self.pd = PsatData()
        self.stream = StringIO("""Supply.con = [ ... 
 1 100 0.1 0.2 0.1 0 1.72 24.8415 0.36505 0 0 0 0 0 1 0.1 0 0 0 1; %g1 
 1 100 0.1 0.2 0.1 0 1.72 24.8415 0.36505 0 0 0 0 0 1 0.1 0 0 0 1; %g2 
 1 100 0.76 0.76 0.152 0 3.5 10.2386 0.038404 0 0 0 0 0 1 0.3 -0.25 0 0 1; %g3 
 1 100 0.76 0.76 0.152 0 3.5 10.2386 0.038404 0 0 0 0 0 1 0.3 -0.25 0 0 1; %g4 
 1 100 0.1 0.2 0.1 0 1.72 24.8415 0.36505 0 0 0 0 0 1 0.1 0 0 0 1; %g5 
 2 100 0.1 0.2 0.1 0 1.72 24.8415 0.36505 0 0 0 0 0 1 0.1 0 0 0 1; %g6 
 2 100 0.76 0.76 0.152 0 3.5 10.2386 0.038404 0 0 0 0 0 1 0.3 -0.25 0 0 1; %g7 
 2 100 0.76 0.76 0.152 0 3.5 10.2386 0.038404 0 0 0 0 0 1 0.3 -0.25 0 0 1; %g8 
 7 100 0.8 1 0.25 0 -0.65 17.9744 0.027484 0 0 0 0 0 1 0.6 0 0 0 1; %g9 
];

PV.con = [ ... 
 1 100 138 1.72 1.035 0.8 -0.5 1.05 0.95 1.0 1
 2 100 138 1.72 1.035 0.8 -0.5 1.05 0.95 1.0 1
 7 100 138 2.4 1.025 1.8 0.0 1.05 0.95 1.0 1
];""")
        self.pd.read(self.stream)

    def test_remove_none(self):
        self.assertEqual(
            set([1, 2, 7]),
            set(self.pd.generators))
        self.assertEqual(
            set("g1 g2 g3 g4 g5 g6 g7 g8 g9".split()),
            set(self.pd.supply))
        self.assertAlmostEqualList(
            [1.72, 1.72, 2.4],
            [item.p for item in self.pd.generators.values()])

    def test_remove_first(self):
        self.pd.remove_generator("g1")
        self.assertEqual(
            set([1, 2, 7]),
            set(self.pd.generators))
        self.assertEqual(
            set("g2 g3 g4 g5 g6 g7 g8 g9".split()),
            set(self.pd.supply))
        self.assertAlmostEqualList(
            [1.376, 1.72, 2.4],
            [item.p for item in self.pd.generators.values()])

    def test_remove_last(self):
        self.pd.remove_generator("g9")
        self.assertEqual(
            set([1, 2]),
            set(self.pd.generators))
        self.assertEqual(
            set("g1 g2 g3 g4 g5 g6 g7 g8".split()),
            set(self.pd.supply))
        self.assertAlmostEqualList(
            [1.72, 1.72],
            [item.p for item in self.pd.generators.values()])

    def test_remove_middle(self):
        self.pd.remove_generator("g7")
        self.assertEqual(
            set([1, 2, 7]),
            set(self.pd.generators))
        self.assertEqual(
            set("g1 g2 g3 g4 g5 g6 g8 g9".split()),
            set(self.pd.supply))
        self.assertAlmostEqualList(
            [1.72, 1.1466666667, 2.4],
            [item.p for item in self.pd.generators.values()])

    def test_remove_double(self):
        self.pd.remove_generator("g2")
        self.pd.remove_generator("g3")
        self.assertEqual(
            set([1, 2, 7]),
            set(self.pd.generators))
        self.assertEqual(
            set("g1 g4 g5 g6 g7 g8 g9".split()),
            set(self.pd.supply))
        self.assertAlmostEqualList(
            [1.032, 1.72, 2.4],
            [item.p for item in self.pd.generators.values()])


#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


class Test_kill_bus_cascade(ModifiedTestCase):

    def setUp(self):
        self.pd = PsatData()
        self.stream = StringIO("""Bus.con = [ ... 
1 138 1 0 2 1;
2 138 1 0 2 1;
3 138 1 0 2 1;
4 138 1 0 2 1;
];

Line.con = [ ... 
1 2 100 138 60 0.0 0.0 0.0026 0.0139 0.4611 0.0 0.0 1.93 0.0 2.0 1; %a1
1 3 100 138 60 0.0 0.0 0.0546 0.2112 0.0572 0.0 0.0 2.08 0.0 2.2 1; %a2
1 3 100 138 60 0.0 0.0 0.0268 0.1037 0.0281 0.0 0.0 2.08 0.0 2.2 1; %a3
2 4 100 138 60 0.0 0.0 0.0328 0.1267 0.0343 0.0 0.0 2.08 0.0 2.2 1; %a5
];

Supply.con = [ ... 
 1 100 0.1 0.2 0.1 0 1.72 24.8415 0.36505 0 0 0 0 0 1 0.1 0 0 0 1; %g1 
 1 100 0.1 0.2 0.1 0 1.72 24.8415 0.36505 0 0 0 0 0 1 0.1 0 0 0 1; %g2 
 1 100 0.76 0.76 0.152 0 3.5 10.2386 0.038404 0 0 0 0 0 1 0.3 -0.25 0 0 1; %g3
 1 100 0.76 0.76 0.152 0 3.5 10.2386 0.038404 0 0 0 0 0 1 0.3 -0.25 0 0 1; %g4
 1 100 0.1 0.2 0.1 0 1.72 24.8415 0.36505 0 0 0 0 0 1 0.1 0 0 0 1; %g5 
 2 100 0.1 0.2 0.1 0 1.72 24.8415 0.36505 0 0 0 0 0 1 0.1 0 0 0 1; %g6 
 2 100 0.76 0.76 0.152 0 3.5 10.2386 0.038404 0 0 0 0 0 1 0.3 -0.25 0 0 1; %g7
 2 100 0.76 0.76 0.152 0 3.5 10.2386 0.038404 0 0 0 0 0 1 0.3 -0.25 0 0 1; %g8
];

PV.con = [ ... 
 1 100 138 1.72 1.035 0.8 -0.5 1.05 0.95 1.0 1
 2 100 138 1.72 1.035 0.8 -0.5 1.05 0.95 1.0 1
];""")
        self.pd.read(self.stream)

    def test_remove_none(self):
        self.assertEqual(
            set([1, 2, 3, 4]),
            set(self.pd.busses))
        self.assertEqual(
            set("a1 a2 a3 a5".split()), 
            set(self.pd.lines))
        self.assertEqual(
            set("g1 g2 g3 g4 g5 g6 g7 g8".split()),
            set(self.pd.supply))
        self.assertEqual(
            set([1, 2]),
            set(self.pd.generators))

    def test_remove_first(self):
        self.pd.remove_bus(1)
        self.assertEqual(
            set([2, 3, 4]),
            set(self.pd.busses))
        self.assertEqual(
            set("a5".split()), 
            set(self.pd.lines))
        self.assertEqual(
            set("g6 g7 g8".split()),
            set(self.pd.supply))
        self.assertEqual(
            set([2]),
            set(self.pd.generators))

    def test_remove_last(self):
        self.pd.remove_bus(2)
        self.assertEqual(
            set([1, 3, 4]),
            set(self.pd.busses))
        self.assertEqual(
            set("a2 a3".split()), 
            set(self.pd.lines))
        self.assertEqual(
            set("g1 g2 g3 g4 g5".split()),
            set(self.pd.supply))
        self.assertEqual(
            set([1]),
            set(self.pd.generators))


#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


class Test_read_write(ModifiedTestCase):

    def test_basic(self):
        pd = PsatData()
        istream = StringIO("""Bus.con = [ ... 
  1 138 1.0 0.0 2 1;
  2 138 1.0 0.0 2 1;
  3 138 1.0 0.0 2 1;
  4 138 1.0 0.0 2 1;
];

Line.con = [ ... 
  1 2 100 138 60 0.0 0.0 0.0026 0.0139 0.4611 0.0 0.0 1.93 0.0 2.0 1; %a1
  1 3 100 138 60 0.0 0.0 0.0546 0.2112 0.0572 0.0 0.0 2.08 0.0 2.2 1; %a2
  1 3 100 138 60 0.0 0.0 0.0268 0.1037 0.0281 0.0 0.0 2.08 0.0 2.2 1; %a3
  2 4 100 138 60 0.0 0.0 0.0328 0.1267 0.0343 0.0 0.0 2.08 0.0 2.2 1; %a5
];

PV.con = [ ... 
  1 100 138 1.72 1.035 0.8 -0.5 1.05 0.95 1.0 1;
  2 100 138 1.72 1.035 0.8 -0.5 1.05 0.95 1.0 1;
  7 100 138 2.4 1.025 1.8 0.0 1.05 0.95 1.0 1;
];

""")
        pd.read(istream)
        ostream = StringIO()
        pd.write(ostream)
        self.assertEqual(istream.getvalue(), ostream.getvalue())

#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


if __name__ == '__main__':
    unittest.main()
