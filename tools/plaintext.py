"""Render a page of this site as the 72-column plaintext document that gets signed.

Only understands the handful of structures the site uses: section headings,
paragraphs, service entries, spec rows, process steps and the fit lists.
"""
import textwrap
from html.parser import HTMLParser

WIDTH = 72
RULE = "-" * WIDTH
VOID = {"br", "meta", "link", "img", "input", "hr", "source"}
SKIP = {"script", "style", "nav", "button", "pre", "head"}


class Node:
    def __init__(self, tag, attrs, parent=None):
        self.tag, self.attrs, self.parent, self.kids = tag, dict(attrs), parent, []

    def cls(self):
        return self.attrs.get("class", "").split()

    def text(self):
        out = []
        for k in self.kids:
            if isinstance(k, str):
                out.append(k)
            elif k.tag == "br":
                out.append(" ")
            elif k.tag not in SKIP:
                out.append(k.text())
        return " ".join("".join(out).split())

    def find(self, tag=None, cls=None):
        for k in self.kids:
            if isinstance(k, Node):
                if (tag is None or k.tag == tag) and (cls is None or cls in k.cls()):
                    yield k


class Tree(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = self.cur = Node("root", {})
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.cur)
        self.cur.kids.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.kids.append(data)


def walk(node, tag=None, cls=None):
    for k in node.kids:
        if isinstance(k, Node):
            if (tag is None or k.tag == tag) and (cls is None or cls in k.cls()):
                yield k
            yield from walk(k, tag, cls)


def wrap(text, indent="", hang=None):
    return textwrap.fill(text, WIDTH, initial_indent=indent,
                         subsequent_indent=indent if hang is None else hang,
                         break_on_hyphens=False, break_long_words=False)


def rows(dl, key_width=12, indent="  "):
    out = []
    for row in dl.find("div", "row"):
        dt, dd = next(row.find("dt")).text(), next(row.find("dd")).text()
        out.append(wrap(dd, indent + dt.ljust(key_width), indent + " " * key_width))
    return out


def section(sec, number):
    title = next(sec.find("h2")).text()
    out = [f"{number:02d}  {title.upper()}", RULE, ""]
    for el in sec.kids:
        if not isinstance(el, Node):
            continue
        cls = el.cls()
        if el.tag == "p":
            out += [wrap(el.text()), ""]
        elif el.tag == "article":
            out.append(next(el.find("h3")).text())
            for k in el.kids:
                if isinstance(k, Node) and k.tag == "p":
                    out.append(wrap(k.text(), "  "))
                    out.append("")
                elif isinstance(k, Node) and k.tag == "dl":
                    for row in k.find("div", "row"):
                        out.append(f"  {next(row.find('dt')).text()}:")
                        out.append(wrap(next(row.find("dd")).text(), "    "))
                        out.append("")
        elif el.tag == "dl":
            out += rows(el) + [""]
        elif el.tag == "ol" and "steps" in cls:
            for i, li in enumerate(el.find("li"), 1):
                out.append(f"  {i:02d}  {next(li.find('h3')).text()}")
                out += [wrap(next(li.find("p")).text(), "      "), ""]
        elif el.tag == "div" and "fit-cols" in cls:
            for col in el.find("div", "fit-col"):
                out.append(f"  {next(col.find('h3')).text()}:")
                ul = next(col.find("ul"))
                mark = "[+]" if "good" in ul.cls() else "[-]"
                out += [wrap(li.text(), f"  {mark} ", "      ") for li in ul.find("li")]
                out.append("")
    return out


def render(html, footer):
    root = Tree(html).root
    head = next(walk(root, "header", "head"))
    out = [next(walk(head, "h1")).text().upper(), ""]
    for p in head.find("p"):
        out += [wrap(p.text()), ""]
    main = next(walk(root, "main"))
    for i, sec in enumerate(main.find("section"), 1):
        out += section(sec, i)
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out + ["", RULE, footer, ""])
