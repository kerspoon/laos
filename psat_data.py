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

from misc import struct, read_struct
import re
import unittest
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
        stream.write("  " + str(value) + ";\n")
    stream.write(" ];\n")


def read_section(stream, items, classtype):
    """read one section of Matlab file, assuming the header is done.
       and assuming that each line is one row ended by a semicolon. 
    """

    for n,line in enumerate(stream):
        line = line.strip()

        if re.match("\A *\] *; *\Z", line): # if line == "];"
            break

        if len(line) == 0 or line.startswith("#"):
            continue

        cols = [x.lower() for x in line.replace(";"," ").split()]
        items[n] = read_struct(classtype, cols)


#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


class PsatData(object):
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

        for line in stream:
            line = line.strip()

            if len(line) == 0 or line.startswith("#"):
                continue
            elif title_matches(line, "Bus.con"):
                assert len(self.busses) == 0

                # silly little hack to get busses[id].bus_no == id
                tmp = {}
                read_section(stream, tmp, self.Bus)
                for bus in tmp.values():
                    self.busses[bus.bus_no] = bus

                # make sure that hack worked
                assert len(self.busses) >= 1
                for idx,bus in self.busses.items():
                    assert bus.bus_no == idx, str(bus.bus_no) + " " + str(idx)
            elif title_matches(line, "Line.con"):
                assert len(self.lines) == 0
                read_section(stream, self.lines, self.Line)
                assert len(self.lines) >= 1
            elif title_matches(line, "SW.con"):
                assert len(self.slack) == 0
                read_section(stream, self.slack, self.Slack)
                assert len(self.slack) == 1
            elif title_matches(line, "PV.con"):
                assert len(self.generators) == 0
                read_section(stream, self.generators, self.Generator)
                assert len(self.generators) >= 0
            elif title_matches(line, "PQ.con"):
                assert len(self.loads) == 0
                read_section(stream, self.loads, self.Load)
                assert len(self.loads) >= 1
            elif title_matches(line, "Shunt.con"):
                assert len(self.shunts) == 0
                read_section(stream, self.shunts, self.Shunt)
                assert len(self.shunts) >= 0
            elif title_matches(line, "Demand.con"):
                assert len(self.demand) == 0
                read_section(stream, self.demand, self.Demand)
                assert len(self.demand) >= 0 
            elif title_matches(line, "Supply.con"):
                assert len(self.supply) == 0
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
                self.remove_line(idx, 
                                 line.fbus,
                                 line.tbus)

        for idx, gen in self.generators.items():
            if gen.bus_no == bus_no:
                self.mismatch -= gen.p
                del self.generators[idx]

        for idx, load in self.loads.items():
            if load.bus_no == bus_no:
                self.mismatch += load.p
                del self.loads[idx]

        assert len(self.slack) == 1
        assert self.slack[0].bus_no != bus_no, "todo: deal with deleting slack bus"

    def remove_line(self, line_id, fbus, tbus):
        assert self.lines[line_id].fbus == fbus
        assert self.lines[line_id].tbus == tbus
        del self.lines[line_id]
        # TODO:: deal with islanding

    def remove_generator(self, supply_id, bus_no=None):
        """kill the specified supply and reduce the corosponding 
           PV element (self.generators) by the correct amount"""
        
        if bus_no:
            assert self.supply[supply_id].bus_no == bus_no
        else:
            bus_no = self.supply[supply_id].bus_no

        gens = [n for n,x in enumerate(self.generators.values()) 
                    if x.bus_no == bus_no]
        assert len(gens) == 1
        gen_id = gens[0]

        # TODO set-up mini pool system for deciding power of each gen 
        # for now assume they distributed power equally.
        num_units = len([x for x in self.supply.values() if x.bus_no == bus_no])
        unit_power = self.generators[gen_id].p / num_units

        del self.supply[supply_id]
        self.mismatch -= unit_power
        self.generators[gen_id].p -= unit_power

    def set_all_demand(self, value):
        for load in self.loads.values():
            # Note:: should I change P, Q or both. 
            load.p *= value

