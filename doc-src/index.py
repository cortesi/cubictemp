
import countershape.widgets
import countershape.layout
import countershape.grok
from countershape.doc import *

ns.docTitle = "Cubictemp Manual"
ns.docMaintainer = "Aldo Cortesi"
ns.docMaintainerEmail = "aldo@nullcube.com"
ns.foot = "Copyright Nullcube 2007"
ns.head = readFrom("_header.html")
ns.sidebar = countershape.widgets.SiblingPageIndex('/index.html', exclude=['countershape'])
this.layout = countershape.layout.TwoPane("yui-t2", "doc3")

ns.ctgrok = countershape.grok.grok("../cubictemp.py")

pages = [
    Page("index.html", "Introduction"),
    Page("subs.html", "Substitution Tags"),
    Directory("subs"),
    Page("blocks.html", "Blocks"),
    Directory("blocks"),
    Page("api.html", "API"),
    Page("example.html", "An Example"),
    Page("admin.html", "Administrivia")
]
