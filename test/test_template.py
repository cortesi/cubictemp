#!/usr/local/bin/python

import glob, sys, os.path
import pylid
import cubictemp

class uBasic(pylid.TestCase):
    def test_simple(self):
        test = "@!1!@"
        ct = cubictemp.Temp(test)
        self.failUnless(str(ct) == "1")

    def test_simple2(self):
        test = "@!a!@"
        ns = {"a": 1}
        ct = cubictemp.Temp(test, **ns)
        self.failUnless(str(ct) == "1")


class TemplateTester(pylid.TestCase):
    def _run(self, filename):
        nsDict = {}
        try:
            execfile(filename + ".py", {}, nsDict)
            nsDict = nsDict["mdict"]
        except IOError:
            pass
        return str(cubictemp.File(filename + ".test", **nsDict))


class uTemplate(TemplateTester):
    PREFIX = "ptests"
    def _run(self, filename):
        filename = os.path.join(self.PREFIX, filename)
        mtemp = TemplateTester._run(self, filename)
        out = open(filename + ".out", "r").read().split()
        
        mout = mtemp.split()
        if not mout == out:
            print "Expected output:"
            print "-------"
            print out
            print "-------"
            print "Actual output:"
            print "-------"
            print mout
            print "-------"
            self.fail("Actual output does not match expected output")

    def test_if(self):
        self._run("if")

    def test_block(self):
        self._run("block")

    def test_commonuse(self):
        self._run("commonuse")

    def test_nested(self):
        self._run("nested")

    def test_repeat(self):
        self._run("repeat")

    def test_simple(self):
        self._run("simple")


class uErrors(TemplateTester):
    PREFIX = "ntests"
    def _run(self, filename):
        filename = os.path.join(self.PREFIX, filename)
        try:
            TemplateTester._run(self, filename)
        except cubictemp.TempException, value:
            pass
        else:
            self.fail("No exception on test case %s.\n" % (filename))
        
    def test_blockLine(self):
        self._run("blockLine")

    def test_ifundefined(self):
        self._run("ifundefined")

    def test_loopsyntax(self):
        self._run("loopsyntax")

    def test_loopundefined(self):
        self._run("loopundefined")

    def test_noniterable(self):
        self._run("noniterable")

    def test_syntax(self):
        self._run("syntax")

    def test_undefined(self):
        self._run("undefined")


class uQuoting(TemplateTester):
    PREFIX = "qtests"
    def _run(self, filename):
        filename = os.path.join(self.PREFIX, filename)
        output = TemplateTester._run(self, filename)
        if (output.find("<") >= 0): self.fail()
        if (output.find(">") >= 0): self.fail()
        
    def test_commonuse(self):
        self._run("commonuse")


class uNonQuoting(TemplateTester):
    PREFIX = "nqtests"
    def _run(self, filename):
        filename = os.path.join(self.PREFIX, filename)
        output = TemplateTester._run(self, filename)
        if (output.find("<") < 0): self.fail()
        if (output.find(">") < 0): self.fail()
        
    def test_commonuse(self):
        self._run("object")

    def test_tag(self):
        self._run("tag")
