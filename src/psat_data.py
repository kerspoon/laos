#! /usr/local/bin/python
# psat_data.py - PsatData - psat_file - psat

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
psat_data.py - PsatData - psat_file - psat
"""

#==============================================================================
#  Imports:
#==============================================================================

from misc import struct, read_struct, as_csv, duplicates_exist, EnsureEqual, \
    Ensure, EnsureNotEqual, EnsureIn, Error
import re
import unittest
from StringIO import StringIO
from modifiedtestcase import ModifiedTestCase

#==============================================================================
#
#==============================================================================


def write_section(stream, items, title):
    """write one section of a Matlab file"""

    if len(items) == 0:
        return

    stream.write(title + ".con = [ ... \n")
    for _, value in sorted(items.items()):
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

    for _, line in enumerate(stream):
        line = line.strip()

        # check if we are done 
        if re.match("\A *\] *; *\Z", line): # if line == "];"
            break

        # skip comments
        if len(line) == 0 or line.startswith("%"):
            continue

        # everything should be lowercase, we don't care about the ';'
        cols = [x.lower() for x in line.replace(";", " ").split()]

        # strip comment delimiter from component ID
        # e.g. change '%a1' to 'a1' if it exists
        if cols[-1].startswith("%"):
            cols[-1] = cols[-1][1:]

        items.append(read_struct(classtype, cols))

    return items

#==============================================================================
#
#==============================================================================


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
            return line.startswith(title)
     
        def read_as_cid(storage, classtype):
            EnsureEqual(len(storage), 0)
            for item in read_section(stream, classtype):
                storage[item.cid] = item
            Ensure(len(storage) >= 0, "failed to read any items")
     
        def read_as_bus_no(storage, classtype):
            EnsureEqual(len(storage), 0)
            for item in read_section(stream, classtype):
                storage[item.bus_no] = item
            Ensure(len(storage) >= 0, "failed to read any items")
            
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
            elif title_matches(line, "Demand.con"):
                read_as_bus_no(self.demand, self.Demand)
            else:
                raise Error("expected matlab section, got '" + line + "'")

        self.invariant()

    def invariant(self):
        passed = self.in_limits()

        if duplicates_exist(gen.bus_no for gen in self.generators.values()):
            print "PsatData invariant: only one bus per generator"
            passed = False

        # we could also make sure that the key and cid/bus_no match.
        return passed
    
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

        # TODO: really should be an 'assert' not an 'if' but make testing easier
        if len(self.slack) == 1:
            slack = self.slack.values()[0]
            EnsureNotEqual(slack.bus_no, bus_no)
        else:
            print "Expected one slack got %d" % len(self.slack)
 

        EnsureEqual(self.busses[bus_no].bus_no, bus_no)
        del self.busses[bus_no]

        # as we now have virtal busses that connect to generators
        # we need to find and delete any of those hat connect to
        # this bus. 
        # We can find them by using the cid of the lines
        # find all lines with who's cid starts with "C" that 
        # connect to this bus

        for line in self.lines.values():
            if line.fbus == bus_no:
                self.remove_line(line.cid)
                if line.cid.startswith("c"):
                    self.remove_bus(line.tbus)
            elif line.tbus == bus_no:
                self.remove_line(line.cid)
                if line.cid.startswith("c"):
                    self.remove_bus(line.fbus)

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

        for idx, gen in self.generators.items():
            if gen.bus_no == bus_no:
                self.mismatch -= gen.p
                del self.generators[idx]

        for idx, load in self.loads.items():
            if load.bus_no == bus_no:
                self.mismatch += load.p
                del self.loads[idx]


    def remove_line(self, line_id):
        del self.lines[line_id]
        # TODO:: deal with islanding

    def remove_generator(self, supply_id):
        """kill the specified supply and corresponding generator
           with the requiement that there is only one generator
           per busbar.
           Could kill the line and busbar as well in most cases.
           But where there was only one gen on a bus anyway it 
           doesn't have a virtual bus hence might have a load.
        """

        bus_no = self.supply[supply_id].bus_no


        # really just for testing (my god that is poor style)
        if len(self.slack) == 0:
            Ensure(bus_no in self.generators, "missing generator info (%s)" % bus_no)
            self.mismatch -= self.generators[bus_no].p 
            del self.generators[bus_no]
            del self.supply[supply_id]
            return 
        
        EnsureEqual(len(self.slack), 1)
        slack = self.slack.values()[0]

        if slack.bus_no == bus_no:
            
            # todo: lets just hope that's accurate, it's probably not.
            self.mismatch -= slack.p_guess 

            # del self.generators[bus_no] 
            # we are not doing this because we instead change the slack to the
            # new value from the chosen bus. 
            
            # we do want to remove this. 
            del self.supply[supply_id]

            allowed_slacks = [37, 38]
            gen = None 
            for x in allowed_slacks:
                if x in self.generators:
                    # print "deleting slack bus: new slack =", x
                    EnsureEqual(self.generators[x].bus_no, x, "%s, %s" % (self.generators[x].bus_no, x))
                    gen = self.generators[x]
                    break
            Ensure(gen, "no slack bus")

            slack.bus_no = gen.bus_no
            slack.s_rating = gen.s_rating
            slack.v_rating = gen.v_rating
            slack.v_magnitude = gen.v
            slack.ref_angle = 0.0
            slack.q_max = gen.q_max
            slack.q_min = gen.q_min
            slack.v_max = gen.v_max
            slack.v_min = gen.v_min
            slack.p_guess = gen.p
            slack.lp_coeff = gen.lp_coeff
            slack.ref_bus = 1.0
            slack.status = gen.status
            del self.generators[gen.bus_no]
        else:
            EnsureIn(bus_no, self.generators, "missing generator info")
            self.mismatch -= self.generators[bus_no].p 
            del self.generators[bus_no]
            del self.supply[supply_id]

    def set_all_demand(self, value):
        # Note:: should I change P, Q or both.

        # this doesn't really do much other than check the data type
        # we need it that high for testing but the system wont work
        # with value above 1.08 currently 
        Ensure(0 < value <= 4, "just a vague sanity check")

        for load in self.loads.values():
            newval = load.p * value
            self.mismatch += load.p - newval
            load.p = newval
            self.demand[load.bus_no].p_bid_max = newval
            self.demand[load.bus_no].p_bid_min = newval
            
    def get_stats(self):
        
        scheduleable_generators = self.generators.values()
        min_limit = []
        max_limit = []
        for gen in scheduleable_generators:
            min_limit.append(sum(supply.p_bid_min for supply in 
                              self.supply.values() 
                              if supply.bus_no == gen.bus_no))
            max_limit.append(sum(supply.p_bid_max for supply in 
                              self.supply.values() 
                              if supply.bus_no == gen.bus_no))

        for slack in self.slack.values():
            min_limit.append(sum(supply.p_bid_min for supply in 
                              self.supply.values() 
                              if supply.bus_no == slack.bus_no))
            max_limit.append(sum(supply.p_bid_max for supply in 
                              self.supply.values() 
                              if supply.bus_no == slack.bus_no))
                
        gpowers = [gen.p for gen in scheduleable_generators] + [slack.p_guess for slack in self.slack.values()]
        lpowers = [load.p for load in self.loads.values()]
        
        return (self.mismatch, sum(gpowers), sum(lpowers), sum(min_limit), sum(max_limit))
        # return "mis= %f gen= %f load= %f lim ( %f < X < %f )"

    def fix_mismatch(self):
        """
        Changes the generators power to compensate for the imbalance caused 
        by remove_* or set_*. It sets each generator proportionally based 
        upon it's current generating power (though it respects generator 
        limits). We then need to check limits, though if the algorithm is
        working we shouldn't need to.

        It does this by using `self.mismatch`
        TODO: Not sure what to do with reactive power
        TODO: make this only count scheduleable generators i.e. not wind farms
        """
        

        if self.mismatch != 0:
    
            scheduleable_generators = self.generators.values()
        
            gpowers = [gen.p for gen in scheduleable_generators] + [slack.p_guess for slack in self.slack.values()]
            
            min_limit = []
            max_limit = []
            for gen in scheduleable_generators:
                min_limit.append(sum(supply.p_bid_min for supply in 
                                  self.supply.values() 
                                  if supply.bus_no == gen.bus_no))
                max_limit.append(sum(supply.p_bid_max for supply in 
                                  self.supply.values() 
                                  if supply.bus_no == gen.bus_no))
                

            for slack in self.slack.values():
                min_limit.append(sum(supply.p_bid_min for supply in 
                                  self.supply.values() 
                                  if supply.bus_no == slack.bus_no))
                max_limit.append(sum(supply.p_bid_max for supply in 
                                  self.supply.values() 
                                  if supply.bus_no == slack.bus_no))
    
            #print "-----"
            #print "t %f => %f < %f < %f" % (self.mismatch, sum(min_limit), sum(powers), sum(max_limit))
            #for pmin,power,pmax in zip(min_limit, powers, max_limit):
            #    print "p %f < %f < %f" % (pmin,power,pmax)
            #print "-----"
             
    
            # check nothing starts out of limits 
            gnames = [gen.bus_no for gen in scheduleable_generators] + [slack.bus_no for slack in self.slack.values()]
            
            for idx in range(len(gpowers)):
                if not(min_limit[idx] <= gpowers[idx] <= max_limit[idx]):

                    print "Power (#%d - bus(%d)) started out of limit (%f<=%f<=%f)" % (
                        idx,
                        gnames[idx],
                        min_limit[idx],
                        gpowers[idx],
                        max_limit[idx])

            res = fix_mismatch(-self.mismatch, gpowers, min_limit, max_limit)
    
            for newp, generator in zip(res, scheduleable_generators):
                generator.p = newp

        Ensure(self.in_limits(), "fixing mismatch should leave it in limit")
    
    def in_limits(self):
        """
        Checks that generator power is between the sum of all supply min and
        max bid. Checks that slack and generator voltage is within 
        limit. 
        requires all min bid to be <= 0 and all max bid to be >= 0.
        """

        inlimit = True
        for generator in self.generators.values():
            bus_no = generator.bus_no
            supplies = [s for s in self.supply.values() if s.bus_no == bus_no]
            # assert len(supplies) > 1 # often true but not needed.
            max_bid = sum(s.p_bid_max for s in supplies)
            min_bid = sum(s.p_bid_min for s in supplies)

            if not (generator.p == 0 or min_bid <= generator.p <= max_bid):
                print "generator", bus_no , "power limit:",
                print min_bid, "<=", generator.p, "<=", max_bid
                inlimit = False

            if not(generator.v_min <= generator.v <= generator.v_max):
                print "generator", bus_no, "volt limit:",
                print generator.v_min, "<=", generator.v, "<=", generator.v_max
                inlimit = False

        for slack in self.slack.values():
            if not(slack.v_min <= slack.v_magnitude <= slack.v_max):
                print "slack", slack.bus_no, "volt limit:",
                print slack.v_min, "<=", slack.v_magnitude, "<=", slack.v_max
                inlimit = False

        return inlimit

#==============================================================================
#
#==============================================================================


def fix_mismatch(mismatch, power, min_limit, max_limit):
    """
    func fix_mismatch :: Real, [Real], [Real], [Real] -> [Real]
    
    change the total generated power by `mismatch`.
    Do this based upon current power of each generator
    taking into account its limits.
    Returns a list of new generator powers
    """

    EnsureEqual(len(power), len(min_limit))
    EnsureEqual(len(power), len(max_limit))

    if mismatch == 0:
        return power
    
    done = [False for _ in range(len(power))]
    result = [0.0 for _ in range(len(power))]
     
    def find_limit_max(m):
        """find the index of the first generator that will
        be limited. or None """
        for n in range(len(done)):
            if (not done[n]) and (power[n] * m > max_limit[n]):
                return n
        return None
     
    def find_limit_min(m):
        """find the index of the first generator that will
        be limited. or None """
        for n in range(len(done)):
            if (not done[n]) and (power[n] * m < min_limit[n]):
                return n
        return None

    Ensure(sum(min_limit) < sum(power) + mismatch < sum(max_limit),
           "mismatch of %f is outside limits (%f < %f < %f)" % (mismatch, sum(min_limit), sum(power) + mismatch , sum(max_limit)))

    # print "mismatch\t%f" % mismatch
    # print "total gen\t%f" % sum(power)
    # print "total min gen\t%f" % sum(min_limit)
    # print "total max gen\t%f" % sum(max_limit)
    # print "-"*10
    # print "power\t%s" % as_csv(power,"\t")
    # print "min_limit\t%s" % as_csv(min_limit,"\t")
    # print "max_limit\t%s" % as_csv(max_limit,"\t")
    # if mismatch > 0:
    #     print as_csv([b-a for a,b in zip(power, max_limit)], "\t")
    #     print sum(max_limit) - sum(power)
    # else:
    #     print as_csv([b-a for a,b in zip(power, min_limit)], "\t")
    #     print sum(power) - sum(min_limit)
        

    # deal with each generator that will be limited
    while True:
        Ensure(not all(done), "programmer error")

        # print "fix_mismatch", len([1 for x in done if x])

        total_gen = sum(power[i] for i in range(len(done)) if not done[i])
        EnsureNotEqual(total_gen, 0)
        
        multiplier = 1.0 + (mismatch / total_gen)

        # we shouldn't really care about the miltiplier as long as 
        # the limits are being met should we?
        Ensure(0 <= multiplier <= 5, "vague sanity check")

        if mismatch < 0:
            idx_gen = find_limit_min(multiplier)
            if idx_gen is None:
                break

            # print "generator hit min limit:", idx_gen
            result[idx_gen] = min_limit[idx_gen]
            mismatch -= result[idx_gen] - power[idx_gen]
            done[idx_gen] = True
        else:
            idx_gen = find_limit_max(multiplier)
            if idx_gen is None:
                break

            # print "generator hit max limit:", idx_gen
            result[idx_gen] = max_limit[idx_gen]
            mismatch -= result[idx_gen] - power[idx_gen]
            done[idx_gen] = True

    # deal with all the other generators 
    # knowing that none of them will limit
    for idx in range(len(power)):
        if not done[idx]:
            # print "set generator", idx
            result[idx] = power[idx] * multiplier
            mismatch -= result[idx] - power[idx]
            done[idx] = True
  
    # check nothing is out of limits 
    for idx in range(len(power)):
        Ensure(power[idx] == 0 or (min_limit[idx] <= power[idx] <= max_limit[idx]),
               "Power (%d) out of limit (%f<=%f<=%f)" % (idx,
                                                         min_limit[idx],
                                                         power[idx],
                                                         max_limit[idx]))
    Ensure(mismatch < 0.001, "should be much mismatch left after fixing it")
    Ensure(all(done), "should have fixed everything")
    
    return result


#==============================================================================
#
#==============================================================================


class Test_fix_mismatch(ModifiedTestCase):

    def test_1(self):
        p_list = [1, 1, 1, 1, 1]
        max_list = [2, 2, 2, 2, 2]
        min_list = [-2, -2, -2, -2, -2]

        res = fix_mismatch(0, p_list, min_list, max_list)
        self.assertAlmostEqualList(res, p_list)
      
    def test_2(self):
        p_list = [1, 1]
        max_list = [2, 2]
        min_list = [-2, -2]

        res = fix_mismatch(1.0, p_list, min_list, max_list)
        self.assertAlmostEqualList(res, [1.5, 1.5])

    def test_3(self):
        p_list = [1, 0, 1]
        max_list = [2, 2, 2]
        min_list = [-2, -2, -2]
        res = fix_mismatch(1.0, p_list, min_list, max_list)
        self.assertAlmostEqualList(res, [1.5, 0, 1.5])

    def test_4(self):
        p_list = [2, 4]
        max_list = [8, 8]
        min_list = [-8, -8]
        res = fix_mismatch(3.0, p_list, min_list, max_list)
        self.assertAlmostEqualList(res, [3, 6])

    def test_5(self):
        p_list = [2, 4]
        max_list = [8, 5]
        min_list = [-8, -5]
        res = fix_mismatch(3.0, p_list, min_list, max_list)
        self.assertAlmostEqualList(res, [4, 5])

    def test_6(self):
        p_list = [1, 1]
        max_list = [2, 2]
        min_list = [-2, -2]

        res = fix_mismatch(-1.0, p_list, min_list, max_list)
        self.assertAlmostEqualList(res, [0.5, 0.5])

    def test_7(self):
        p_list = [1, 0, 1]
        max_list = [2, 2, 2]
        min_list = [-2, -2, -2]
        res = fix_mismatch(-1.0, p_list, min_list, max_list)
        self.assertAlmostEqualList(res, [0.5, 0, 0.5])

    def test_8(self):
        p_list = [2, 4]
        max_list = [8, 8]
        min_list = [-8, -8]
        res = fix_mismatch(-3.0, p_list, min_list, max_list)
        self.assertAlmostEqualList(res, [1, 2])

    def test_9(self):
        p_list = [2, 4]
        max_list = [8, 5]
        min_list = [-1, 3]
        res = fix_mismatch(-3.0, p_list, min_list, max_list)
        self.assertAlmostEqualList(res, [0, 3])



#==============================================================================
#
#==============================================================================


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


#==============================================================================
#
#==============================================================================


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


#==============================================================================
#
#==============================================================================


class Test_kill_generator(ModifiedTestCase):

    def setUp(self):
        self.pd = PsatData()
        self.stream = StringIO("""Supply.con = [ ... 
 25 100 0.81 1.0 0.0 0 1.72 24.8415 0.36505 0 0 0 0 0 1 0.1 0 0 0 1; %g1
 26 100 0.72 1.0 0.0 0 1.72 24.8415 0.36505 0 0 0 0 0 1 0.1 0 0 0 1; %g2
 27 100 0.63 1.0 0.0 0 3.5 10.2386 0.038404 0 0 0 0 0 1 0.3 -0.25 0 0 1; %g3
 28 100 0.54 1.0 0.0 0 3.5 10.2386 0.038404 0 0 0 0 0 1 0.3 -0.25 0 0 1; %g4
 29 100 0.45 1.0 0.0 0 1.72 24.8415 0.36505 0 0 0 0 0 1 0.1 0 0 0 1; %g5
 30 100 0.36 1.0 0.0 0 1.72 24.8415 0.36505 0 0 0 0 0 1 0.1 0 0 0 1; %g6
 31 100 0.27 1.0 0.0 0 3.5 10.2386 0.038404 0 0 0 0 0 1 0.3 -0.25 0 0 1; %g7
 32 100 0.18 1.0 0.0 0 3.5 10.2386 0.038404 0 0 0 0 0 1 0.3 -0.25 0 0 1; %g8
];

