#! /usr/local/bin/python
# psat_report.parse_stream(open(psat_01.txt))
 
from pyparsing import *
from decimal import Decimal
import string
import logging
import sys

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
    # print data

def GetHeaders():
    title = Group(Optional(Literal("OPTIMAL")) + Literal("POWER FLOW REPORT"))
    title.setParseAction(process_header_title)
    version = Literal("P S A T  2.1.5").suppress()
    author = Literal("Author:  Federico Milano, (c) 2002-2009").suppress()
    email = Literal("e-mail:  Federico.Milano@uclm.es").suppress()
    website = Literal("website: http://www.uclm.es/area/gsee/Web/Federico").suppress()
    filename = Literal("File:").suppress() + restOfLine.suppress()
    date = Literal("Date:").suppress() + restOfLine.suppress()

    return title + version + author + email + website + filename + date

def GetStats():
    ntitle = Literal("NETWORK STATISTICS")
    buses = Literal("Buses:") + integer.setResultsName("buses")
    lines = Literal("Lines:") + integer.setResultsName("lines")
    transformers = Literal("Transformers:") + integer.setResultsName("transformers")
    generators = Literal("Generators:") + integer.setResultsName("generators")
    loads = Literal("Loads:") + integer.setResultsName("loads")
    ngroup = Group(ntitle + buses + lines + transformers + generators + loads)
    
    stitle = Literal("SOLUTION STATISTICS")
    iterations = Literal("Number of Iterations:") + integer.setResultsName("iterations")
    pmismatch = Literal("Maximum P mismatch [p.u.]   ") + decimal.setResultsName("pmis")
    qmismatch = Literal("Maximum Q mismatch [p.u.]") + decimal.setResultsName("qmis")
    rate = Literal("Power rate [MVA]") + decimal.setResultsName("rate")
    sgroup = Group(stitle + iterations + pmismatch + qmismatch + rate)

    return (ngroup + sgroup).setParseAction(process_stats)

def GetPflow():
    title = Literal("POWER FLOW RESULTS")
    head1 = stringtolits("Bus V phase P gen Q gen P load Q load")
    head2 = stringtolits("[p.u.] [rad] [p.u.] [p.u.] [p.u.] [p.u.]")

    busdef = busname + decimaltable("v phase pg qg pl ql".split())

    buses = OneOrMore(busdef.setParseAction(process_pflow_bus))

    limline = Literal("Maximum voltage at bus <") + busname + Literal(">")

    limits = OneOrMore(limline.setParseAction(process_pflow_line))

    return title + head1 + head2 + buses + limits

def GetLineflow():
    title = Literal("LINE FLOWS")
    head1 = stringtolits("From Bus To Bus Line P Flow Q Flow P Loss Q Loss")
    head2 = stringtolits("[p.u.] [p.u.] [p.u.] [p.u.]")
    
    busdef = And([busname, 
                  busname,
                  integer.setResultsName("linenum"),
                  decimaltable("pf qf pl ql".split())])

    busdef = busdef.setParseAction(process_lineflow_bus)
    buses = OneOrMore(busdef)

    lineflow = title + head1 + head2 + buses

    return lineflow + lineflow

def GetSummary():
    title = Literal("GLOBAL SUMMARY REPORT")

    real = Literal("REAL POWER [p.u.]") + decimal
    react = Literal("REACTIVE POWER [p.u.]") + decimal

    totalgen = Literal("TOTAL GENERATION") + real + react
    totalload = Literal("TOTAL LOAD") + real + react
    totalloss = Literal("TOTAL LOSSES") + real + react
    
    return (title + totalgen + totalload + totalloss).setParseAction(process_summary)

def GetLimits():
    title = Literal("LIMIT VIOLATION STATISTICS")

    volt = Literal("ALL VOLTAGES WITHIN LIMITS") + restOfLine.suppress()
    react = Literal("ALL REACTIVE POWER WITHIN LIMITS") + restOfLine.suppress()
    current = Literal("ALL CURRENT FLOWS WITHIN LIMITS") + restOfLine.suppress()
    real = Literal("ALL REAL POWER FLOWS WITHIN LIMITS") + restOfLine.suppress()
    apparent = Literal("ALL APPARENT POWER FLOWS WITHIN LIMITS") + restOfLine.suppress()

    return (title + volt + react + current + real + apparent).setParseAction(process_limits)

def process_header_title(tokens):
    print("Header : %s" % tokens)

def process_stats(tokens):
    print("Stats : %s" % tokens)

def process_pflow_bus(tokens):
    print("Bus Power Flow : %s" % tokens)

def process_pflow_line(tokens):
    print("Line Power Flow : %s" % tokens)

def process_lineflow_bus(tokens):
    print("Bus Line Flow : %s" % tokens)

def process_summary(tokens):
    print("Summary : %s" % tokens)

def process_limits(tokens):
    print("Limits : %s" % tokens)

