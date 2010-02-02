#! /usr/local/bin/python
# psat_report.py - PsatReport - report_file - report

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

psat_report.py - PsatReport - report_file - report

Read in a report from psat; check format & sanity check.
Note:: doesn't check component limits against their stored values
Note:: doesn't fully fill in the data, but parses everything
"""

#------------------------------------------------------------------------------
# Imports:
#------------------------------------------------------------------------------


from parsingutil import Literal, integer, Group, Optional, restOfLine, decimal
from parsingutil import stringtolits, decimaltable, OneOrMore, ZeroOrMore, slit
from decimal import Decimal


#------------------------------------------------------------------------------
# Util:
#------------------------------------------------------------------------------

def dec_check(val, vmin=Decimal("-1.0"), vmax=Decimal("1.0")):
    return Decimal(vmin) <= val <= Decimal(vmax)

def almost_equal(x, y):
    return abs(Decimal(x) - Decimal(y)) < Decimal("0.001")

busname = Literal("Bus").suppress() + integer

#------------------------------------------------------------------------------
# PsatReport:
#------------------------------------------------------------------------------

class PsatReport(object):
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
        self.power_flow = {}
        self.line_flow = {}

        self.acceptable = True

    def in_limit(self):
        return self.acceptable

    def read(self, stream):
        # print "Parsing stream: %s" % stream

        try:
            headers = self.GetHeaders()
            stats = self.GetStats()
            pflow = self.GetPflow()
            lineflow = self.GetLineflow()
            summary = self.GetSummary()
            limits = self.GetLimits()

            case = headers + stats + pflow + lineflow + summary + limits
            self.data = case.parseFile(stream)
            # print "Done Parsing stream"
        except:
            print "PARSING ERROR"
            raise
        return self.acceptable

    def ensure(self, cond, text):
        if not cond:
            print "FAIL!!!\t", text
            self.acceptable = False

    def process_header_title(self, tokens):
        # print("Header : %s" % tokens)
        if len(tokens[0]) == 1:
            # print "Power Flow"
            pass
        elif len(tokens[0]) == 2:
            # print "Optimal Power Flow"
            pass 
        else:
            raise Exception("%s" % tokens)

    def process_stats(self, tokens):
        # print("Stats : %s" % tokens)

        for x in "loads generators transformers lines buses".split():
            y = tokens[0][x]
            self.ensure(y > 0, "incorrect number of components, got " + str(y))

        self.ensure(1 <= tokens[1]["iterations"] <= 10000, "iterations >= 1")
        self.ensure(dec_check(tokens[1]["pmis"]), "pmis")
        self.ensure(dec_check(tokens[1]["qmis"]), "qmis")
        self.ensure(almost_equal("100", tokens[1]["rate"]), "rate == 100")

        self.num_load = tokens[0]["loads"]
        self.num_generator = tokens[0]["generators"]
        self.num_transformer = tokens[0]["transformers"]
        self.num_line = tokens[0]["lines"]
        self.num_bus = tokens[0]["buses"]
        self.power_rate = tokens[1]["rate"]

        # set length only (line flows are there and back)
        self.power_flow = {}
        self.line_flow = {}

    def process_pflow_bus(self, tokens):
        # print "Bus Power Flow : %d : %s" % (tokens["bus"][0],tokens)
        # print tokens["bus"][0]

        pu_check = lambda x: dec_check(x, Decimal("-10.0"), Decimal("10.0"))
        for x in "v pg qg pl ql".split():
            self.ensure(pu_check(tokens[x]), "error : \n%s" % tokens)
        self.ensure(dec_check(tokens["phase"]), "error : \n%s" % tokens)

        # actually add to self.power_flow

        # are we to assume that there is a 1-to-1 mapping of names to the 
        # natural numbers if not then we need a very gay lookup, if so then 
        # ... woo
        # im going to assume they do map. even then, do we then keep the 1 based 
        # counting or convert to zero based. GAAAAYYYY
        #  * if I convert the external file to zero based. it wont then match the
        #    journal paper
        #  * if I convert the interal representation it wont match the file or
        #    paper
        #  * if I leave it then there may be strange bugs as there will be a
        #    dummy element

        # I have decided to use a dict rather than a list, it still has integers
        # as the key it sovles the other problems. only requirement is that they
        # are unique integers. 

        bus_num = tokens["bus"][0]

        assert bus_num >= 0
        assert bus_num not in self.power_flow, "already added bus "+ str(bus_num) 

        self.power_flow[bus_num] = self.PowerFlow(
            bus_num,
            tokens["v"],
            tokens["phase"],
            tokens["pg"],
            tokens["qg"],
            tokens["pl"],
            tokens["ql"])

    def process_pflow_overload(self, _):
        # print("Limit : %s" % tokens)
        
        self.ensure(False, "PowerFlow Limit")

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
        ten_check = lambda x: dec_check(x, Decimal("0.0"), Decimal("10.0"))

        for x in range(4):
            self.ensure(inrange(x), "error : \n%s" % tokens)

        self.ensure(ten_check(tokens[4]), "error : \n%s" % tokens)
        self.ensure(ten_check(tokens[5]), "error : \n%s" % tokens)

    def process_limits(self, tokens):
        # print("Limits : %s" % tokens)

        if any((tok in tokens) for tok in ["reactfail", "voltfail"]):
            self.acceptable = False

    #---------------------------------------------------------------------------
    #
    #---------------------------------------------------------------------------

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

        maxmin = slit("Maximum") | slit("Minimum")
        afix = maxmin + (slit("reactive power") | slit("voltage")) 
        postfix = busname("bus") + slit(">") + restOfLine.suppress()

        binding = afix + slit("at bus <") + postfix
        overload = afix + slit("limit violation at bus <") + postfix
        overload.setParseAction(self.process_pflow_overload)

        limits = ZeroOrMore(binding | overload)

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

        summary = title + totalgen + totalload + totalloss
        summary.setParseAction(self.process_summary)
        return summary

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

        limits = title + volt + react + current + real + apparent
        limits.setParseAction(self.process_limits)
        return limits


#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------

