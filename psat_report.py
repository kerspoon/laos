#! /usr/local/bin/python
# psat_report.parse_stream(open("psat_outage0_01.txt"))
 
from pyparsing import *
from decimal import Decimal
import string
import logging
import sys
import pprint

logger = logging.getLogger(__name__)

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
    format="%(levelname)s: %(message)s")

class ToBoolean(TokenConverter):
    """ Converter to make token boolean """
 
    def postParse(self, instring, loc, tokenlist):
        """ Converts the first token to boolean """
        tok = string.lower(tokenlist[0])
        if tok in ["t", "true", "1"]:
            return True
        elif tok in ["f", "false", "0"]:
            return False
        else:
            raise Exception
 
class ToInteger(TokenConverter):
    """ Converter to make token into an integer """
 
    def postParse(self, instring, loc, tokenlist):
        """ Converts the first token to an integer """
 
        return int(tokenlist[0])
 
class ToDecimal(TokenConverter):
    """ Converter to make token into a float """
 
    def postParse(self, instring, loc, tokenlist):
        """ Converts the first token into a float """
 
        return Decimal(tokenlist[0])
 
decimal_sep = "."
sign = oneOf("+ -")
symbols = "_-."
 
bool_true = Or([CaselessLiteral("true"), CaselessLiteral("t"), Literal("1")])
bool_false = Or([CaselessLiteral("false"), CaselessLiteral("f"), Literal("0")])
 
boolean = ToBoolean(Or([bool_true, bool_false]))
 
integer = ToInteger(
    Combine(Optional(sign) + Word(nums))
)
 
decimal = ToDecimal(
    Combine(
        Optional(sign) +
        Word(nums) +
        Optional(decimal_sep + Word(nums)) +
        Optional(oneOf("E e") + Optional(sign) + Word(nums))
    )
)

word = Word(alphanums, alphanums + symbols)
qstring = (sglQuotedString | dblQuotedString)

# don't care about having extra spaces in the literal
stringtolits = lambda x: And([Literal(y) for y in x.split()])

# a space seperated line of decimal values that have a column name
decimaltable = lambda x: And([decimal.setResultsName(y) for y in x])

busname = Or([Literal("Bus") + integer, Word(alphanums + "-_")])

slit = lambda x: Suppress(Literal(x))

def parse_stream(stream):
 
    logger.debug("Parsing stream: %s" % stream)
 
    headers = GetHeaders()
    stats = GetStats()
    pflow = GetPflow()
    lineflow = GetLineflow()
    summary = GetSummary()
    limits = GetLimits()

    case = headers + stats + pflow + lineflow + summary + limits
    data = case.parseFile(stream)

    logger.debug("Done Parsing stream")

def GetHeaders():
    title = Group(Optional(Literal("OPTIMAL")) + Literal("POWER FLOW REPORT"))
    title.setParseAction(process_header_title)
    version = slit("P S A T  2.1.") + integer.suppress()
    author = slit("Author:  Federico Milano, (c) 2002-2009")
    email = slit("e-mail:  Federico.Milano@uclm.es")
    website = slit("website: http://www.uclm.es/area/gsee/Web/Federico")
    filename = slit("File:") + restOfLine.suppress()
    date = slit("Date:") + restOfLine.suppress()

    return title + version + author + email + website + filename + date

def GetStats():
    ntitle = slit("NETWORK STATISTICS")
    buses = slit("Buses:") + integer.setResultsName("buses")
    lines = slit("Lines:") + integer.setResultsName("lines")
    transformers = slit("Transformers:") + integer.setResultsName("transformers")
    generators = slit("Generators:") + integer.setResultsName("generators")
    loads = slit("Loads:") + integer.setResultsName("loads")
    ngroup = Group(ntitle + buses + lines + transformers + generators + loads)
    
    stitle = slit("SOLUTION STATISTICS")
    iterations = slit("Number of Iterations:") + integer.setResultsName("iterations")
    pmismatch = slit("Maximum P mismatch [p.u.]") + decimal.setResultsName("pmis")
    qmismatch = slit("Maximum Q mismatch [p.u.]") + decimal.setResultsName("qmis")
    rate = slit("Power rate [MVA]") + decimal.setResultsName("rate")
    sgroup = Group(stitle + iterations + pmismatch + qmismatch + rate)

    return (ngroup + sgroup).setParseAction(process_stats)

def GetPflow():
    title = slit("POWER FLOW RESULTS")
    head1 = stringtolits("Bus V phase P gen Q gen P load Q load")
    head2 = stringtolits("[p.u.] [rad] [p.u.] [p.u.] [p.u.] [p.u.]")

    busdef = busname.setResultsName("bus") + decimaltable("v phase pg qg pl ql".split())

    buses = OneOrMore(busdef.setParseAction(process_pflow_bus))

    limvoltmin = And([slit("Minimum voltage limit violation at bus <"),
                   busname.setResultsName("limvoltmin"),
                   slit("> [V_min =") + decimal.suppress() + slit("]")])

    topvolt = And([slit("Maximum voltage at bus <"),
                   busname.setResultsName("topvolt"),
                   slit(">")])

    limreact = And([slit("Maximum reactive power limit violation at bus <"),
                    busname.setResultsName("limreact"),
                    slit("> [Qg_max =") + decimal.suppress() + slit("]")])

    limline = limvoltmin | topvolt | limreact
    limits = OneOrMore(limline).setParseAction(process_pflow_bus_limit)

    return title + head1 + head2 + buses + limits

