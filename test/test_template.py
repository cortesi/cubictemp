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
    def _run(self, filename, nsDict):
        return str(cubictemp.File(filename + ".test", **nsDict))


class uTemplate(TemplateTester):
    PREFIX = "ptests"
    def _run(self, filename, nsDict={}):
        filename = os.path.join(self.PREFIX, filename)
        mtemp = TemplateTester._run(self, filename, nsDict)
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
        ns = {
            "bar": "rab",
        }
        self._run("block", ns)

    def test_commonuse(self):
        ns = {
             "foo": open("ptests/commonuse.data")
        }
        self._run("commonuse", ns)

    def test_nested(self):
        self._run("nested")

    def test_repeat(self):
        self._run("repeat")

    def test_simple(self):
        ns = {
            "foo": "one",
            "bar": "two",
            "boo": "three",
            "mdict": {"entry": "foo"}
        }
        self._run("simple", ns)


class uErrors(TemplateTester):
    PREFIX = "ntests"
    def _run(self, filename, err):
        filename = os.path.join(self.PREFIX, filename)
        self.failWith(err, TemplateTester._run, self, filename, {})
        
    def test_blockLine(self):
        self._run("blockLine", "'a' is not defined")

    def test_ifundefined(self):
        self._run("ifundefined", "'a' is not defined")

    def test_loopsyntax(self):
        self._run("loopsyntax", "invalid expression")

    def test_loopundefined(self):
        self._run("loopundefined", "'a' is not defined")

    def test_noniterable(self):
        self._run("noniterable", "can not iterate")

    def test_syntax(self):
        self._run("syntax", "invalid expression")

    def test_undefined(self):
        self._run("undefined", "'foo' is not defined")


class uQuoting(TemplateTester):
    PREFIX = "qtests"
    def _run(self, filename, nsDict={}):
        filename = os.path.join(self.PREFIX, filename)
        output = TemplateTester._run(self, filename, nsDict)
        if (output.find("<") >= 0): self.fail()
        if (output.find(">") >= 0): self.fail()
        
    def test_commonuse(self):
        class Dummy:
            def __repr__(self):
                return "<foo>"

        mdict = {
            "foo":      "<foinkle>",
            "object":   Dummy()
        }
        self._run("commonuse", mdict)


class uNonQuoting(TemplateTester):
    PREFIX = "nqtests"
    def _run(self, filename, nsDict):
        filename = os.path.join(self.PREFIX, filename)
        output = TemplateTester._run(self, filename, nsDict)
        if (output.find("<") < 0): self.fail()
        if (output.find(">") < 0): self.fail()
        
    def test_commonuse(self):
        class Dummy:
            _cubictemp_unescaped = 1
            def __repr__(self):
                return "<foo>"

        mdict = {
            "object":   Dummy()
        }
        self._run("object", mdict)

    def test_tag(self):
        mdict = {
            "tag":   "<foo>"
        }
        self._run("tag", mdict)
