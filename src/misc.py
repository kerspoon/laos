#! /usr/local/bin/python

 
#==============================================================================
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
#==============================================================================
 
""" Package info:
James Brooks (kerspoon)

Misc utilities. 
"""

#==============================================================================
# Imports:
#==============================================================================

import sys
import re 
import os
import logging
import itertools
import traceback
from collections import defaultdict

#==============================================================================
# Logging:
#==============================================================================
 
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
    format="%(levelname)s: %(message)s")
 
logger = logging.getLogger(__name__)

#==============================================================================
# Grem: regexp file deleter
#==============================================================================

def grem(path, pattern, test=False):
    """remove all folders/files in 'path' thatmatches the 
       regexp 'pattern'. test prints out names only.

       <http://docs.python.org/library/re.html>
       it's highly recommended that you use raw strings for 
       all but the simplest expressions.
    """
    pattern = re.compile(pattern)
    for each in os.listdir(path):
        if pattern.search(each):
            name = os.path.join(path, each)
            try:
                if not test: os.remove(name)
                # logger.info("Grem removed " + name)
            except:
                if not test: 
                    grem(name, '')
                    os.rmdir(name)
                # logger.info("Grem removed dir " + name)

def test_grem():
    grem(".", r".*\.pyc", True)
    grem(".", r"rts_[1234567890]{2}\.txt", True)
# test_grem()        

#==============================================================================
# split_every
#==============================================================================

def split_every(n, iterable):
    """
    split_every :: Int -> [e] -> [[e]]
    @'split_every' n@ splits a list into length-n pieces.  The last
    piece will be shorter if @n@ does not evenly divide the length of
    the list.
    from: http://stackoverflow.com/questions/1915170#1915307
    """
    i = iter(iterable)
    piece = list(itertools.islice(i, n))
    while piece:
        yield piece
        piece = list(itertools.islice(i, n))

def TEST_split_every():
    # should not enter infinite loop with generators and lists
    split_every(itertools.count(), 10)
    split_every(range(1000), 10)

    # last piece must be shorter if n does not evenly divide
    assert list(split_every(5, range(9))) == [[0, 1, 2, 3, 4], [5, 6, 7, 8]]

    # should give same correct results with generators
    tmp = itertools.islice(itertools.count(), 9)
    assert list(split_every(5, tmp)) == [[0, 1, 2, 3, 4], [5, 6, 7, 8]]

    # should work with empty list. 
    assert list(split_every(100, [])) == []
# TEST_split_every()


#==============================================================================
# duplicates_exist
#==============================================================================

def duplicates_exist(iterable):
    """
    duplicates_exist [x] -> Bool
    Are there two or more elements in this list that are equal?
    could sort then compare adjacent or by building a count of elements and 
    making sure that count is all 1.
    """

    tally = defaultdict(int)
    for x in iterable:
        tally[x] += 1

    return not all(count == 1 for count in tally.values()) 


def TEST_duplicates_exist():
    assert duplicates_exist([0, 1, 2, 3]) == False
    assert duplicates_exist([2, 1, 2, 3]) == True
    assert duplicates_exist([1, 1, 2, 3]) == True
    assert duplicates_exist([1, 1, 1, 1]) == True
    assert duplicates_exist([-4, 8, 2, 7]) == False
# TEST_duplicates_exist()


#==============================================================================
#  as_csv :: [T], str -> str
#==============================================================================
def as_csv(iterable, sep="  "):
    """a string of each item seperated by 'sep'"""
    return sep.join(str(x) for x in list(iterable))

def TEST_as_csv():
    assert as_csv([1, 2, 3], ", ") == "1, 2, 3"
    assert as_csv([1], "abc") == "1"
    assert as_csv(xrange(5), "_") == "0_1_2_3_4"
# TEST_as_csv()

#==============================================================================
#  struct:
#==============================================================================
class struct(object):
    """
        e.g. a simple use of the struct class:

            class Bus(struct):
                entries = "bus_id fail_rate repair_rate".split()
                types = "int real real".split()

            bus = read_struct(Bus, "101 0.025 13".split())

            assert bus.bus_id == 101
            assert abs(bus.fail_rate - 0.025) > 0.0001
            assert abs(bus.repair_rate - 13) > 0.0001
            assert str(bus) == "101 0.025 13"
    """

    def __init__(self, tokens=None):
        """if we are given tokens (a dict of entries) then fill them in
           and check we have filled all of them. 
           if we have self.types convert all entries to correct type
        """

        EnsureIn("entries", dir(self), "structs must have `entries`")

        if "types" in dir(self):
            EnsureEqual(len(self.entries), len(self.types))

        if tokens:
            self.dict_fill(tokens)
            self.check_entries()
            
            if "types" in dir(self):
                self.convert_types()

    def __str__(self):
        """a simple space seperated string with entries in the 
           same order as 'entries'
        """
        return as_csv([self.__dict__[x] for x in self.entries], " ")

    def dict_fill(self, kwds):
        """fill in all 'entries' using the dict 'kwds'"""
        self.__dict__.update(kwds)

    def convert_types(self):
        """convert all entries into the proper types using self.types"""

        self.typemap = dict(zip(self.entries, self.types))

        # typemap = {'bus_id':'int',
        #            'fail_rate':'real',
        #            'repair_rate':'real'}

        for member in self.entries:
            if self.typemap[member] == "int":
                self.__dict__[member] = int(self.__dict__[member])
            elif self.typemap[member] == "real":
                self.__dict__[member] = float(self.__dict__[member])
            elif self.typemap[member] == "bool":
                self.__dict__[member] = bool(self.__dict__[member])
            elif self.typemap[member] == "str":
                self.__dict__[member] = str(self.__dict__[member])
            else:
                raise Error("bad datatype. expected (int, real, bool, str) got " + 
                                self.typemap[member])

    def check_entries(self):
        """make sure that all the entries are added"""
        for member in self.entries:
            EnsureIn(member, dir(self), "entry not added")

