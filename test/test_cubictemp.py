import pylid
import cubictemp


class u_Expression(pylid.TestCase):
    def test_call(self):
        e = cubictemp._Expression("foo", "@", 0, "foo")
        assert e(dict(foo="bar")) == "bar"

    def test_block(self):
        e = cubictemp._Expression("foo", "@", 0, "foo")
        t = cubictemp._Block()
        t.append(cubictemp._Text("bar"))
        assert e(dict(foo=t)) == "bar"

    def test_syntaxerr(self):
        self.failWith(
            "invalid expression",
            cubictemp._Expression,
            "for x", "@",
            0, "foo"
        )

    def test_namerr(self):
        e = cubictemp._Expression("foo", "@", 0, "foo")
        self.failWith(
            "NameError",
            e,
            {}
        )

    def test_escaping(self):
        e = cubictemp._Expression(
            "foo", "@",
            0, "foo"
        )
        f = e(dict(foo="<>"))
        assert "&lt;" in f
        assert not "<" in f
        assert not ">" in f

    def test_unescaped(self):
        class T:
            _cubictemp_unescaped = True
            def __str__(self):
                return "<>"
        t = T()
        e = cubictemp._Expression("foo", "@", 0, "foo")
        f = e(dict(foo=t))
        assert "<" in f
        assert ">" in f


class uText(pylid.TestCase):
    def test_call(self):
        t = cubictemp._Text("foo")
        assert t({}) == "foo"
        

class uBlock(pylid.TestCase):
    def test_call(self):
        t = cubictemp._Block()
        t.ns["foo"] = cubictemp._Block()
        t.ns["foo"].append(cubictemp._Text("bar"))
        t.append(cubictemp._Expression("foo", "@", 0, "foo"))
        assert t.ns["foo"]({}) == "bar"
        assert t({}) == "bar"


class uIterable(pylid.TestCase):
    def test_call(self):
        t = cubictemp._Iterable("foo", "bar", 0, "foo")
        t.append(cubictemp._Expression("bar", "@", 0, "foo"))
        assert t(dict(foo=[1, 2, 3])) == "123"


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