def GetLineflow():
    title = slit("LINE FLOWS")
    head1 = stringtolits("From Bus To Bus Line P Flow Q Flow P Loss Q Loss")
    head2 = stringtolits("[p.u.] [p.u.] [p.u.] [p.u.]")
    
    busdef = And([busname.setResultsName("bus1"), 
                  busname.setResultsName("bus2"),
                  integer.setResultsName("linenum"),
                  decimaltable("pf qf pl ql".split())])

    busdef = busdef.setParseAction(process_lineflow_bus)
    buses = OneOrMore(busdef)

    lineflow = title + head1 + head2 + buses

    return lineflow + lineflow

def GetSummary():
    title = slit("GLOBAL SUMMARY REPORT")

    real = slit("REAL POWER [p.u.]") + decimal
    react = slit("REACTIVE POWER [p.u.]") + decimal

    totalgen = slit("TOTAL GENERATION") + real + react
    totalload = slit("TOTAL LOAD") + real + react
    totalloss = slit("TOTAL LOSSES") + real + react
    
    return (title + totalgen + totalload + totalloss).setParseAction(process_summary)

def GetLimits():
    title = slit("LIMIT VIOLATION STATISTICS")

    volt = slit("ALL VOLTAGES WITHIN LIMITS") + restOfLine.suppress()

    reactpass = slit("ALL REACTIVE POWER WITHIN LIMITS") + restOfLine.suppress()
    reactfail = And([slit("# OF REACTIVE POWER LIMIT VIOLATIONS:"),
                     integer.setResultsName("reactfail")])
    react = reactfail | reactpass

    current = slit("ALL CURRENT FLOWS WITHIN LIMITS") + restOfLine.suppress()
    real = slit("ALL REAL POWER FLOWS WITHIN LIMITS") + restOfLine.suppress()
    apparent = slit("ALL APPARENT POWER FLOWS WITHIN LIMITS") + restOfLine.suppress()

    return (title + volt + react + current + real + apparent).setParseAction(process_limits)

def dec_check(val, vmin=Decimal("-1.0"), vmax=Decimal("1.0")):
    return Decimal(vmin) <= val <= Decimal(vmax)

def almost_equal (x, y): 
    return abs(Decimal(x) - Decimal(y)) < Decimal("0.001")

def ensure(cond, text):
    if not cond:
        print "FAIL!!!\t", text

def process_header_title(tokens):
    # print("Header : %s" % tokens)
    if len(tokens[0]) == 1:
        print "Power Flow"
        pass 
    elif len(tokens[0]) == 2:
        print "Optimal Power Flow"
    else:
        raise Exception("%s" % tokens)

def process_stats(tokens):
    # print("Stats : %s" % tokens)

    for x in "loads generators transformers lines buses".split():
        y = tokens[0][x]
        ensure(y > 0, "incorrect number of components, got " + str(y))

    ensure(1 <= tokens[1]["iterations"] <= 10000, "error : \n%s" % tokens)
    ensure(dec_check(tokens[1]["pmis"]), "error : \n%s" % tokens)
    ensure(dec_check(tokens[1]["qmis"]), "error : \n%s" % tokens)
    ensure(almost_equal("100", tokens[1]["rate"]), "error : \n%s" % tokens)

def process_pflow_bus(tokens):
    # print("Bus Power Flow : %s" % tokens)
    # print tokens["bus"]
    
    pu_check = lambda x: dec_check(x, Decimal("-10.0"), Decimal("10.0"))
    for x in "v pg qg pl ql".split():
        ensure(pu_check(tokens[x]), "error : \n%s" % tokens)
    ensure(dec_check(tokens["phase"],"-1.0","1.0"), "error : \n%s" % tokens)

def process_pflow_bus_limit(tokens):
    # print("Limit : %s" % tokens)
    ensure("limreact" not in tokens, "Reactive Power Limit")
    pass 

def process_lineflow_bus(tokens):
    # print("Bus Line Flow : %s" % tokens)
    # print tokens["bus1"]
    # print tokens["bus2"]

    pu_check = lambda x: dec_check(x, Decimal("-5.0"), Decimal("5.0"))
    for x in "pf qf pl ql".split():
        ensure(pu_check(tokens[x]), "error : \n%s" % tokens)
    ensure(1 <= tokens["linenum"] <= 1000, "error : \n%s" % tokens)

def process_summary(tokens):
    # print("Summary : %s" % tokens)

    inrange = lambda x: dec_check(x, Decimal("0.0"), Decimal("100.0"))
    for x in range(4):
        ensure(inrange(x), "error : \n%s" % tokens)

    ensure(dec_check(tokens[4], Decimal("-10.0"), Decimal("10.0")), "error : \n%s" % tokens)
    ensure(dec_check(tokens[5], Decimal("-10.0"), Decimal("10.0")), "error : \n%s" % tokens)

def process_limits(tokens):
    # print("Limits : %s" % tokens)
    pass

# parse_stream(open("psat_outage0_01.txt"))
