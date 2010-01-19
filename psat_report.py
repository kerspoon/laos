#! /usr/local/bin/python
# parse a psat report
# psat_report.PSATreport.parse_stream(open("psat_outage0_01.txt"))

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

""" Package info:
James Brooks (kerspoon)

Read in a report from psat; check format & sanity check.
"""

#------------------------------------------------------------------------------
# Imports:
#------------------------------------------------------------------------------

from parsingutil import *
from decimal import Decimal
import logging
import sys
from copy import deepcopy

#------------------------------------------------------------------------------
# Logging:
#------------------------------------------------------------------------------

logger = logging.getLogger(__name__)

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
    format="%(levelname)s: %(message)s")

#------------------------------------------------------------------------------
# Util:
#------------------------------------------------------------------------------

def dec_check(val, vmin=Decimal("-1.0"), vmax=Decimal("1.0")):
    return Decimal(vmin) <= val <= Decimal(vmax)

def almost_equal(x, y):
    return abs(Decimal(x) - Decimal(y)) < Decimal("0.001")

busname = Literal("Bus").suppress() + integer

#------------------------------------------------------------------------------
# PSATreport:
#------------------------------------------------------------------------------

class PSATreport(object):
    """Matlab PSAT report file.
    """

    class PowerFlow(object):
        """Bus Bar power flow"""

        def __init__(self, name, v, phase, pg, qg, pl, ql):
            self.name = name
            self.v = v
            self.phase = phase
            self.pg = pg
            self.qg = qg
            self.pl = pl
            self.ql = ql

    class LineFlow(object):
        """line flow results
        """

        def __init__(self, fbus, tbus, line, pf, qf, pl, ql):
            self.fbus = fbus
            self.tbus = tbus
            self.line = line
            self.pf = pf
            self.qf = qf
            self.pl = pl
            self.ql = ql

    def __init__(self):
        self.num_bus = None
        self.num_line = None
        self.num_transformer = None
        self.num_generator = None
        self.num_load = None

        self.power_rate = None
        self.power_flow = []
        self.line_flow = []

        self.acceptable = True

    def parse_stream(self, stream):
        logger.debug("Parsing stream: %s" % stream)

        try:
            headers = self.GetHeaders()
            stats = self.GetStats()
            pflow = self.GetPflow()
            lineflow = self.GetLineflow()
            summary = self.GetSummary()
            limits = self.GetLimits()

            case = headers + stats + pflow + lineflow + summary + limits
            data = case.parseFile(stream)
            logger.debug("Done Parsing stream")
        except:
            logger.debug("PARSING ERROR")
            raise
        return self.acceptable

    def ensure(self, cond, text):
        if not cond:
            print "FAIL!!!\t", text
            self.acceptable = False

    def process_header_title(self, tokens):
        # print("Header : %s" % tokens)
        if len(tokens[0]) == 1:
            print "Power Flow"
        elif len(tokens[0]) == 2:
            print "Optimal Power Flow"
        else:
            raise Exception("%s" % tokens)

    def process_stats(self, tokens):
        # print("Stats : %s" % tokens)

        for x in "loads generators transformers lines buses".split():
            y = tokens[0][x]
            self.ensure(y > 0, "incorrect number of components, got " + str(y))

        self.ensure(1 <= tokens[1]["iterations"] <= 10000, "error : \n%s" % tokens)
        self.ensure(dec_check(tokens[1]["pmis"]), "error : \n%s" % tokens)
        self.ensure(dec_check(tokens[1]["qmis"]), "error : \n%s" % tokens)
        self.ensure(almost_equal("100", tokens[1]["rate"]), "error : \n%s" % tokens)

        self.num_load = tokens[0]["loads"]
        self.num_generator = tokens[0]["generators"]
        self.num_transformer = tokens[0]["transformers"]
        self.num_line = tokens[0]["lines"]
        self.num_bus = tokens[0]["buses"]
        self.power_rate = tokens[1]["rate"]

        # set length only (line flows are there and back)
        self.power_flow = [None for _ in range(self.num_bus)]
        self.line_flow = [None for _ in range(self.num_line * 2)]

    def process_pflow_bus(self, tokens):
        # print("Bus Power Flow : %s" % tokens)
        # print tokens["bus"]

        pu_check = lambda x: dec_check(x, Decimal("-10.0"), Decimal("10.0"))
        for x in "v pg qg pl ql".split():
            self.ensure(pu_check(tokens[x]), "error : \n%s" % tokens)
        self.ensure(dec_check(tokens["phase"],"-1.0","1.0"), "error : \n%s" % tokens)

        # actually add to self.power_flow
        # are we to assume that there is a 1-to-1 mapping of names to the natural numbers
        # if not then we need a very gay lookup, if so then ... woo 
        # im going to assume they are sequential.

        bus_num = tokens["bus"][0]
        self.power_flow[bus_num] = self.PowerFlow(
            bus_num,
            tokens["v"],
            tokens["phase"],
            tokens["pg"],
            tokens["qg"],
            tokens["pl"],
            tokens["ql"])

    def process_pflow_bus_limit(self, tokens):
        # print("Limit : %s" % tokens)
        self.ensure("limreact" not in tokens, "Reactive Power Limit")

    def process_lineflow_bus(self, tokens):
        # print("Bus Line Flow : %s" % tokens)
        # print tokens["bus1"]
        # print tokens["bus2"]

        pu_check = lambda x: dec_check(x, Decimal("-5.0"), Decimal("5.0"))
        for x in "pf qf pl ql".split():
            self.ensure(pu_check(tokens[x]), "error : \n%s" % tokens)
        self.ensure(1 <= tokens["linenum"] <= 1000, "error : \n%s" % tokens)

        # TODO: I don't actually add anything to self.line_flow
        # fbus, tbus, line, pf, qf, pl, ql

    def process_summary(self, tokens):
        # print("Summary : %s" % tokens)

        inrange = lambda x: dec_check(x, Decimal("0.0"), Decimal("100.0"))
        for x in range(4):
            self.ensure(inrange(x), "error : \n%s" % tokens)

        self.ensure(dec_check(tokens[4], Decimal("-10.0"), Decimal("10.0")), "error : \n%s" % tokens)
        self.ensure(dec_check(tokens[5], Decimal("-10.0"), Decimal("10.0")), "error : \n%s" % tokens)

    def process_limits(self, tokens):
        # print("Limits : %s" % tokens)

        if any((tok in tokens) for tok in ["reactfail", "voltfail"]):
            self.acceptable = False

    #------------------------------------------------------------------------------
    #
    #------------------------------------------------------------------------------

    def GetHeaders(self):
        title = Group(Optional(Literal("OPTIMAL")) + Literal("POWER FLOW REPORT"))
        title.setParseAction(self.process_header_title)
        version = slit("P S A T  2.1.") + integer.suppress()
        author = slit("Author:  Federico Milano, (c) 2002-2009")
        email = slit("e-mail:  Federico.Milano@uclm.es")
        website = slit("website: http://www.uclm.es/area/gsee/Web/Federico")
        filename = slit("File:") + restOfLine.suppress()
        date = slit("Date:") + restOfLine.suppress()

        return title + version + author + email + website + filename + date

    def GetStats(self):
        ntitle = slit("NETWORK STATISTICS")
        buses = slit("Buses:") + integer("buses")
        lines = slit("Lines:") + integer("lines")
        transformers = slit("Transformers:") + integer("transformers")
        generators = slit("Generators:") + integer("generators")
        loads = slit("Loads:") + integer("loads")
        ngroup = Group(ntitle + buses + lines + transformers + generators + loads)

        stitle = slit("SOLUTION STATISTICS")
        iterations = slit("Number of Iterations:") + integer("iterations")
        pmismatch = slit("Maximum P mismatch [p.u.]") + decimal("pmis")
        qmismatch = slit("Maximum Q mismatch [p.u.]") + decimal("qmis")
        rate = slit("Power rate [MVA]") + decimal("rate")
        sgroup = Group(stitle + iterations + pmismatch + qmismatch + rate)

        return (ngroup + sgroup).setParseAction(self.process_stats)

    def GetPflow(self):
        title = slit("POWER FLOW RESULTS")
        head1 = stringtolits("Bus V phase P gen Q gen P load Q load")
        head2 = stringtolits("[p.u.] [rad] [p.u.] [p.u.] [p.u.] [p.u.]")

        busdef = busname("bus") + decimaltable("v phase pg qg pl ql".split())

        buses = OneOrMore(busdef.setParseAction(self.process_pflow_bus))

        limvoltmin = (slit("Minimum voltage limit violation at bus <") +
                      busname("limvoltmin") +
                      slit("> [V_min =") + 
                      decimal.suppress() + 
                      slit("]"))

        topvolt = (slit("Maximum voltage at bus <") +
                   busname("topvolt") +
                   slit(">"))

        limreact = (slit("Maximum reactive power limit violation at bus <") +
                    busname("limreact") +
                    slit("> [Qg_max =") + 
                    decimal.suppress() + 
                    slit("]"))

        topreact = (slit("Maximum reactive power at bus <") +
                    busname("topreact") +
                    slit(">"))

        limline = limvoltmin | topvolt | limreact | topreact
        limits = ZeroOrMore(limline).setParseAction(self.process_pflow_bus_limit)

        return title + head1 + head2 + buses + limits

    def GetLineflow(self):
        title = slit("LINE FLOWS")
        head1 = stringtolits("From Bus To Bus Line P Flow Q Flow P Loss Q Loss")
        head2 = stringtolits("[p.u.] [p.u.] [p.u.] [p.u.]")

        busdef = (busname("bus1") +
                  busname("bus2") +
                  integer("linenum") +
                  decimaltable("pf qf pl ql".split()))

        busdef = busdef.setParseAction(self.process_lineflow_bus)
        buses = OneOrMore(busdef)

        lineflow = title + head1 + head2 + buses

        return lineflow + lineflow

    def GetSummary(self):
        title = slit("GLOBAL SUMMARY REPORT")

        real = slit("REAL POWER [p.u.]") + decimal
        react = slit("REACTIVE POWER [p.u.]") + decimal

        totalgen = slit("TOTAL GENERATION") + real + react
        totalload = slit("TOTAL LOAD") + real + react
        totalloss = slit("TOTAL LOSSES") + real + react

        return (title + totalgen + totalload + totalloss).setParseAction(self.process_summary)

    def GetLimits(self):
        title = slit("LIMIT VIOLATION STATISTICS")

        voltfail = slit("# OF VOLTAGE LIMIT VIOLATIONS:") + integer("voltfail")
        voltpass = slit("ALL VOLTAGES WITHIN LIMITS") + restOfLine.suppress()
        volt = voltpass | voltfail

        reactpass = (slit("ALL REACTIVE POWER") + 
                     Optional("S").suppress() + 
                     slit("WITHIN LIMITS") + 
                     restOfLine.suppress())

        reactfail = (slit("# OF REACTIVE POWER LIMIT VIOLATIONS:") +
                     integer("reactfail"))

        react = reactfail | reactpass

        current = slit("ALL CURRENT FLOWS WITHIN LIMITS") + restOfLine.suppress()
        real = slit("ALL REAL POWER FLOWS WITHIN LIMITS") + restOfLine.suppress()
        apparent = slit("ALL APPARENT POWER FLOWS WITHIN LIMITS") + restOfLine.suppress()

        return (title + volt + react + current + real + apparent).setParseAction(self.process_limits)

