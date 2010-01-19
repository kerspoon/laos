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
 
""" Package info:
James Brooks (kerspoon)

Misc utilities. 
"""

#------------------------------------------------------------------------------
# Imports:
#------------------------------------------------------------------------------

import sys
import os
import re 
import logging
import itertools

#------------------------------------------------------------------------------
# Logging:
#------------------------------------------------------------------------------
 
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
    format="%(levelname)s: %(message)s")
 
logger = logging.getLogger(__name__)

#------------------------------------------------------------------------------
# Grem: regexp file deleter
#------------------------------------------------------------------------------

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

#------------------------------------------------------------------------------
# splitEvery
#------------------------------------------------------------------------------

def splitEvery(n, iterable):
    """
    splitEvery :: Int -> [e] -> [[e]]
    @'splitEvery' n@ splits a list into length-n pieces.  The last
    piece will be shorter if @n@ does not evenly divide the length of
    the list.
    from: http://stackoverflow.com/questions/1915170#1915307
    """
    i = iter(iterable)
    piece = list(itertools.islice(i, n))
    while piece:
        yield piece
        piece = list(itertools.islice(i, n))

def TEST_splitEvery():
    # should not enter infinite loop with generators and lists
    splitEvery(itertools.count(), 10)
    splitEvery(range(1000), 10)

    # last piece must be shorter if n does not evenly divide
    assert list(splitEvery(5, range(9))) == [[0, 1, 2, 3, 4], [5, 6, 7, 8]]

    # should give same correct results with generators
    tmp = itertools.islice(itertools.count(), 9)
    assert list(splitEvery(5, tmp)) == [[0, 1, 2, 3, 4], [5, 6, 7, 8]]

    # should work with empty list. 
    assert list(splitEvery(100, [])) == []
# TEST_splitEvery()

#------------------------------------------------------------------------------
#  as_csv :: [T], str -> str
#------------------------------------------------------------------------------
def as_csv(iterable, sep = "  "):
    """a string of each item seperated by 'sep'"""
    iterable = list(iterable)
    res = ""
    if len(iterable) == 0:
        return ""
    for item in iterable[:-1]:
        res += str(item) + sep
    return res + str(iterable[len(iterable)-1])

#------------------------------------------------------------------------------
#  struct:
#------------------------------------------------------------------------------
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

        assert "entries" in dir(self)

        if "types" in dir(self):
            assert(len(self.entries) == len(self.types))

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
                raise Exception("bad datatype. expected (int, real, bool, str) got " + self.typemap[member])

    def check_entries(self):
        """make sure that all the entries are added"""
        for member in self.entries:
            assert member in dir(self), str(member) + " not added"

def read_struct(class_type, cols):
    """read a list of strings as the data for 'class_type'
       e.g. read_struct(Bus, "101 0.025 13".split())
       This should return a Bus with all data filled in.
    """
    assert len(class_type.entries) == len(cols), "incomplete info. got " + str(cols)
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
