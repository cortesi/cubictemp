
import countershape.widgets
import countershape.layout
from countershape.doc import *

ns.docTitle = "Cubictemp Manual"
ns.docMaintainer = "Aldo Cortesi"
ns.docMaintainerEmail = "aldo@nullcube.com"
ns.foot = "Copyright Nullcube 2007"
ns.head = readFrom("_header.html")
ns.sidebar = countershape.widgets.SiblingPageIndex('/index.html', exclude=['countershape'])
this.layout = countershape.layout.TwoPane("yui-t2", "doc3")

pages = [
    Page("index.html", "Introduction"),
    Page("start.html", "Getting Started"),
    Page("templates.html", "Templates"),
    Page("subs.html", "Substitution Tags"),
    Directory("subs"),
    Page("blocks.html", "Blocks"),
    Directory("blocks"),
    Page("exceptions.html", "Exceptions"),
    Page("example.html", "An Example"),
    Page("cheat.html", "Cheat Sheet"),
    PythonPage("../cubictemp.py", "Source"),
    Page("admin.html", "Administrivia")
]
