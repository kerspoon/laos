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

""" Defines a class for reading PSAT data files.
    based almost entirely on pylon by Richard W. Lincoln
    overload the PSATReader push functions to use.
"""

#------------------------------------------------------------------------------
#  Imports:
#------------------------------------------------------------------------------

import sys 
import optparse
import time
import logging
from os.path import basename, splitext
from parsing_util import integer, boolean, real, scolon, matlab_comment
from pyparsing import Optional, Literal, ZeroOrMore

#------------------------------------------------------------------------------
#  Logging:
#------------------------------------------------------------------------------

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
    format="%(levelname)s: %(message)s")

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
#  as_csv :: [T], str -> str
#------------------------------------------------------------------------------
def as_csv(iterable,sep = "  "):
    """a string of each item seperated by commas"""
    iterable = list(iterable)
    res = ""
    if len(iterable) == 0:
        return ""
    for item in iterable[:-1]:
        res += str(item) + sep
    return res + str(iterable[len(iterable)-1])

#------------------------------------------------------------------------------
#  PSAT classes:
#------------------------------------------------------------------------------

def write_section(stream, items, title):
    stream.write(title + ".con = [ ... \n")
    for item in items:
        stream.write("  " + str(item) + "\n")
    stream.write(" ];\n")

class PSAT(object):

    class basic(object):
        def __init__(self, tokens=None):
            if tokens:
                self.dictfill(tokens)
                self.check()

        def __str__(self):
            return as_csv(self.__dict__[x] for x in self.entries)

        def dictfill(self, kwds):
            self.__dict__.update(kwds)

        def check(self):
            for item in self.entries:
                assert item in self.__dict__

    class Bus(basic):
        entries = "bus_no v_base v_magnitude_guess v_angle_guess area region".split()
                   
    class Line(basic):
        entries = "fbus tbus s_rating v_rating f_rating length v_ratio r x b tap shift i_limit p_limit s_limit status".split()
            
    class Slack(basic):
        entries = "bus_no s_rating v_rating v_magnitude ref_angle q_max q_min v_max v_min p_guess lp_coeff ref_bus status".split()

    class Generator(basic):
        entries = "bus_no s_rating v_rating p v q_max q_min v_max v_min lp_coeff status".split()

    class Load(basic):
        entries = "bus_no s_rating v_rating p q v_max v_min z_conv status".split()

    class Shunt(basic):
        entries = "bus_no  s_rating v_rating f_rating g b status".split()

    class Demand(basic):
        entries = "bus_no s_rating p_direction q_direction \
            p_bid_max p_bid_min p_optimal_bid p_fixed \
            p_proportional p_quadratic q_fixed q_proportional \
            q_quadratic commitment cost_tie_break cost_cong_up \
            cost_cong_down status".split()

    class Supply(basic):
        entries = "bus_no s_rating p_direction p_bid_max \
            p_bid_min p_bid_actual p_fixed p_proportional \
            p_quadratic q_fixed q_proportional q_quadratic \
            commitment cost_tie_break lp_factor q_max q_min \
            cost_cong_up cost_cong_down status".split()

    def __init__(self):
        self.busses = []
        self.lines = []
        self.slack = []
        self.generators = []
        self.loads = []
        self.shunts = []
        self.demand = []
        self.supply = []

    def write(self, stream):
        write_section(stream, self.busses, "Bus")
        write_section(stream, self.lines, "Line")
        write_section(stream, self.slack, "SW")
        write_section(stream, self.generators, "PV")
        write_section(stream, self.loads, "PQ")
        write_section(stream, self.shunts, "Shunt")
        write_section(stream, self.demand, "Demand")
        write_section(stream, self.supply, "Supply")

#------------------------------------------------------------------------------
#  "PSATReader" class:
#------------------------------------------------------------------------------

