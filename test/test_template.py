#!/usr/local/bin/python
import glob, sys, os.path
import libpry
import cubictemp

class uBasic(libpry.AutoTree):
    def test_simple(self):
        test = "@!1!@"
        ct = cubictemp.Template(test)
        assert unicode(ct) == "1"

    def test_simple2(self):
        test = "@!a!@"
        ns = {"a": 1}
        ct = cubictemp.Template(test, **ns)
        assert unicode(ct) == "1"


class TemplateTester(libpry.AutoTree):
    def _runTemp(self, filename, nsDict):
        return unicode(cubictemp.File(filename + ".test", **nsDict))


class uTemplate(TemplateTester):
    PREFIX = "ptests"
    def _runTemp(self, filename, nsDict={}):
        filename = os.path.join(self.PREFIX, filename)
        mtemp = TemplateTester._runTemp(self, filename, nsDict)
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
            raise AssertionError("Actual output does not match expected output")

    def test_if(self):
        self._runTemp("if")

    def test_block(self):
        ns = {
            "bar": "rab",
        }
        self._runTemp("block", ns)

    def test_commonuse(self):
        ns = {
             "foo": open("ptests/commonuse.data")
        }
        self._runTemp("commonuse", ns)

    def test_nested(self):
        self._runTemp("nested")

    def test_repeat(self):
        self._runTemp("repeat")

    def test_simple(self):
        ns = {
            "foo": "one",
            "bar": "two",
            "boo": u"three",
            "mdict": {"entry": "foo"}
        }
        self._runTemp("simple", ns)


class uErrors(TemplateTester):
    PREFIX = "ntests"
    def _runTemp(self, filename, err):
        filename = os.path.join(self.PREFIX, filename)
        libpry.raises(err, TemplateTester._runTemp, self, filename, {})

    def test_blockLine(self):
        self._runTemp("blockLine", "'a' is not defined")

    def test_ifundefined(self):
        self._runTemp("ifundefined", "'a' is not defined")

    def test_loopsyntax(self):
        self._runTemp("loopsyntax", "invalid expression")

    def test_loopundefined(self):
        self._runTemp("loopundefined", "'a' is not defined")

    def test_noniterable(self):
        self._runTemp("noniterable", "can not iterate")

    def test_syntax(self):
        self._runTemp("syntax", "invalid expression")

    def test_undefined(self):
        self._runTemp("undefined", "'foo' is not defined")


class uQuoting(TemplateTester):
    PREFIX = "qtests"
    def _runTemp(self, filename, nsDict={}):
        filename = os.path.join(self.PREFIX, filename)
        output = TemplateTester._runTemp(self, filename, nsDict)
        if (output.find("<") >= 0): raise AssertionError()
        if (output.find(">") >= 0): raise AssertionError()

    def test_commonuse(self):
        class Dummy:
            def __repr__(self):
                return "<foo>"

        mdict = {
            "foo":      "<foinkle>",
            "object":   Dummy()
        }
        self._runTemp("commonuse", mdict)


class uNonQuoting(TemplateTester):
    PREFIX = "nqtests"
    def _runTemp(self, filename, nsDict):
        filename = os.path.join(self.PREFIX, filename)
        output = TemplateTester._runTemp(self, filename, nsDict)
        if (output.find("<") < 0): raise AssertionError()
        if (output.find(">") < 0): raise AssertionError()

    def test_commonuse(self):
        class Dummy:
            _cubictemp_unescaped = 1
            def __repr__(self):
                return "<foo>"

        mdict = {
            "object":   Dummy()
        }
        self._runTemp("object", mdict)

    def test_tag(self):
        mdict = {
            "tag":   "<foo>"
        }
        self._runTemp("tag", mdict)


tests = [
    uBasic(),
    uTemplate(),
    uErrors(),
    uQuoting(),
    uNonQuoting(),
]