PV.con = [ ... 
 % ------------------- Bus 1
 25  100  138  0.81  1.035 0.10  0    1.05  0.95  1  1;
 26  100  138  0.72  1.035 0.10  0    1.05  0.95  1  1;
 27  100  138  0.63  1.035 0.30 -0.25 1.05  0.95  1  1;
 28  100  138  0.54  1.035 0.30 -0.25 1.05  0.95  1  1;
 % ------------------- Bus 2
 29  100  138  0.45  1.035 0.10  0    1.05  0.95  1  1;
 30  100  138  0.36  1.035 0.10  0    1.05  0.95  1  1;
 31  100  138  0.27  1.035 0.30 -0.25 1.05  0.95  1  1;
 32  100  138  0.18  1.035 0.30 -0.25 1.05  0.95  1  1;
];""")
        self.pd.read(self.stream)

    def test_remove_none(self):
        self.assertEqual(
            set([25, 26, 27, 28, 29, 30, 31, 32]),
            set(self.pd.generators))
        self.assertEqual(
            set("g1 g2 g3 g4 g5 g6 g7 g8".split()),
            set(self.pd.supply))


    def test_remove_first(self):
        self.pd.remove_generator("g1")
        self.assertEqual(
            set([26, 27, 28, 29, 30, 31, 32]),
            set(self.pd.generators))
        self.assertEqual(
            set("g2 g3 g4 g5 g6 g7 g8".split()),
            set(self.pd.supply))

    def test_remove_last(self):
        self.pd.remove_generator("g8")
        self.assertEqual(
            set([25, 26, 27, 28, 29, 30, 31]),
            set(self.pd.generators))
        self.assertEqual(
            set("g1 g2 g3 g4 g5 g6 g7".split()),
            set(self.pd.supply))

    def test_remove_middle(self):
        self.pd.remove_generator("g5")
        self.assertEqual(
            set([25, 26, 27, 28, 30, 31, 32]),
            set(self.pd.generators))
        self.assertEqual(
            set("g1 g2 g3 g4 g6 g7 g8".split()),
            set(self.pd.supply))

    def test_remove_double(self):
        self.pd.remove_generator("g2")
        self.pd.remove_generator("g3")
        self.assertEqual(
            set([25, 28, 29, 30, 31, 32]),
            set(self.pd.generators))
        self.assertEqual(
            set("g1 g4 g5 g6 g7 g8".split()),
            set(self.pd.supply))


#==============================================================================
#
#==============================================================================


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


#==============================================================================
#
#==============================================================================


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
  1 100 138 0.0 1.035 0.8 -0.5 1.05 0.95 1.0 1;
  2 100 138 0.0 1.035 0.8 -0.5 1.05 0.95 1.0 1;
  7 100 138 0.0 1.025 1.8 0.0 1.05 0.95 1.0 1;
];

""")
        pd.read(istream)
        ostream = StringIO()
        pd.write(ostream)
        self.assertEqual(istream.getvalue(), ostream.getvalue())