#     def set_all_supply(self, value):
#         # can't set this simply it depends on the bid price.
#         raise Exception("not implemented")
#  
#     def set_demand(self, bus_no, value):
#         raise Exception("not implemented")
#  
#     def set_supply(self, bus_no, value):
#         # can't set this simply it depends on the bid price.
#         raise Exception("not implemented")

    def fix_mismatch(self):
        """
        change generator powers so that the mismatch is taking
        into account. Keep to limits. 

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
        self.lines = [
            "1 2 100 138 60 0.0 0.0 0.0026 0.0139 0.4611 0.0 0.0 1.93 0.0 2.0 1",
            "1 3 100 138 60 0.0 0.0 0.0546 0.2112 0.0572 0.0 0.0 2.08 0.0 2.2 1",
            "1 3 100 138 60 0.0 0.0 0.0268 0.1037 0.0281 0.0 0.0 2.08 0.0 2.2 1",
            "1 5 100 138 60 0.0 0.0 0.0218 0.0845 0.0229 0.0 0.0 2.08 0.0 2.2 1",
            "2 4 100 138 60 0.0 0.0 0.0328 0.1267 0.0343 0.0 0.0 2.08 0.0 2.2 1"]
        for n,line in enumerate(self.lines):
            self.pd.lines[n] = read_struct(PsatData.Line, line.split())
 
    def util_pprint(self, collection):
        return [str(value) for key, value in sorted(collection.items())]
        
    def test_1(self):
        self.pd.remove_line(0, 1, 2)
        self.assertEqual(
            self.util_pprint(self.pd.lines),
            self.lines[1:])

    def test_2(self):
        self.pd.remove_line(1, 1, 3)
        self.assertEqual(
            self.util_pprint(self.pd.lines),
            [self.lines[0]] + self.lines[2:])

    def test_3(self):
        self.pd.remove_line(2, 1, 3)
        self.assertEqual(
            self.util_pprint(self.pd.lines),
            self.lines[:2] + self.lines[3:])

    def test_4(self):
        self.pd.remove_line(2, 1, 3)
        self.pd.remove_line(4, 2, 4)
        self.assertEqual(
            self.util_pprint(self.pd.lines),
            self.lines[:2] + [self.lines[3]])


#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


class Test_kill_generator(ModifiedTestCase):

    def setUp(self):
        self.pd = PsatData()
        self.supply = [
            ("1 100 0.1 0.2 0.1 0.0 1.72 24.8415 0.36505 0.0 0.0 0.0 "
             "0.0 0.0 1.0 0.1 0.0 0.0 0.0 1"),
            ("1 100 0.1 0.2 0.1 0.0 1.72 24.8415 0.36505 0.0 0.0 0.0 "
             "0.0 0.0 1.0 0.1 0.0 0.0 0.0 1"),
            ("1 100 0.76 0.76 0.152 0.0 3.5 10.2386 0.038404 0.0 0.0 "
             "0.0 0.0 0.0 1.0 0.3 -0.25 0.0 0.0 1"),
            ("1 100 0.76 0.76 0.152 0.0 3.5 10.2386 0.038404 0.0 0.0 "
             "0.0 0.0 0.0 1.0 0.3 -0.25 0.0 0.0 1"),
            ("2 100 0.1 0.2 0.1 0.0 1.72 24.8415 0.36505 0.0 0.0 0.0 "
             "0.0 0.0 1.0 0.1 0.0 0.0 0.0 1"),
            ("2 100 0.1 0.2 0.1 0.0 1.72 24.8415 0.36505 0.0 0.0 0.0 "
             "0.0 0.0 1.0 0.1 0.0 0.0 0.0 1"),
            ("2 100 0.76 0.76 0.152 0.0 3.5 10.2386 0.038404 0.0 0.0 "
             "0.0 0.0 0.0 1.0 0.3 -0.25 0.0 0.0 1"),
            ("2 100 0.76 0.76 0.152 0.0 3.5 10.2386 0.038404 0.0 0.0 "
             "0.0 0.0 0.0 1.0 0.3 -0.25 0.0 0.0 1"),
            ("7 100 0.8 1.0 0.25 0.0 -0.65 17.9744 0.027484 0.0 0.0 0"
             ".0 0.0 0.0 1.0 0.6 0.0 0.0 0.0 1"),
            ("7 100 0.8 1.0 0.25 0.0 -0.65 17.9744 0.027484 0.0 0.0 0"
             ".0 0.0 0.0 1.0 0.6 0.0 0.0 0.0 1"),
            ("7 100 0.8 1.0 0.25 0.0 -0.65 17.9744 0.027484 0.0 0.0 0"
             ".0 0.0 0.0 1.0 0.6 0.0 0.0 0.0 1")]

        self.generators = [
            "1 100 138 1.72 1.035 0.8 -0.5 1.05 0.95 1.0 1",
            "2 100 138 1.72 1.035 0.8 -0.5 1.05 0.95 1.0 1",
            "7 100 138 2.4 1.025 1.8 0.0 1.05 0.95 1.0 1"]

        for n,item in enumerate(self.supply):
            self.pd.supply[n] = read_struct(PsatData.Supply, item.split())
 
        for n,item in enumerate(self.generators):
            self.pd.generators[n] = read_struct(PsatData.Generator, item.split())
 
    def util_pprint(self, collection):
        return [str(value) for key, value in sorted(collection.items())]
        
    def test_0(self):
        self.assertEqual(
            self.util_pprint(self.pd.supply),
            self.supply)
        self.assertEqual(
            self.util_pprint(self.pd.generators),
            self.generators)

    def test_1(self):
        self.pd.remove_generator(0, 1)
        self.assertEqual(
            self.util_pprint(self.pd.supply),
            self.supply[1:])
        self.assertEqual(
            self.util_pprint(self.pd.generators),
            ["1 100 138 1.29 1.035 0.8 -0.5 1.05 0.95 1.0 1"] + self.generators[1:])

    def test_2(self):
        self.pd.remove_generator(3, 1)
        self.assertEqual(
            self.util_pprint(self.pd.supply),
            self.supply[:3] + self.supply[4:])
        self.assertEqual(
            self.util_pprint(self.pd.generators),
            ["1 100 138 1.29 1.035 0.8 -0.5 1.05 0.95 1.0 1"] + self.generators[1:])

    def test_3(self):
        self.pd.remove_generator(3, 1)
        self.pd.remove_generator(4, 2)
        self.assertEqual(
            self.util_pprint(self.pd.supply),
            self.supply[:3] + self.supply[5:])
        self.assertEqual(
            self.util_pprint(self.pd.generators),
            ["1 100 138 1.29 1.035 0.8 -0.5 1.05 0.95 1.0 1",
             "2 100 138 1.29 1.035 0.8 -0.5 1.05 0.95 1.0 1"] + self.generators[2:])


#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


class Test_kill_bus(ModifiedTestCase):

    def util_pprint(self, collection):
        return [str(value) for key, value in sorted(collection.items())]
        
    def test_1(self):
        pd = PsatData()
        busses = [
            "1 138 1 0 2 1",
            "2 138 1 0 2 1",
            "3 138 1 0 2 1",
            "4 138 1 0 2 1"]

        for n, item in enumerate(busses):
            pd.busses[n+1] = read_struct(PsatData.Bus, item.split())

        pd.remove_bus(1)

        self.assertEqual(self.util_pprint(pd.generators), busses[1:])

    def test_2(self):
        pd = PsatData()
        busses = [
            "1 138 1 0 2 1",
            "2 138 1 0 2 1",
            "3 138 1 0 2 1",
            "4 138 1 0 2 1"]
        
        for n, item in enumerate(busses):
            pd.busses[n+1] = read_struct(PsatData.Bus, item.split())

        pd.remove_bus(2)

        self.assertEqual(self.util_pprint(pd.generators), [busses[0]] + busses[2:])


class Test_kill_bus2(ModifiedTestCase):

    def setUp(self):
        self.pd = PsatData()
        self.busses = [
            "1 138 1.0 0.0 2 1",
            "2 138 1.0 0.0 2 1",
            "3 138 1.0 0.0 2 1",
            "4 138 1.0 0.0 2 1"]
        self.lines = [
            "1 2 100 138 60 0.0 0.0 0.0026 0.0139 0.4611 0.0 0.0 1.93 0.0 2.0 1",
            "1 3 100 138 60 0.0 0.0 0.0546 0.2112 0.0572 0.0 0.0 2.08 0.0 2.2 1",
            "1 3 100 138 60 0.0 0.0 0.0268 0.1037 0.0281 0.0 0.0 2.08 0.0 2.2 1",
            "2 4 100 138 60 0.0 0.0 0.0328 0.1267 0.0343 0.0 0.0 2.08 0.0 2.2 1"]
        self.supply = [
            "1 100 0.1 0.2 0.1 0.0 1.72 24.8415 0.36505 0.0 0.0 0.0 0.0 0.0 1.0 0.1 0.0 0.0 0.0 1",
            "1 100 0.1 0.2 0.1 0.0 1.72 24.8415 0.36505 0.0 0.0 0.0 0.0 0.0 1.0 0.1 0.0 0.0 0.0 1",
            "1 100 0.76 0.76 0.152 0.0 3.5 10.2386 0.038404 0.0 0.0 0.0 0.0 0.0 1.0 0.3 -0.25 0.0 0.0 1",
            "1 100 0.76 0.76 0.152 0.0 3.5 10.2386 0.038404 0.0 0.0 0.0 0.0 0.0 1.0 0.3 -0.25 0.0 0.0 1",
            "2 100 0.1 0.2 0.1 0.0 1.72 24.8415 0.36505 0.0 0.0 0.0 0.0 0.0 1.0 0.1 0.0 0.0 0.0 1",
            "2 100 0.1 0.2 0.1 0.0 1.72 24.8415 0.36505 0.0 0.0 0.0 0.0 0.0 1.0 0.1 0.0 0.0 0.0 1",
            "2 100 0.76 0.76 0.152 0.0 3.5 10.2386 0.038404 0.0 0.0 0.0 0.0 0.0 1.0 0.3 -0.25 0.0 0.0 1",
            "2 100 0.76 0.76 0.152 0.0 3.5 10.2386 0.038404 0.0 0.0 0.0 0.0 0.0 1.0 0.3 -0.25 0.0 0.0 1"]
        self.generators = [
            "1 100 138 1.72 1.035 0.8 -0.5 1.05 0.95 1.0 1",
            "2 100 138 1.72 1.035 0.8 -0.5 1.05 0.95 1.0 1"]

        for n,item in enumerate(self.supply):
            self.pd.supply[n] = read_struct(PsatData.Supply, item.split())
 
        for n,item in enumerate(self.generators):
            self.pd.generators[n] = read_struct(PsatData.Generator, item.split())
 
        for n,item in enumerate(self.busses):
            self.pd.busses[n+1] = read_struct(PsatData.Bus, item.split())

        for n,line in enumerate(self.lines):
            self.pd.lines[n] = read_struct(PsatData.Line, line.split())

        self.pd.slack[0] = read_struct(
            PsatData.Slack,
            "13 100 230 1.02 0 2.4 0 1.05 0.95 4.7321 1 1 1".split())

    def util_pprint(self, collection):
        return [str(value) for key, value in sorted(collection.items())]
                
    def test_1(self):
        self.assertEqual(
            self.util_pprint(self.pd.busses),
            self.busses)
        self.assertEqual(
            self.util_pprint(self.pd.lines),
            self.lines)
        self.assertEqual(
            self.util_pprint(self.pd.supply),
            self.supply)
        self.assertEqual(
            self.util_pprint(self.pd.generators),
            self.generators)

    def test_2(self):
        self.pd.remove_bus(1)
        self.assertEqual(
            self.util_pprint(self.pd.busses),
            self.busses[1:])
        self.assertEqual(
            self.util_pprint(self.pd.lines),
            [self.lines[3]])
        self.assertEqual(
            self.util_pprint(self.pd.supply),
            self.supply[4:])
        self.assertEqual(
            self.util_pprint(self.pd.generators),
            self.generators[1:])

#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------


if __name__ == '__main__':
    unittest.main()

