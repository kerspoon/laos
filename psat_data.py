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

#------------------------------------------------------------------------------
#
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
        self.busses = []
        self.lines = []
        self.slack = []
        self.generators = []
        self.loads = []
        self.shunts = []
        self.demand = []
        self.supply = []

    def read(self, stream):

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
            print "Unable to find bus:", bus_no
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
            print "todo: deal with deleting slack bus"

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
            print "Unable to find item:", bus_no

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

    def set_all_demand(self, value):
        for load in self.loads:
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


#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------