class PSATReader(object):
    """ Defines a method class for reading PSAT data files
    """

    def __init__(self):
        """ Initialises a new PSATReader instance.
        """
        # Path to the data file or file object.
        self.file_or_filename = None
        self.psat = PSAT()

    def __call__(self, file_or_filename):
        """ Calls the reader with the given file or file name.
        """
        self.read(file_or_filename)

    #--------------------------------------------------------------------------
    #  Parse a PSAT data file and return a case object
    #--------------------------------------------------------------------------

    def read(self, file_or_filename):
        """ Parses a PSAT data file and returns a case object

            file: File object or path to data file with PSAT format data
            return: Case object
        """
        self.file_or_filename = file_or_filename

        logger.info("Parsing PSAT case file [%s]." % file_or_filename)

        t0 = time.time()

        # Name the case
        if isinstance(file_or_filename, basestring):
            name, ext = splitext(basename(file_or_filename))
        else:
            name, ext = splitext(file_or_filename.name)

        bus_array = self._get_bus_array_construct()
        line_array = self._get_line_array_construct()
        # TODO: Lines.con - Alternative line data format
        slack_array = self._get_slack_array_construct()
        pv_array = self._get_pv_array_construct()
        pq_array = self._get_pq_array_construct()
        shunt_array = self._get_shunt_array_construct()
        demand_array = self._get_demand_array_construct()
        supply_array = self._get_supply_array_construct()
        # TODO: Varname.bus (Bus names)

        # Pyparsing case:
        case = \
            ZeroOrMore(matlab_comment) + bus_array + \
            ZeroOrMore(matlab_comment) + line_array + \
            ZeroOrMore(matlab_comment) + slack_array + \
            ZeroOrMore(matlab_comment) + pv_array + \
            ZeroOrMore(matlab_comment) + pq_array + \
            ZeroOrMore(matlab_comment) + shunt_array + \
            ZeroOrMore(matlab_comment) + demand_array + \
            ZeroOrMore(matlab_comment) + supply_array

        data = case.parseFile(file_or_filename)

        elapsed = time.time() - t0
        logger.info("PSAT case file parsed in %.3fs." % elapsed)

        return data

    #--------------------------------------------------------------------------
    #  Construct getters:
    #--------------------------------------------------------------------------

    def _get_bus_array_construct(self):
        """ Returns a construct for an array of bus data.
        """
        bus_no = integer.setResultsName("bus_no")
        v_base = real.setResultsName("v_base") # kV
        v_magnitude_guess = Optional(real).setResultsName("v_magnitude_guess")
        v_angle_guess = Optional(real).setResultsName("v_angle_guess") # radians
        area = Optional(integer).setResultsName("area") # not used yet
        region = Optional(integer).setResultsName("region") # not used yet

        bus_data = bus_no + v_base + v_magnitude_guess + v_angle_guess + \
            area + region + scolon

        bus_data.setParseAction(self.push_bus)

        bus_array = Literal("Bus.con") + "=" + "[" + "..." + \
            ZeroOrMore(bus_data + Optional("]" + scolon))

        # Sort buses according to their name (bus_no)
        bus_array.setParseAction(self.sort_buses)

        return bus_array


    def _get_line_array_construct(self):
        """ Returns a construct for an array of line data.
        """
        source_bus = integer.setResultsName("fbus")
        target_bus = integer.setResultsName("tbus")
        s_rating = real.setResultsName("s_rating") # MVA
        v_rating = real.setResultsName("v_rating") # kV
        f_rating = real.setResultsName("f_rating") # Hz
        length = real.setResultsName("length") # km (Line only)
        v_ratio = real.setResultsName("v_ratio") # kV/kV (Transformer only)
        r = real.setResultsName("r") # p.u. or Ohms/km
        x = real.setResultsName("x") # p.u. or Henrys/km
        b = real.setResultsName("b") # p.u. or Farads/km (Line only)
        tap_ratio = real.setResultsName("tap") # p.u./p.u. (Transformer only)
        phase_shift = real.setResultsName("shift") # degrees (Transformer only)
        i_limit = Optional(real).setResultsName("i_limit") # p.u.
        p_limit = Optional(real).setResultsName("p_limit") # p.u.
        s_limit = Optional(real).setResultsName("s_limit") # p.u.
        status = Optional(integer).setResultsName("status")

        line_data = source_bus + target_bus + s_rating + v_rating + \
            f_rating + length + v_ratio + r + x + b + tap_ratio + \
            phase_shift + i_limit + p_limit + s_limit + status + scolon

        line_data.setParseAction(self.push_line)

        line_array = Literal("Line.con") + "=" + "[" + "..." + \
            ZeroOrMore(line_data + Optional("]" + scolon))

        return line_array


    def _get_slack_array_construct(self):
        """ Returns a construct for an array of slack bus data.
        """
        bus_no = integer.setResultsName("bus_no")
        s_rating = real.setResultsName("s_rating") # MVA
        v_rating = real.setResultsName("v_rating") # kV
        v_magnitude = real.setResultsName("v_magnitude") # p.u.
        ref_angle = real.setResultsName("ref_angle") # p.u.
        q_max = Optional(real).setResultsName("q_max") # p.u.
        q_min = Optional(real).setResultsName("q_min") # p.u.
        v_max = Optional(real).setResultsName("v_max") # p.u.
        v_min = Optional(real).setResultsName("v_min") # p.u.
        p_guess = Optional(real).setResultsName("p_guess") # p.u.
         # Loss participation coefficient
        lp_coeff = Optional(real).setResultsName("lp_coeff")
        ref_bus = Optional(integer).setResultsName("ref_bus")
        status = Optional(integer).setResultsName("status")

        slack_data = bus_no + s_rating + v_rating + v_magnitude + \
            ref_angle + q_max + q_min + v_max + v_min + p_guess + \
            lp_coeff + ref_bus + status + scolon

        slack_data.setParseAction(self.push_slack)

        slack_array = Literal("SW.con") + "=" + "[" + "..." + \
            ZeroOrMore(slack_data + Optional("]" + scolon))

        return slack_array

    def _get_shunt_array_construct(self):
        """ Returns a construct for an array of shunts.
        """
        bus_no = integer.setResultsName("bus_no")
        s_rating = real.setResultsName("s_rating") # MVA
        v_rating = real.setResultsName("v_rating") # kV
        f_rating = real.setResultsName("f_rating") # Hz
        g = real.setResultsName("g") # p.u.
        b = real.setResultsName("b") # p.u.
        status = Optional(integer).setResultsName("status")
        
        shunt_data = bus_no +  s_rating + v_rating + f_rating + \
            g + b + status + scolon

        shunt_data.setParseAction(self.push_shunt)

        shunt_array = Literal("Shunt.con") + "=" + "[" + "..." + \
            ZeroOrMore(shunt_data + Optional("]" + scolon))

        return shunt_array
         
    def _get_pv_array_construct(self):
        """ Returns a construct for an array of PV generator data.
        """
        bus_no = integer.setResultsName("bus_no")
        s_rating = real.setResultsName("s_rating") # MVA
        v_rating = real.setResultsName("v_rating") # kV
        p = real.setResultsName("p") # p.u.
        v = real.setResultsName("v") # p.u.
        q_max = Optional(real).setResultsName("q_max") # p.u.
        q_min = Optional(real).setResultsName("q_min") # p.u.
        v_max = Optional(real).setResultsName("v_max") # p.u.
        v_min = Optional(real).setResultsName("v_min") # p.u.
         # Loss participation coefficient
        lp_coeff = Optional(real).setResultsName("lp_coeff")
        status = Optional(integer).setResultsName("status")

        pv_data = bus_no + s_rating + v_rating + p + v + q_max + \
            q_min + v_max + v_min + lp_coeff + status + scolon

        pv_data.setParseAction(self.push_pv)

        pv_array = Literal("PV.con") + "=" + "[" + "..." + \
            ZeroOrMore(pv_data + Optional("]" + scolon))

        return pv_array


    def _get_pq_array_construct(self):
        """ Returns a construct for an array of PQ load data.
        """
        bus_no = integer.setResultsName("bus_no")
        s_rating = real.setResultsName("s_rating") # MVA
        v_rating = real.setResultsName("v_rating") # kV
        p = real.setResultsName("p") # p.u.
        q = real.setResultsName("q") # p.u.
        v_max = Optional(real).setResultsName("v_max") # p.u.
        v_min = Optional(real).setResultsName("v_min") # p.u.
        # Allow conversion to impedance
        z_conv = Optional(integer).setResultsName("z_conv")
        status = Optional(integer).setResultsName("status")

        pq_data = bus_no + s_rating + v_rating + p + q + v_max + \
            v_min + z_conv + status + scolon

        pq_data.setParseAction(self.push_pq)

        pq_array = Literal("PQ.con") + "=" + "[" + "..." + \
            ZeroOrMore(pq_data + Optional("]" + scolon))

        return pq_array


    def _get_demand_array_construct(self):
        """ Returns a construct for an array of power demand data.
        """
        bus_no = integer.setResultsName("bus_no")
        s_rating = real.setResultsName("s_rating") # MVA
        p_direction = real.setResultsName("p_direction") # p.u.
        q_direction = real.setResultsName("q_direction") # p.u.
        p_bid_max = real.setResultsName("p_bid_max") # p.u.
        p_bid_min = real.setResultsName("p_bid_min") # p.u.
        p_optimal_bid = Optional(real).setResultsName("p_optimal_bid")
        p_fixed = real.setResultsName("p_fixed") # $/hr
        p_proportional = real.setResultsName("p_proportional") # $/MWh
        p_quadratic = real.setResultsName("p_quadratic") # $/MW^2h
        q_fixed = real.setResultsName("q_fixed") # $/hr
        q_proportional = real.setResultsName("q_proportional") # $/MVArh
        q_quadratic = real.setResultsName("q_quadratic") # $/MVAr^2h
        commitment = integer.setResultsName("commitment")
        cost_tie_break = real.setResultsName("cost_tie_break") # $/MWh
        cost_cong_up = real.setResultsName("cost_cong_up") # $/h
        cost_cong_down = real.setResultsName("cost_cong_down") # $/h
        status = Optional(integer).setResultsName("status")

        demand_data = bus_no + s_rating + p_direction + q_direction + \
            p_bid_max + p_bid_min + p_optimal_bid + p_fixed + \
            p_proportional + p_quadratic + q_fixed + q_proportional + \
            q_quadratic + commitment + cost_tie_break + cost_cong_up + \
            cost_cong_down + status + scolon

        demand_data.setParseAction(self.push_demand)

        demand_array = Literal("Demand.con") + "=" + "[" + "..." + \
            ZeroOrMore(demand_data + Optional("]" + scolon))

        return demand_array


    def _get_supply_array_construct(self):
        """ Returns a construct for an array of power supply data.
        """
        bus_no = integer.setResultsName("bus_no")
        s_rating = real.setResultsName("s_rating") # MVA
        p_direction = real.setResultsName("p_direction") # CPF
        p_bid_max = real.setResultsName("p_bid_max") # p.u.
        p_bid_min = real.setResultsName("p_bid_min") # p.u.
        p_bid_actual = real.setResultsName("p_bid_actual") # p.u.
        p_fixed = real.setResultsName("p_fixed") # $/hr
        p_proportional = real.setResultsName("p_proportional") # $/MWh
        p_quadratic = real.setResultsName("p_quadratic") # $/MW^2h
        q_fixed = real.setResultsName("q_fixed") # $/hr
        q_proportional = real.setResultsName("q_proportional") # $/MVArh
        q_quadratic = real.setResultsName("q_quadratic") # $/MVAr^2h
        commitment = integer.setResultsName("commitment")
        cost_tie_break = real.setResultsName("cost_tie_break") # $/MWh
        lp_factor = real.setResultsName("lp_factor")# Loss participation factor
        q_max = real.setResultsName("q_max") # p.u.
        q_min = real.setResultsName("q_min") # p.u.
        cost_cong_up = real.setResultsName("cost_cong_up") # $/h
        cost_cong_down = real.setResultsName("cost_cong_down") # $/h
        status = Optional(integer).setResultsName("status")

        supply_data = bus_no + s_rating + p_direction + p_bid_max + \
            p_bid_min + p_bid_actual + p_fixed + p_proportional + \
            p_quadratic + q_fixed + q_proportional + q_quadratic + \
            commitment + cost_tie_break + lp_factor + q_max + q_min + \
            cost_cong_up + cost_cong_down + status + scolon

        supply_data.setParseAction(self.push_supply)

        supply_array = Literal("Supply.con") + "=" + "[" + "..." + \
            ZeroOrMore(supply_data + Optional("]" + scolon))

        return supply_array


    def _get_generator_ramping_construct(self):
        """ Returns a construct for an array of generator ramping data.
        """
        supply_no = integer.setResultsName("supply_no")
        s_rating = real.setResultsName("s_rating") # MVA
        up_rate = real.setResultsName("up_rate") # p.u./h
        down_rate = real.setResultsName("down_rate") # p.u./h
        min_period_up = real.setResultsName("min_period_up") # h
        min_period_down = real.setResultsName("min_period_down") # h
        initial_period_up = integer.setResultsName("initial_period_up")
        initial_period_down = integer.setResultsName("initial_period_down")
        c_startup = real.setResultsName("c_startup") # $
        status = integer.setResultsName("status")

        g_ramp_data = supply_no + s_rating + up_rate + down_rate + \
            min_period_up + min_period_down + initial_period_up + \
            initial_period_down + c_startup + status + scolon

        g_ramp_array = Literal("Rmpg.con") + "=" + "[" + \
            ZeroOrMore(g_ramp_data + Optional("]" + scolon))

        return g_ramp_array


    def _get_load_ramping_construct(self):
        """ Returns a construct for an array of load ramping data.
        """
        bus_no = integer.setResultsName("bus_no")
        s_rating = real.setResultsName("s_rating") # MVA
        up_rate = real.setResultsName("up_rate") # p.u./h
        down_rate = real.setResultsName("down_rate") # p.u./h
        min_up_time = real.setResultsName("min_up_time") # min
        min_down_time = real.setResultsName("min_down_time") # min
        n_period_up = integer.setResultsName("n_period_up")
        n_period_down = integer.setResultsName("n_period_down")
        status = integer.setResultsName("status")

        l_ramp_data = bus_no + s_rating + up_rate + down_rate + \
            min_up_time + min_down_time + n_period_up + \
            n_period_down + status + scolon

        l_ramp_array = Literal("Rmpl.con") + "=" + "[" + \
            ZeroOrMore(l_ramp_data + Optional("]" + scolon))

        return l_ramp_array

    #--------------------------------------------------------------------------
    #  Parse actions:
    #--------------------------------------------------------------------------

    def push_bus(self, tokens):
        """ Adds a Bus object to the case.
        """
        logger.debug("Pushing bus data: %s" % tokens)
        self.psat.busses.append(PSAT.Bus(tokens))

    def sort_buses(self, tokens):
        """ Sorts bus list according to name (bus_no).
        """
        logger.debug("Sorting busses: %s" % tokens)
        #TODO: might need to do something smart with the names!

    def push_line(self, tokens):
        """ Adds a Branch object to the case.
        """
        logger.debug("Pushing line data: %s" % tokens)
        self.psat.lines.append(PSAT.Line(tokens))

    def push_shunt(self, tokens):
        """ Adds a Shunt object to the case.
        """
        logger.debug("Pushing shunt data: %s" % tokens)
        self.psat.shunts.append(PSAT.Shunt(tokens))

    def push_slack(self, tokens):
        """ Finds the slack bus, adds a Generator with the appropriate data
            and sets the bus type to slack.
        """
        logger.debug("Pushing slack data: %s" % tokens)
        self.psat.slack.append(PSAT.Slack(tokens))

    def push_pv(self, tokens):
        """ Creates and Generator object, populates it with data,
            finds its Bus and adds it.
        """
        logger.debug("Pushing PV data: %s" % tokens)
        self.psat.generators.append(PSAT.Generator(tokens))

    def push_pq(self, tokens):
        """ Creates and Load object, populates it with data,
            finds its Bus and adds it.
        """
        logger.debug("Pushing PQ data: %s" % tokens)
        self.psat.loads.append(PSAT.Load(tokens))

    def push_demand(self, tokens):
        """ Added OPF and CPF data to an appropriate Load.
        """
        logger.debug("Pushing demand data: %s" % tokens)
        self.psat.demand.append(PSAT.Demand(tokens))

    def push_supply(self, tokens):
        """ Adds OPF and CPF data to a Generator.
        """
        logger.debug("Pushing supply data: %s" % tokens)
        self.psat.supply.append(PSAT.Supply(tokens))

