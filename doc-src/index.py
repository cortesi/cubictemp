
import countershape.widgets
import countershape.layout
import countershape.grok
from countershape.doc import *

ns.docTitle = "Cubictemp Manual"
ns.docMaintainer = "Aldo Cortesi"
ns.docMaintainerEmail = "aldo@nullcube.com"
ns.foot = "Copyright Nullcube 2008"
ns.head = readFrom("_header.html")
ns.sidebar = countershape.widgets.SiblingPageIndex('/index.html', exclude=['countershape'])
this.layout = countershape.layout.TwoPane("yui-t2", "doc3")
this.titlePrefix = "Cubictemp Manual - "

ns.ctgrok = countershape.grok.grok("../cubictemp.py")

pages = [
    Page("index.html", "Introduction"),
    Page("subs.html", "Tags"),
    Page("blocks.html", "Blocks"),
    Page("processors.html", "Processors"),
    Page("api.html", "API"),
    Page("admin.html", "Administrivia")
]
