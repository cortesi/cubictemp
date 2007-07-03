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
        startc = 0 if i < context else i - context
        endc = len(lines) if i+context > len(lines) else i + context + 1
        marker = "%s\n"%("^"*len(l))
        context = lines[startc:i+1] + [marker] + lines[i+1:endc]
        context = ["\t\t" + l for l in context]
        return i + 1, context

    def __str__(self):
        ret = [
            "TempException: %s"%self.val,
            "\tContext: line %s in %s:"%(self.lineNo, self.tmpl.name),
        ]
        ret.append("".join(self.context))
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


class _Text:
    def __init__(self, txt):
        self.txt = txt

    def __call__(self, ns):
        return self.txt


class _Eval:
    def _compile(self, expr, pos, tmpl):
            try:
                return compile(expr, "<string>", "eval")
            except SyntaxError, value:
                s = 'Invalid expression: "%s"'%(expr)
                raise TempException(s, pos, tmpl)

    def _eval(self, e, ns):
        try:
            return eval(e, {}, ns)
        except NameError, value:
            s = 'NameError: "%s"'%value
            raise TempException(s, self.pos, self.tmpl)


class _Expression(_Eval):
    def __init__(self, expr, flavor, pos, tmpl):
        self.expr, self.flavor = expr, flavor
        self.pos, self.tmpl = pos, tmpl
        self._ecache = self._compile(expr, pos, tmpl)

    def __call__(self, ns):
        ret = self._eval(self._ecache, ns)
        if isinstance(ret, _Block):
            ret = ret(ns)
        if self.flavor == "@":
            if not getattr(ret, "_cubictemp_unescaped", 0):
                return escape(str(ret))
        return str(ret)


class _Block(list, _Eval):
    def __init__(self, processor, pos, tmpl):
        self.ns, self.processor = {}, processor
        self.pos, self.tmpl = pos, tmpl
        if processor:
            self._ecache = self._compile(processor, pos, tmpl)

    def __call__(self, ns):
        ns = ns.copy()
        ns.update(self.ns)
        r = "".join([i(ns) for i in self])
        if self.processor:
            proc = self._eval(self._ecache, ns)
            return proc(r)
        else:
            return r


class _Iterable(list, _Eval):
    def __init__(self, iterable, varname, pos, tmpl):
        self.iterable, self.varname = iterable, varname
        self.pos, self.tmpl = pos, tmpl
        self._ecache = self._compile(iterable, pos, tmpl)
        self.ns = {}

    def __call__(self, ns):
        ns = ns.copy()
        ns.update(self.ns)
        loopIter = self._eval(self._ecache, ns)
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
                |   block\s+(?P<blockName>\w+)? \s* (\|\s*(?P<processor>\w+))?
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
        matches = self._reParts.finditer(txt)
        pos = 0
        self.block = _Block(None, pos, self)
        stack = [self.block]
        for m in matches:
            parent = stack[-1]
            if m.start() > pos:
                parent.append(_Text(txt[pos:m.start()]))
            pos = m.end()
            g = m.groupdict()
            if g["blockName"]:
                b = _Block(g["processor"], pos, self)
                parent.ns[g["blockName"]] = b
                stack.append(b)
            if g["processor"]:
                b = _Block(g["processor"], pos, self)
                stack.append(b)
                parent.append(b)
            elif g["iterable"]:
                b = _Iterable(g["iterable"], g["varName"], pos, self)
                parent.append(b)
                stack.append(b)
            elif g["end"]:
                stack.pop()
                if not stack:
                    raise TempException("Unbalanced block.", pos, self)
            elif g["expr"]:
                e = _Expression(g["expr"], g["flavor"], pos, self)
                parent.append(e)
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
