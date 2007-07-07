#!/usr/bin/env python
import time, sys
sys.path.insert(0, "..")
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
    <!--(for i in range(10))
        <!--(block foo)
            @!one!@
        (end)-->
        @!foo(one="<%s>"%i)!@ @!dict(one="<%s>"%i)!@
        @!foo(one="<%s>"%i)!@ @!dict(one="<%s>"%i)!@
        @!foo(one="<%s>"%i)!@
    (end)-->
    @!1!@
    @!1!@
    @!1!@
    @!1!@
    @!1!@
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

def main():
    start = time.time()
    t = cubictemp.Template(tmpl)
    for i in range(1000):
        str(t)
    stop = time.time()
    print stop-start

def profile():
    import cProfile, pstats
    p = cProfile.Profile()
    p.run("main()")
    s = pstats.Stats(p).strip_dirs().sort_stats("time")
    s.print_stats()

if __name__ == "__main__":
    main()
