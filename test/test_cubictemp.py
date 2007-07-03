import pylid
import cubictemp

def dummyproc(s):
    return "::%s::"%s


class uTempException(pylid.TestCase):
    def setUp(self):
        self.s = cubictemp.Temp("text")
        self.t = cubictemp.TempException("foo", 0, self.s)

    def test_getLines(self):
        txt = """
           one
           two
           three
        """
        x = txt.find("one")
        i, ctx = self.t._getLines(txt, x, 1)
        assert i == 2
        assert len(ctx) == 4
        assert ctx[1].strip() == "one"

        x = txt.find("three")
        i, ctx = self.t._getLines(txt, x, 2)
        assert i == 4
        assert len(ctx) == 5

    def test_format(self):
        s = """
            <!--(block foo)-->
                @!foo!@
            <!--(end)-->
            @![!@
            <!--(block bar)-->
                @!foo!@
            <!--(end)-->
        """
        self.failWith("line 5", cubictemp.Temp, s)


class u_Expression(pylid.TestCase):
    def setUp(self):
        self.s = cubictemp.Temp("text")

    def test_call(self):
        e = cubictemp._Expression("foo", "@", 0, self.s, {})
        assert e(foo="bar") == "bar"

    def test_block(self):
        e = cubictemp._Expression("foo", "@", 0, self.s, {})
        t = cubictemp._Block(None, 0, self.s, {})
        t.append(cubictemp._Text("bar"))
        assert e(foo=t) == "bar"

    def test_syntaxerr(self):
        self.failWith(
            "invalid expression",
            cubictemp._Expression,
            "for x", "@",
            0, self.s, {}
        )

    def test_namerr(self):
        e = cubictemp._Expression("foo", "@", 0, self.s, {})
        self.failWith(
            "NameError",
            e,
        )

    def test_escaping(self):
        e = cubictemp._Expression(
            "foo", "@",
            0, "foo", {}
        )
        f = e(foo="<>")
        assert "&lt;" in f
        assert not "<" in f
        assert not ">" in f

    def test_unescaped(self):
        class T:
            _cubictemp_unescaped = True
            def __str__(self):
                return "<>"
        t = T()
        e = cubictemp._Expression("foo", "@", 0, "foo", {})
        f = e(foo=t)
        assert "<" in f
        assert ">" in f


class uText(pylid.TestCase):
    def test_call(self):
        t = cubictemp._Text("foo")
        assert t() == "foo"
        

class uBlock(pylid.TestCase):
    def setUp(self):
        self.s = cubictemp.Temp("text")

    def test_call(self):
        t = cubictemp._Block(None, 0, self.s, {})
        t.append(cubictemp._Text("bar"))
        assert t() == "bar"

    def test_processor(self):
        t = cubictemp._Block("dummyproc", 0, self.s, {})
        t.append(cubictemp._Text("foo"))
        assert t(dummyproc=dummyproc) == "::foo::"


class uIterable(pylid.TestCase):
    def test_call(self):
        t = cubictemp._Iterable("foo", "bar", 0, "foo", {})
        t.append(cubictemp._Expression("bar", "@", 0, "foo", {}))
        assert t(foo=[1, 2, 3]) == "123"


class uTemp(pylid.TestCase):
    def setUp(self):
        self.s = """
            <!--(block foo)-->
                <!--(block foo)-->
                    <!--(for i in [1, 2, 3])-->
                        @!tag!@
                    <!--(end)-->
                <!--(end)-->
                @!foo!@
            <!--(end)-->
            @!foo!@
            one
        """

    def test_init(self):
        c = cubictemp.Temp(self.s).block
        assert len(c) == 4
        assert not c[0].txt.strip()
        assert not c[1].txt.strip()
        assert c[2].expr == "foo"
        assert c[3].txt.strip() == "one"

        assert c.ns["foo"]
        nest = c.ns["foo"].ns["foo"]
        assert len(nest) == 3

        assert nest[1].iterable == "[1, 2, 3]"
        assert nest[1][1].expr == "tag"

    def test_str(self):
        s = str(cubictemp.Temp("foo"))
        assert s == "foo"

    def test_call(self):
        s = cubictemp.Temp(self.s)(tag="voing")
        assert "voing" in s

    def test_unbalanced(self):
        s = """
            <!--(end)-->
            @!foo!@
            <!--(end)-->
            @!foo!@
            one
        """
        self.failWith("unbalanced block", cubictemp.Temp, s)

    def test_complexIterable(self):
        s = """
            <!--(for i in [1, 2, 3, "flibble", range(10)])-->
                @!i!@
            <!--(end)-->
        """
        s = str(cubictemp.Temp(s))
        assert "[0, 1, 2, 3, 4" in s

    def test_simpleproc(self):
        s = """
            <!--(block foo | dummyproc)-->one<!--(end)-->
            @!foo!@
        """
        t = cubictemp.Temp(s)
        assert "::one::" in t(dummyproc=dummyproc)

    def test_inlineproc(self):
        s = """
            <!--(block | dummyproc)-->one<!--(end)-->
        """
        t = cubictemp.Temp(s)
        assert "::one::" in t(dummyproc=dummyproc)

    def test_namespace_err(self):
        s = """
            @!one!@
            <!--(block one)-->one<!--(end)-->
        """
        t = cubictemp.Temp(s)
        self.failWith("not defined", t)

    def test_namespace_follow(self):
        s = """
            <!--(block one)-->one<!--(end)-->
            @!one!@
        """
        t = cubictemp.Temp(s)
        assert t().strip() == "one"

    def test_namespace_follow(self):
        s = """
            <!--(block one)-->one<!--(end)-->
            @!one!@
            <!--(block one)-->two<!--(end)-->
            @!one!@
        """
        t = str(cubictemp.Temp(s))
        assert "one" in t
        assert "two" in t

    def test_namespace_nest(self):
        s = """
            <!--(block one)-->foo<!--(end)-->
            <!--(block one)-->
                <!--(block two)-->
                    @!one!@
                <!--(end)-->
                @!two!@
            <!--(end)-->
            @!one!@
            <!--(block one)-->bar<!--(end)-->
            @!one!@
        """
        t = str(cubictemp.Temp(s))
        assert "foo" in t
        assert "bar" in t