#==============================================================================
#
#==============================================================================


class Test_set_all_demand(ModifiedTestCase):

    def setUp(self):
        self.pd = PsatData()
        istream = StringIO("""PQ.con = [ ... 
  1   100  138  1.00  0.10  1.05  0.95  1  1;
  2   100  138  1.00  0.10  1.05  0.95  1  1;
  3   100  138  1.00  0.10  1.05  0.95  1  1;
  4   100  138  1.00  0.10  1.05  0.95  1  1;
  5   100  138  1.00  0.10  1.05  0.95  1  1;
  6   100  138  1.00  0.10  1.05  0.95  1  1;
 ];

Demand.con = [ ... 
   1  100  1.00  0.242  1.00 1.00  0  0  18  0  0  0  0  0  0  0  0  1;   
   2  100  1.00  0.22   1.00 1.00  0  0  25  0  0  0  0  0  0  0  0  1;   
   3  100  1.00  0.407  1.00 1.00  0  0  19  0  0  0  0  0  0  0  0  1;   
   4  100  1.00  0.165  1.00 1.00  0  0  24  0  0  0  0  0  0  0  0  1;   
   5  100  1.00  0.154  1.00 1.00  0  0  22  0  0  0  0  0  0  0  0  1;   
   6  100  1.00  0.308  1.00 1.00  0  0  19  0  0  0  0  0  0  0  0  1;   
 ];
""")
        self.pd.read(istream)
        self.assertEqual(self.pd.mismatch, 0)

    def test_one(self):
        self.pd.set_all_demand(1)
        self.assertAlmostEqual(self.pd.mismatch, 0)

    def test_two(self):
        self.pd.set_all_demand(2)
        self.assertAlmostEqual(self.pd.mismatch, -6)
        
    def test_four(self):
        self.pd.set_all_demand(4)
        self.assertAlmostEqual(self.pd.mismatch, -18)
        
    def test_half(self):
        self.pd.set_all_demand(0.5)
        self.assertAlmostEqual(self.pd.mismatch, 3)

    def test_0_9(self):
        self.pd.set_all_demand(0.9)
        self.assertAlmostEqual(self.pd.mismatch, 0.6)

    def test_0_1(self):
        self.pd.set_all_demand(0.1)
        self.assertAlmostEqual(self.pd.mismatch, 5.4)


#==============================================================================
#
#==============================================================================


if __name__ == '__main__':
    unittest.main()
