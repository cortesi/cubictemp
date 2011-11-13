import string, os, os.path, time
import libpry
import cubictemp

def dummyproc(s):
    return "::%s::"%s


def dummyproc2(s):
    return "**%s**"%s


class u_Processor(libpry.AutoTree):
    def test_procs(self):
        p = cubictemp._Processor() | dummyproc
        assert p("foo") == "::foo::"

    def test_procs_chain(self):
        p = cubictemp._Processor()
        p = p | dummyproc | dummyproc2
        s = p("foo")
        assert s == "**::foo::**"

        p = cubictemp._Processor()
        p = p | dummyproc2 | dummyproc
        s = p("foo")
        assert s == "::**foo**::"


class uTemplateError(libpry.AutoTree):
    def setUp(self):
        self.s = cubictemp.Template("text")
        self.t = cubictemp.TemplateError("foo", 0, self.s)

    def test_getLines(self):
        txt = """
           one
           two
           three
        """
        x = txt.find("one")
        i, ctx = self.t._getLines(txt, x)
        assert i == 2
        lines = ctx.splitlines()
        assert len(lines) == 5
        assert lines[1].strip() == "one"

        x = txt.find("three")
        i, ctx = self.t._getLines(txt, x)
        assert i == 4
        lines = ctx.splitlines()
        assert len(lines) == 5

    def test_format_compiletime(self):
        s = """
            <!--(block foo)-->
                @!foo!@
            <!--(end)-->
            @![!@
            <!--(block barbar)-->
                @!foo!@
            <!--(end)-->
        """
        libpry.raises("line 5", cubictemp.Template, s)


        s = """
            @![!@
        """
        libpry.raises("line 2", cubictemp.Template, s)

        s = """
            <!--(block foo)-->
                @!]!@
            <!--(end)-->
            @!foo!@
        """
        libpry.raises("line 3", cubictemp.Template, s)

        s = "@!]!@"
        libpry.raises("line 1", cubictemp.Template, s)

    def test_format_execution(self):
        s = """
            <!--(block foo)-->
                @!bar!@
            <!--(end)-->
            @!foo!@
        """
        libpry.raises("line 3", unicode, cubictemp.Template(s))


class u_Expression(libpry.AutoTree):
    def setUp(self):
        self.s = cubictemp.Template("text")

    def test_render(self):
        e = cubictemp._Expression("foo", "@", 0, self.s, {})
        assert e.render(foo="bar") == "bar"

    def test_block(self):
        e = cubictemp._Expression("foo", "@", 0, self.s, {})
        t = cubictemp._Block(None, 0, self.s, {})
        t.append(cubictemp._Text("bar"))
        assert e.render(foo=t) == "bar"

    def test_syntaxerr(self):
        libpry.raises(
            "invalid expression",
            cubictemp._Expression,
            "for x", "@",
            0, self.s, {}
        )

    def test_namerr(self):
        e = cubictemp._Expression("foo", "@", 0, self.s, {})
        libpry.raises(
            "NameError",
            e.render,
        )

    def test_escaping(self):
        e = cubictemp._Expression(
            "foo", "@",
            0, "foo", {}
        )
        f = e.render(foo="<>")
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
        f = e.render(foo=t)
        assert "<" in f
        assert ">" in f


class uText(libpry.AutoTree):
    def test_render(self):
        t = cubictemp._Text("foo")
        assert t.render() == "foo"


class uBlock(libpry.AutoTree):
    def setUp(self):
        self.s = cubictemp.Template("text")

    def test_render(self):
        t = cubictemp._Block(None, 0, self.s, {})
        t.append(cubictemp._Text("bar"))
        assert t.render() == "bar"

    def test_processor(self):
        t = cubictemp._Block("dummyproc", 0, self.s, {})
        t.append(cubictemp._Text("foo"))
        assert t.render(dummyproc=dummyproc) == "::foo::"


class uIterable(libpry.AutoTree):
    def test_call(self):
        t = cubictemp._Iterable("foo", "bar", 0, "foo", {})
        t.append(cubictemp._Expression("bar", "@", 0, "foo", {}))
        assert t.render(foo=[1, 2, 3]) == "123"


