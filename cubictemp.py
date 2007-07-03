#!/usr/local/bin/python
import cgi, re, itertools
context = 2

class TempException(Exception):
    def __init__(self, val, pos, tmpl):
        Exception.__init__(self, val)
        self.val, self.pos, self.tmpl = val, pos, tmpl
        self.lineNo, self.context = self._getLines(tmpl.txt, pos, context)

    def _getLines(self, txt, pos, context):
        lines = txt.splitlines(True)
        cur = 0
        for i, l in enumerate(lines):
            cur += len(l)
            if cur > pos:
                break
        if i < context:
            startc = 0
        else:
            startc = i - context
        if i > (len(lines)-context):
            endc = len(lines)
        else:
            endc = i + context + 1
        return i + 1, [j.strip() for j in lines[startc:endc]]

    def __str__(self):
        ret = [
            "TempException: %s"%self.val,
            "\tContext: line %s in %s:"%(self.lineNo, self.tmpl.name),
        ]
        ret.extend(["\t\t" + i for i in self.context])
        return "\n".join(ret)



def escape(s):
    """
        Replace special characters '&', '<', '>', ''', and '"' with the
        appropriate HTML escape sequences.
    """
    s = s.replace("&", "&amp;") # Must be done first!
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace('"', "&quot;")
    s = s.replace("'", "&#39;")
    return s


def _compile(expr, pos, tmpl):
        try:
            return compile(expr, "<string>", "eval")
        except SyntaxError, value:
            s = 'Invalid expression: "%s"'%(expr)
            raise TempException(s, pos, tmpl)


class _Expression:
    def __init__(self, expr, flavor, pos, tmpl):
        self.expr, self.flavor = expr, flavor
        self.pos, self.tmpl = pos, tmpl
        self._ecache = _compile(expr, pos, tmpl)

    def __call__(self, ns):
        try:
            ret = eval(self._ecache, {}, ns)
            if isinstance(ret, _Block):
                ret = ret(ns)
        except NameError, value:
            s = 'NameError: "%s"'%value
            raise TempException(s, self.pos, self.tmpl)
        if self.flavor == "@":
            if not getattr(ret, "_cubictemp_unescaped", 0):
                return escape(str(ret))
        return str(ret)


class _Text:
    def __init__(self, txt):
        self.txt = txt

    def __call__(self, ns):
        return self.txt


class _Block(list):
    def __init__(self):
        self.ns = {}

    def __call__(self, ns):
        ns = ns.copy()
        ns.update(self.ns)
        return "".join([i(ns) for i in self])


class _Iterable(list):
    def __init__(self, iterable, varname, pos, tmpl):
        self.iterable, self.varname = iterable, varname
        self.pos, self.tmpl = pos, tmpl
        self._ecache = _compile(iterable, pos, tmpl)
        self.ns = {}

    def __call__(self, ns):
        ns = ns.copy()
        ns.update(self.ns)
        try:
            loopIter = eval(self._ecache, {}, ns)
        except NameError, value:
            s = 'NameError: "%s"'%value
            raise TempException(s, self.pos, self.tmpl)
        try:
            loopIter = iter(loopIter)
        except TypeError:
            s = "Can not iterate over %s"%self.iterable
            raise TempException(s, self.pos, self.tmpl)
        s = []
        for i in loopIter:
            ns[self.varname] = i
            s.append("".join([i(ns) for i in self]))
        return "".join(s)


class Temp:
    _cubictemp_unescaped = 1
    _bStart = r"""
        # Two kinds of tags: named blocks and for loops
        (<!--\(\s*               
            (
                    for\s+(?P<varName>\w+)\s+in\s+(?P<iterable>.+)
                |   block\s+ (?P<process>\|)? (?P<blockName>\w+)
            )
        \s*\)(-->)?) | 
        # The end of a tag
        (?P<end>(<!--)?\(\s*end\s*\)-->) |
        # An expression
        ((?P<flavor>@|\$)!(?P<expr>.+?)!(?P=flavor))
    """
    _reParts = re.compile(_bStart, re.X|re.M)
    name = "<string>"
    def __init__(self, txt, **nsDict):
        self.nsDict, self.txt = nsDict, txt
        self.block = _Block()
        matches = self._reParts.finditer(txt)
        pos = 0
        stack = [self.block]
        for m in matches:
            if m.start() > pos:
                stack[-1].append(_Text(txt[pos:m.start()]))
            pos = m.end()
            g = m.groupdict()
            if g["blockName"] or g["iterable"]:
                parent = stack[-1]
                if g["blockName"]:
                    b = _Block()
                    parent.ns[g["blockName"]] = b
                else:
                    b = _Iterable(g["iterable"], g["varName"], pos, self)
                    parent.append(b)
                stack.append(b)
            elif g["end"]:
                stack.pop()
            elif g["expr"]:
                e = _Expression(g["expr"], g["flavor"], pos, self)
                stack[-1].append(e)
        if pos < len(txt):
            stack[-1].append(_Text(txt[pos:]))

    def __str__(self):
        return self.block(self.nsDict)

    def __call__(self, **override):
        ns = self.nsDict.copy()
        ns.update(override)
        return self.block(ns)


class File(Temp):
    def __init__(self, filename, **nsDict):
        self.name = filename
        data = open(filename).read()
        Temp.__init__(self, data, **nsDict)