#------------------------------------------------------------------------------
#  "main2" function:
#------------------------------------------------------------------------------

def main2(infile, outfile):
    readme = PSATReader()
    readme(infile)
    readme.psat.write(open(outfile,"w"))

#------------------------------------------------------------------------------
#  "main" function:
#------------------------------------------------------------------------------

def main():
    """ Parses the command line and call Pylon with the correct data.
    """
    parser = optparse.OptionParser("usage: pylon [options] input_file")

    parser.add_option("-o", "--output", dest="output", metavar="FILE",
        help="Write the solution report to FILE.")

    parser.add_option("-q", "--quiet", action="store_true", dest="quiet",
        default=False, help="Print less information.")

    parser.add_option("-d", "--debug", action="store_true", dest="debug",
        default=False, help="Print debug information.")

    (options, args) = parser.parse_args()

    if options.quiet:
        logger.info("setting logger level to critical")
        logger.setLevel(logging.CRITICAL)
    elif options.debug:
        logger.info("setting logger level to debug")
        logger.setLevel(logging.DEBUG)
    else:
        logger.info("setting logger level to info")
        logger.setLevel(logging.INFO)

    # Output.
    if options.output:
        outfile = options.output
        if outfile == "-":
            outfile = sys.stdout
            logger.info("logger level set to critical as output is to stdout")
            logger.setLevel(logging.CRITICAL) # we must stay quiet
    else:
        outfile = sys.stdout
        logger.info("logger level set to critical as output is to stdout")
        logger.setLevel(logging.CRITICAL) # we must stay quiet

    # Input.
    if len(args) > 1:
        parser.print_help()
        sys.exit(1)
    elif len(args) == 0 or args[0] == "-":
        infilename = ""
        if sys.stdin.isatty():
            # True if the file is connected to a tty device, and False
            # otherwise (pipeline or file redirection).
            parser.print_help()
            sys.exit(1)
        else:
            # Handle piped input ($ cat ehv3.raw | pylon | rst2pdf -o ans.pdf).
            infile = sys.stdin
    else:
        infilename = args[0]
        infile   = open(infilename)

    logger.info("Running Program with: %s" % infilename)
    logger.info("===================")
    main2(infile, outfile)
    logger.info("===================")

if __name__ == "__main__":
    main()


# EOF -------------------------------------------------------------------------
