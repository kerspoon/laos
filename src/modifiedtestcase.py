#! /usr/bin/env python
import unittest
import StringIO
import random
import sys
from misc import Ensure

class ModifiedTestCase(unittest.TestCase):
    def assertRaisesEx(self, exception, callable, *args, **kwargs):
        if "exc_args" in kwargs:
            exc_args = kwargs["exc_args"]
            del kwargs["exc_args"]
        else:
            exc_args = None
        if "exc_pattern" in kwargs:
            exc_pattern = kwargs["exc_pattern"]
            del kwargs["exc_pattern"]
        else:
            exc_pattern = None

        argv = [repr(a) for a in args]\
               + ["%s=%r" % (k, v)  for k, v in kwargs.items()]
        callsig = "%s(%s)" % (callable.__name__, ", ".join(argv))

        try:
            callable(*args, **kwargs)
        except exception, exc:
            if exc_args is not None:
                self.failIf(exc.args != exc_args,
                            "%s raised %s with unexpected args: "\
                            "expected=%r, actual=%r"\
                            % (callsig, exc.__class__, exc_args, exc.args))
            if exc_pattern is not None:
                self.failUnless(exc_pattern.search(str(exc)),
                                "%s raised %s, but the exception "\
                                "does not match '%s': %r"\
                                % (callsig, exc.__class__, exc_pattern.pattern,
                                   str(exc)))
        except:
            exc_info = sys.exc_info()
            print exc_info
            self.fail("%s raised an unexpected exception type: "\
                      "expected=%s, actual=%s"\
                      % (callsig, exception, exc_info[0]))
        else:
            self.fail("%s did not raise %s" % (callsig, exception))

    def assertAlmostEqualList(self, list1, list2):
        self.assertEqual(len(list1), len(list2))
        for x, y in zip(list1, list2):
            self.assertAlmostEqual(x, y)


class ReadError(Exception):
    pass

def ReadAssert(cond, text=None):
    if not cond: 
        raise ReadError(text)

# mockfile :: str -> filehandler
def mockfile(text):
    return StringIO.StringIO(text)

# rnd_True :: Real(0,1) -> Bool
def rnd_True(_):
    return True

# rnd_False :: Real(0,1) -> Bool
def rnd_False(_):
    return False

# rnd_random :: Real(0,1) -> Bool
def rnd_random(probability):
    return random.random() > probability

# Generate_rnd_result :: [Bool] -> (Real(0,1) -> Bool)
def Generate_rnd_result(seq):
    """
    returns the sequence of Bools passed in to it
    regardless of the probability each time.
    """

    class Inner:
        def __init__(self, seq):
            for x in seq:
                Ensure(x is True or x is False, "expected Boolena got %s" % str(x))
            self.seq = seq
            self.n = 0

        def callme(self, _):
            ret = self.seq[self.n]
            self.n += 1
            return ret

    this = Inner(seq)
    return this.callme

# Generate_rnd_sequence :: [Real(0,1)] -> (Real(0,1) -> Bool)
def Generate_rnd_sequence(seq):
    """a fake random number generator, uses the input sequence as the 
    'random' numbers."""

    class Inner:
        def __init__(self, seq):
            self.seq = seq
            self.n = 0

        def callme(self, probability):
            ret = self.seq[self.n] > probability
            self.n += 1
            return ret

    this = Inner(seq)
    return this.callme

class Test_Generate_rnd_result(ModifiedTestCase):
    def test1(self):
        seq = [x == 't' for x in list("tftftttfttftffttt")]
        rnd = Generate_rnd_result(seq)
        for x in seq:
            self.assertEqual(rnd(.5), x)
    def test2(self):
        seq = [True]
        rnd = Generate_rnd_result(seq)
        self.assertEqual(rnd(.5), True)
        self.assertRaisesEx(IndexError, rnd, .5, exc_args=(("list index out of range",)))

class Test_Generate_rnd_sequence(ModifiedTestCase):

    def test1(self):
        seq = [.5]
        rnd = Generate_rnd_sequence(seq)
        for _ in range(len(seq)):
            self.assertEqual(rnd(.9), False)

    def test2(self):
        seq = [.95]
        rnd = Generate_rnd_sequence(seq)
        for _ in range(len(seq)):
            self.assertEqual(rnd(.9), True)

    def test3(self):
        seq = [x / 10.0 + 0.1 for x in range(9)]
        rnd = Generate_rnd_sequence(seq)
        for x in seq:
            self.assertEqual(rnd(0), True)

    def test4(self):
        seq = [x / 10.0 + 0.1 for x in range(9)]
        rnd = Generate_rnd_sequence(seq)
        for x in seq:
            self.assertEqual(rnd(1), False)

if __name__ == '__main__':
    unittest.main()

