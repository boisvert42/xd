#!/usr/bin/env python

import re

from xdfile.metadatabase import xd_publications_meta
from xdfile.utils import open_output, get_args
from xdfile.html import html_header, html_footer
import xdfile

style_css = """
table {
/*	font-family: "Lucida Sans Unicode", "Lucida Grande", Sans-Serif; */
	font-size: 14px;
	background: #fff;
	margin: 25px;
/*	width: 480px; */
	border-collapse: collapse;
	text-align: left;
}
th {
	font-size: 16px;
	font-weight: normal;
	color: #039;
	padding: 10px 8px;
	border-bottom: 2px solid #6678b1;
}
td, option, select {
	border-bottom: 1px solid #ccc;
	color: #669;
	padding: 6px 8px;
}
tbody tr:hover td {
	background: #ccf;
}
"""

def mkhref(text, link, title=""):
    return '<a href="%s" title="%s">%s</a>' % (link, title, text)

def table_header(keys):
    out = '<tr class="hdr">'

    for k in keys:
        out += '<th>'
        out += str(k)
        out += '</th>'  # end header cell

    out += '</tr>\n'
    return out


def table_row(row, keys, rowclass="row"):
    if isinstance(row, dict):
        row = [ row[k] for k in keys ]

    out = '<tr class="%s">' % rowclass
    for k, v in zip(keys, row):
        v = unicode(v or "")
        out += '<td class="%s">' % k
        out += v
        out += '</td>'  # end cell
    out += '</tr>\n'  # end row
    return out


def table_to_html(rows, colnames, rowclass="row"):
    out = '<table>'
    out += table_header(colnames)

    for r in rows:
        out += table_row(r, colnames, rowclass)

    out += '</table>'  # end table
    return out.encode("ascii", 'xmlcharrefreplace')


def tally_to_dict(d, v):
    v = v.strip()
    if v:
        d[v] = d.get(v, 0) + 1

def clean_copyright(xd):
    copyright = xd.get_header("Copyright")
    author = xd.get_header("Author").strip()
    if author:
        copyright = copyright.replace(author, "&lt;Author&gt;")

    # and remove textual date
    return re.sub(r"\s*(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JAN|FEB|MAR|APR|JUN|JUL|AUG|SEP|OCT|NOV|DEC)?\s*(\d{1,2})?,?\s*\d{4},?\s*", " &lt;Date&gt; ", copyright, flags=re.IGNORECASE)


class Publication:
    def __init__(self, pubid):
        self.publication_id = pubid
        self.copyrights = {}  # [copyright_text] -> number of xd
        self.editors = {}  # [editor_name] -> number of xd
        self.formats = {}  # ["15x15 RS"] -> number of xd
        self.mindate = ""
        self.maxdate = ""
        self.num_xd = 0

    def add(self, xd):
        tally_to_dict(self.copyrights, clean_copyright(xd))
        tally_to_dict(self.editors, xd.get_header("Editor"))
        tally_to_dict(self.formats, "%sx%s %s%s" % (xd.width(), xd.height(), xd.get_header("Rebus") and "R" or "", xd.get_header("Special") and "S" or ""))
        datestr = xd.get_header("Date")
        if datestr:
            if not self.mindate:
                self.mindate = datestr
            else:
                self.mindate = min(self.mindate, datestr)
            if not self.maxdate:
                self.maxdate = datestr
            else:
                self.maxdate = max(self.maxdate, datestr)
        self.num_xd += 1

    def row(self):
        return [
                self.publication_id,
                mkhref(str(self.num_xd), self.publication_id),
                "%s - %s" % (self.mindate, self.maxdate),
                tally_to_cell(self.formats),
                tally_to_cell(self.copyrights),
                tally_to_cell(self.editors),
               ]


def tally_to_cell(d):
    freq_sorted = sorted([(v, k) for k, v in d.items()], reverse=True)

    if not freq_sorted:
        return ""
    elif len(freq_sorted) == 1:
        return "<br>".join("%s [x%s]" % (k, v) for v, k in freq_sorted)
    else:
        return "<select><option>" + "</option><option>".join("%s [x%s]" % (k, v) for v, k in freq_sorted) + "</select>"


def publication_header():
    return "PubId NumCollected DatesCollected Formats Copyrights Editors".split()


def main():
    get_args("generate publishers html pages and index")

    outf = open_output()

    #publishers_index = html_header.format(title=time.strftime("Crossword publishers"))

    all_pubs = {}  # [pubid] -> Publication

    total_xd = 0
    for xd in xdfile.corpus():
        pubid = xd.publication_id()
        if pubid not in all_pubs:
            all_pubs[pubid] = Publication(pubid)

        all_pubs[pubid].add(xd)
        total_xd += 1

    pubrows = [pub.row() for pubid, pub in sorted(all_pubs.items()) if pub.num_xd >= 20]

    pub_index = html_header.format(title="Index of crossword publishers")

    pub_index += table_to_html(pubrows, publication_header(), "Publication")

    pub_index += "<p>%d crosswords from %d publications</p>" % (total_xd, len(all_pubs))

    pub_index += html_footer

    outf.write_file("pubs/index.html", pub_index)
    outf.write_file("pubs/style.css", style_css)

"""
outlines = []
total_xd = 0
    num_xd = publ.num_xd
    total_xd += num_xd
    dates = "%s - %s" % (publ.FirstIssueDate, publ.LastIssueDate)
    pubid = publ.PublicationAbbr

    outlines.append((publ.num_xd, '<li><a href="{pubid}"><b>{pubid}</b></a>: {num_xd} crosswords from {years}</li>'.format(**{
                    'pubid': pubid,
                    "num_xd": num_xd,
                    "years": years
                    })))

out = mkwww.html_header.format(title=time.strftime("xd corpus grid similarity results [%Y-%m-%d]"))
out += "The xd corpus has %d crosswords total:" % total_xd
out += "<ul>"
out += "\n".join(L for n, L in sorted(outlines, reverse=True))
out += "</ul>"
out += '<a href="xd-xdiffs.zip">xd-xdiffs.zip</a> (7MB) has raw data for all puzzles that are at least 25% similar.  Source code for using <a href="https://github.com/century-arcade/xd">the .xd format is available on Github.</a><br/>'
out += mkwww.html_footer

print out
"""

if __name__ == "__main__":
    main()