#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------

# PSATreport().parse_stream(open("psat_01.txt"))

def zeros(length):
    """an array of given length where each item is zero"""
    return [0 for _ in range(length)]

# take a psat report file and a psat file
# combine to make a new psat file that has the following set. 
#
# SW.con
#   3. V0      -- power_flow[slackbusnum]._v
#   4. theta0  -- power_flow[slackbusnum]._phase
#   9. Pg0     -- ???  power_flow[slackbusnum]._pg
#
# pv.con
#   Pg         -- power_flow[busnum]._pg
#   V0         -- power_flow[busnum]._v
#
# PQ.con
#   Pl         -- power_flow[busnum]._pl
#   Ql         -- power_flow[busnum]._ql
# 

def generate_scenario(report_stream, psat_data):

    new_psat = deepcopy(psat_data)

    report = PSATreport()
    report.parse_stream(report_stream)
    pf = report.power_flow

    slack = new_psat.slack[0]
    slack.v_magnitude = pf[slack.bus_no]._v
    slack.ref_angle = pf[slack.bus_no]._phase
    # slack.p_guess = pf[slack.bus_no]._pg

    for gen in new_psat.generators:
        assert pf[gen.bus_no] != None
        gen.p = pf[gen.bus_no]._pg
        gen.v = pf[gen.bus_no]._v

    for load in new_psat.loads:
        assert pf[load.bus_no] != None
        load.p = pf[load.bus_no]._pg
        load.q = pf[load.bus_no]._q

    return new_psat
