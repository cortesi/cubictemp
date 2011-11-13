# Copyright (c) 2003-2008, Nullcube Pty Ltd All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
import cgi, re, itertools, copy, os.path

class TemplateError(Exception):
    """
        Template evaluation exception class.
    """
    # Character offset within the raw template at which the error occurred
    pos = None
    # Template object
    template = None
    # Line number
    lineNo = None
    # Error context length
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
            "%s"%self.args[0],
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


class _Processor:
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

    def render(self, **ns):
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

    def render(self, **ns):
        ns.update(self.ns)
        ret = self._eval(self._ecache, ns)
        if isinstance(ret, _Block):
            ret = ret.render(**ns)
        if self.flavor == "@":
            if not getattr(ret, "_cubictemp_unescaped", 0):
                return escape(unicode(ret))
        return unicode(ret)


class _Block(list, _Eval):
    def __init__(self, processor, pos, tmpl, ns):
        self.ns, self.processor = ns, processor
        self.pos, self.tmpl = pos, tmpl
        if processor:
            self._ecache = self._compile(
                "_cubictemp_processor | " + processor, pos, tmpl
            )

    def render(self, **ns):
        n = ns.copy()
        n.update(self.ns)
        r = "".join([i.render(**n) for i in self])
        if self.processor:
            n["_cubictemp_processor"] = _Processor()
            proc = self._eval(self._ecache, n)
            return proc(r)
        else:
            return r

    def __call__(self, **override):
        """
            :override A set of key/value pairs.

            Returns a copy of this block, with the over-riding namespace
            incorporated.
        """
        c = copy.copy(self)
        c.ns = self.ns.copy()
        c.ns.update(**override)
        return c


class _Iterable(list, _Eval):
    def __init__(self, iterable, varname, pos, tmpl, ns):
        self.iterable, self.varname = iterable, str(varname)
        self.pos, self.tmpl = pos, tmpl
        self.ns = ns
        self._ecache = self._compile(iterable, pos, tmpl)

    def render(self, **ns):
        loopIter = self._eval(self._ecache, ns)
        try:
            loopIter = iter(loopIter)
        except TypeError:
            s = "Can not iterate over %s"%self.iterable
            raise TemplateError(s, self.pos, self.tmpl)
        s = []
        for i in loopIter:
            ns[self.varname] = i
            s.append("".join([i.render(**ns) for i in self]))
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
        \s*\)(-->)?[ \t\r\f\v]*?\n) |
        # The end of a tag
        (?P<end>^[ \t]*(<!--)?\(\s*end\s*\)-->[ \t\r\f\v]*\n) |
        # An expression
        ((?P<flavor>@|\$)!(?P<expr>.+?)!(?P=flavor))
    """
    _reParts = re.compile(_bStart, re.X|re.M)
    # Name by which this template is referred to in exceptions.
    name = "<string>"
    def __init__(self, txt, **nsDict):
        """
            :txt Template body
            :nsDict Namespace dictionary
        """
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
                parent.ns[str(g["blockName"])] = b
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

    def __unicode__(self):
        """
            Evaluate the template in the namespace provided at instantiation.
        """
        return self.block.render(**self.nsDict)

    def __str__(self):
        """
            Evaluate the template in the namespace provided at instantiation.
        """
        return unicode(self).encode("ascii")

    def raw(self):
        """
            Return an unencoded representation.
        """
        return self.block.render(**self.nsDict)

    def __call__(self, **override):
        """
            :override A set of key/value pairs.

            Returns a copy of this template, with the over-riding namespace
            incorporated.
        """
        c = copy.copy(self)
        c.nsDict = self.nsDict.copy()
        c.nsDict.update(**override)
        return c


class File(Template):
    """
        Convenience class that extends Template to provide easy instantiation
        from a file.
    """
    def __init__(self, filename, **nsDict):
        """
            :filename Full Path to file containing template body.
            :nsDict Instantiation namespace dictionary.
        """
        self.name = filename
        data = open(filename, "rb").read().decode("utf8")
        Template.__init__(self, data, **nsDict)


class FileWatcher:
    def __init__(self, filename, **nsDict):
        """
            :filename Full Path to file containing template body.
            :nsDict Instantiation namespace dictionary.
        """
        self.name = filename
        self.initDict = nsDict
        self._reload()

    def _reload(self):
        self.last = os.path.getmtime(self.name)
        data = open(self.name).read()
        self.template = Template(data, **self.initDict)

    def __call__(self, *args, **kwargs):
        if os.path.getmtime(self.name) != self.last:
            self._reload()
        return self.template(*args, **kwargs)

    def raw(self):
        if os.path.getmtime(self.name) != self.last:
            self._reload()
        return self.template.raw()

    def __unicode__(self):
        if os.path.getmtime(self.name) != self.last:
            self._reload()
        return unicode(self.template)

    def __str__(self):
        """
            Evaluate the template in the namespace provided at instantiation.
        """
        return unicode(self).encode("ascii")

