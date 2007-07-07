#!/usr/local/bin/python
import cgi, re, itertools

class TemplateError(Exception):
    pos = None
    template = None
    lineNo = None
    contextLen = 2
    def __init__(self, message, pos, template):
        Exception.__init__(self, message)
        self.pos, self.template = pos, template
        self.lineNo, self._contextStr = self._getLines(template.txt, pos)

    def _getLines(self, txt, pos):
        lines = txt.splitlines(True)
        cur = 0
        for i, l in enumerate(lines):
            cur += len(l)
            if cur > pos:
                break

        if i < self.contextLen:
            startc = 0
        else:
            startc = i - self.contextLen

        if i + self.contextLen > len(lines):
            endc = len(lines)
        else:
            endc = i + self.contextLen + 1

        marker = "%s\n"%("^"*len(lines[i].rstrip()))
        _contextStr = lines[startc:i+1] + [marker] + lines[i+1:endc]
        _contextStr = ["        " + l.rstrip() for l in _contextStr]
        _contextStr = "\n".join(_contextStr)
        return i + 1, _contextStr

    def __str__(self):
        ret = [
            "%s"%self.message,
            "\tContext: line %s in %s:"%(self.lineNo, self.template.name),
        ]
        ret.append(self._contextStr)
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


class Processor:
    def __init__(self):
        self.funcs = []

    def __or__(self, other):
        self.funcs.append(other)
        return self

    def __call__(self, s):
        for i in self.funcs:
            s = i(s)
        return s


class _Text:
    def __init__(self, txt):
        self.txt = txt

    def __call__(self, **ns):
        return self.txt


class _Eval:
    def _compile(self, expr, pos, tmpl):
            try:
                return compile(expr, "<string>", "eval")
            except SyntaxError, value:
                s = 'Invalid expression: "%s"'%(expr)
                raise TemplateError(s, pos, tmpl)

    def _eval(self, e, ns):
        try:
            return eval(e, {}, ns)
        except NameError, value:
            s = 'NameError: "%s"'%value
            raise TemplateError(s, self.pos, self.tmpl)


class _Expression(_Eval):
    def __init__(self, expr, flavor, pos, tmpl, ns):
        self.expr, self.flavor = expr, flavor
        self.pos, self.tmpl = pos, tmpl
        self.ns = ns
        self._ecache = self._compile(expr, pos, tmpl)

    def __call__(self, **ns):
        ns.update(self.ns)
        ret = self._eval(self._ecache, ns)
        if isinstance(ret, _Block):
            ret = ret(**ns)
        if self.flavor == "@":
            if not getattr(ret, "_cubictemp_unescaped", 0):
                return escape(str(ret))
        return str(ret)


class _Block(list, _Eval):
    def __init__(self, processor, pos, tmpl, ns):
        self.ns, self.processor = ns, processor
        self.pos, self.tmpl = pos, tmpl
        if processor:
            self._ecache = self._compile(
                "_cubictemp_processor | " + processor, pos, tmpl
            )

    def __call__(self, **ns):
        r = "".join([i(**ns) for i in self])
        if self.processor:
            ns["_cubictemp_processor"] = Processor()
            proc = self._eval(self._ecache, ns)
            return proc(r)
        else:
            return r


class _Iterable(list, _Eval):
    def __init__(self, iterable, varname, pos, tmpl, ns):
        self.iterable, self.varname = iterable, varname
        self.pos, self.tmpl = pos, tmpl
        self.ns = ns
        self._ecache = self._compile(iterable, pos, tmpl)

    def __call__(self, **ns):
        loopIter = self._eval(self._ecache, ns)
        try:
            loopIter = iter(loopIter)
        except TypeError:
            s = "Can not iterate over %s"%self.iterable
            raise TemplateError(s, self.pos, self.tmpl)
        s = []
        for i in loopIter:
            ns[self.varname] = i
            s.append("".join([i(**ns) for i in self]))
        return "".join(s)


class Template:
    _cubictemp_unescaped = 1
    _bStart = r"""
        # Two kinds of tags: named blocks and for loops
        (^[ \t]*<!--\(\s*               
            (
                    for\s+(?P<varName>\w+)\s+in\s+(?P<iterable>.+)
                |   block(\s+(?P<blockName>\w+))? \s* (\|\s*(?P<processor>.+))?
            )
        \s*\)(-->)?\s*?\n) | 
        # The end of a tag
        (?P<end>^[ \t]*(<!--)?\(\s*end\s*\)-->\s*\n) |
        # An expression
        ((?P<flavor>@|\$)!(?P<expr>.+?)!(?P=flavor))
    """
    _reParts = re.compile(_bStart, re.X|re.M)
    name = "<string>"
    def __init__(self, txt, **nsDict):
        self.nsDict, self.txt = nsDict, txt
        matches = self._reParts.finditer(txt)
        pos = 0
        self.block = _Block(None, pos, self, {})
        stack = [self.block]
        for m in matches:
            parent = stack[-1]
            if m.start() > pos:
                parent.append(_Text(txt[pos:m.start()]))
            pos = m.end()
            g = m.groupdict()
            if g["blockName"]:
                b = _Block(g["processor"], pos, self, parent.ns.copy())
                parent.ns[g["blockName"]] = b
                stack.append(b)
            if g["processor"]:
                b = _Block(g["processor"], pos, self, parent.ns.copy())
                stack.append(b)
                parent.append(b)
            elif g["iterable"]:
                b = _Iterable(
                    g["iterable"],
                    g["varName"],
                    pos,
                    self,
                    parent.ns.copy()
                )
                parent.append(b)
                stack.append(b)
            elif g["end"]:
                stack.pop()
                if not stack:
                    raise TemplateError("Unbalanced block.", pos, self)
            elif g["expr"]:
                e = _Expression(g["expr"], g["flavor"], pos, self, parent.ns.copy())
                parent.append(e)
        if pos < len(txt):
            stack[-1].append(_Text(txt[pos:]))

    def __str__(self):
        return self()

    def __call__(self, **override):
        ns = self.nsDict.copy()
        ns.update(override)
        return self.block(**ns)


class File(Template):
    def __init__(self, filename, **nsDict):
        self.name = filename
        data = open(filename).read()
        Template.__init__(self, data, **nsDict)
