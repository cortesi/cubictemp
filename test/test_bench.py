import libpry
import cubictemp

tmpl = """
    lorem ipsum sic dolor samet
    lorem ipsum sic dolor samet
    lorem ipsum sic dolor samet
    lorem ipsum sic dolor samet
    lorem ipsum sic dolor samet
    lorem ipsum sic dolor samet
    lorem ipsum sic dolor samet
    lorem ipsum sic dolor samet
    lorem ipsum sic dolor samet
    lorem ipsum sic dolor samet
    lorem ipsum sic dolor samet
    <!--(for i in range(1000))
        <!--(block foo)
            @!one!@
        (end)-->
        @!foo(one="<%s>"%i)!@
    (end)-->
    lorem ipsum sic dolor samet
    lorem ipsum sic dolor samet
    lorem ipsum sic dolor samet
    lorem ipsum sic dolor samet
    lorem ipsum sic dolor samet
    lorem ipsum sic dolor samet
    lorem ipsum sic dolor samet
    lorem ipsum sic dolor samet
    lorem ipsum sic dolor samet
    lorem ipsum sic dolor samet
    lorem ipsum sic dolor samet
"""

class uBench(libpry.AutoTree):
    def test_bench(self):
        t = cubictemp.Template(tmpl)
        str(t)


tests = [
    uBench()
]