class uTemplate(libpry.AutoTree):
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
        c = cubictemp.Template(self.s).block
        assert len(c) == 4
        assert not c[0].txt.strip()
        assert not c[1].txt.strip()
        assert c[2].expr == "foo"
        assert c[3].txt.strip() == "one"

        assert c.ns["foo"]
        nest = c.ns["foo"].ns["foo"]
        assert len(nest) == 1

        assert nest[0].iterable == "[1, 2, 3]"
        assert nest[0][1].expr == "tag"

    def test_unicode(self):
        s = unicode(cubictemp.Template(u"\ue2e2foo"))
        assert s == u"\ue2e2foo"

        s = cubictemp.Template("@!foo!@")
        assert unicode(s(foo=u"\ue2e2"))

        s = cubictemp.Template(u"""
                <!--(for i in uc)-->
                    @!i!@
                <!--(end)-->
            """)
        assert unicode(s(uc=[u"\ue2e2"]))

    def test_call(self):
        s = cubictemp.Template(self.s)(tag="voing")
        assert "voing" in unicode(s)

    def test_unbalanced(self):
        s = """
            <!--(end)-->
            @!foo!@
            <!--(end)-->
            @!foo!@
            one
        """
        libpry.raises("unbalanced block", cubictemp.Template, s)

    def test_complexIterable(self):
        s = """
            <!--(for i in [1, 2, 3, "flibble", range(10)])-->
                @!i!@
            <!--(end)-->
        """
        s = unicode(cubictemp.Template(s))
        assert "[0, 1, 2, 3, 4" in s

    def test_simpleproc(self):
        s = """
            <!--(block foo | strip | dummyproc)-->
                one
            <!--(end)-->
            @!foo!@
        """
        t = cubictemp.Template(s, strip=string.strip)
        assert "::one::" in unicode(t(dummyproc=dummyproc))

    def test_inlineproc(self):
        s = """
            <!--(block | strip | dummyproc)-->
                one
            <!--(end)-->
        """
        t = cubictemp.Template(s, strip=string.strip)
        assert "::one::" in unicode(t(dummyproc=dummyproc))

    def test_namespace_err(self):
        s = """
            @!one!@
        """
        t = cubictemp.Template(s)
        libpry.raises("not defined", unicode, t)

    def test_namespace_simplenest(self):
        s = """
            <!--(block one)-->
                @!two!@
                @!three!@
            <!--(end)-->
            @!one(three="bar")!@
        """
        t = cubictemp.Template(s)
        assert "foo" in unicode(t(two="foo"))

    def test_namespace_follow(self):
        s = """
            <!--(block one)-->
                one
            <!--(end)-->
            @!one!@
        """
        t = cubictemp.Template(s)
        assert t().strip() == "one"

    def test_namespace_follow(self):
        s = """
            <!--(block one)-->
                one
            <!--(end)-->
            @!one!@
            <!--(block one)-->
                two
            <!--(end)-->
            @!one!@
        """
        t = unicode(cubictemp.Template(s))
        assert "one" in t
        assert "two" in t

    def test_namespace_nest(self):
        s = """
            <!--(block one)-->
                foo
            <!--(end)-->
            <!--(block one)-->
                <!--(block two)-->
                    @!one!@
                <!--(end)-->
                @!two!@
            <!--(end)-->
            @!one!@
            <!--(block one)-->
                bar
            <!--(end)-->
            @!one!@
        """
        t = unicode(cubictemp.Template(s))
        assert "foo" in t
        assert "bar" in t

    def test_blockspacing(self):
        s = """
            <!--(block|strip|dummyproc)-->
                one
            <!--(end)-->
        """
        t = cubictemp.Template(s, strip=string.strip)
        assert unicode(t(dummyproc=dummyproc)).strip() == "::one::"

    def test_block_following_whitespace(self):
        s = """
            <!--(block|dummyproc)-->
                one
            <!--(end)-->


            test
        """
        t = cubictemp.Template(s, strip=string.strip)
        assert "\n\n" in unicode(t(dummyproc=dummyproc))

    def test_processorchain(self):
        s = """
            <!--(block|strip|dummyproc|dummyproc2)-->
                one
            <!--(end)-->
        """
        t = cubictemp.Template(s, strip=string.strip, dummyproc2=dummyproc2)
        assert unicode(t(dummyproc=dummyproc)).strip() == "**::one::**"

    def test_lines(self):
        s = """
            :<!--(block foo)-->
                one
            :<!--(end)-->
        """
        t = cubictemp.Template(s)
        s = t()
        assert ":<!" in unicode(s)


class uFile(libpry.AutoTree):
    def test_unicode(self):
        d = self.tmpdir()
        p = os.path.join(d, "test")
        f = open(p, "wb")
        f.write(u"\u1234@!a!@\u1111".encode("utf8"))
        f.close()
        tf = cubictemp.File(p, a="\u1234foo")
        assert unicode(tf)



class uFileWatcher(libpry.AutoTree):
    def test_update(self):
        d = self.tmpdir()
        p = os.path.join(d, "test")

        f = open(p, "w")
        f.write("foo")
        f.close()
        w = cubictemp.FileWatcher(p)
        assert unicode(w) == "foo"
        assert unicode(w()) == "foo"
        time.sleep(1)
        f = open(p, "w")
        f.write("bar")
        f.close()
        assert unicode(w) == "bar"
        assert unicode(w()) == "bar"
        assert w.raw() == "bar"


tests = [
    u_Processor(),
    uTemplateError(),
    u_Expression(),
    uText(),
    uBlock(),
    uIterable(),
    uTemplate(),
    uFileWatcher(),
    uFile()
]