def read_struct(class_type, cols):
    """read a list of strings as the data for 'class_type'
       e.g. read_struct(Bus, "101 0.025 13".split())
       This should return a Bus with all data filled in.
    """
    EnsureEqual(len(class_type.entries), len(cols), "incomplete info. got " + str(cols))
    
    return class_type(dict(zip(class_type.entries, cols)))

def TEST_struct():
    class Bus(struct):
        entries = "bus_id fail_rate repair_rate".split()
        types = "int real real".split()
        
    bus = read_struct(Bus, "101 0.025 13".split())
    
    # print bus.bus_id
    # print bus.fail_rate
    # print bus.repair_rate
    # print bus

    assert bus.bus_id == 101
    assert abs(bus.fail_rate - 0.025) < 0.0001
    assert abs(bus.repair_rate - 13) < 0.0001
    assert str(bus) == "101 0.025 13.0"

# TEST_struct()



#==============================================================================
#  round_to:
#==============================================================================
def round_to(val, x):
    """round x to the nearest `val`
       val must be an int"""
    return int(round(x / float(val)) * val)


def TEST_round_to():
    # 10
    assert round_to(10, 0) == 0
    assert round_to(10, 1) == 0
    assert round_to(10, 4) == 0
    assert round_to(10, 5) == 10
    assert round_to(10, 6) == 10
    assert round_to(10, 10) == 10
    assert round_to(10, 15) == 20
    # 5
    assert round_to(5, 0) == 0
    assert round_to(5, 1) == 0
    assert round_to(5, 2.4) == 0
    assert round_to(5, 2.5) == 5
    assert round_to(5, 4) == 5
    assert round_to(5, 4.9) == 5
    assert round_to(5, 5) == 5
    assert round_to(5, 5.1) == 5
    assert round_to(5, 10) == 10
# TEST_round_to()



#==============================================================================
#  Exceptions
#==============================================================================

class Error(Exception):
    """Base class for exceptions in this module.

    Attributes:
        msg         -- explanation of the error

    http://stackoverflow.com/questions/894088/how-do-i-get-the-current-file-current-class-and-current-method-with-python
    http://docs.python.org/library/sys.html
    http://docs.python.org/library/traceback.html
    http://www.doughellmann.com/PyMOTW/traceback/
    http://benjamin-schweizer.de/improved-python-traceback-module.html
    """

    def __init__(self, msg, use_stack_n= -1):
        self.msg = msg
        self.stack_n = use_stack_n

    def __str__(self):
        _exc_type, _exc_value, exc_traceback = sys.exc_info() 
        stack = traceback.extract_tb(exc_traceback) # ==> [(filename, line number, function name, text)]
        file = os.path.basename(stack[self.stack_n][0]).split('.')[0]
        func = stack[self.stack_n][2]
        line = stack[self.stack_n][1]
        return "[E] Error: '%s' (%s.%s[%d])" % (self.msg, file, func, line)

def Ensure(cond, msg):
    if not cond:
        raise Error(msg, -2)

def EnsureEqual(first, second, msg=""):
    if first != second:
        raise Error("Expected '%s' = '%s' %s" % (str(first), str(second), msg), -2)
    
def EnsureNotEqual(first, second, msg=""):
    if first == second:
        if str(first) == str(second):
            raise Error("Expected Type '%s' = '%s' on '%s' %s" % (first.__class__, second.__class__, str(first), msg), -2)
        raise Error("Expected '%s' = '%s' %s" % (str(first), str(second), msg), -2)

def EnsureIn(first, second, msg=""):
    if first not in second:
        raise Error("Expected '%s' in '%s' %s" % (str(first), str(second), msg), -2)

def TEST_EnsureEqual():
    def lumberjack():
        bright_side_of_death()

    def bright_side_of_death():
        EnsureEqual(3, 5)
        
    try:
        lumberjack()
    except Exception as exc:
        print exc
