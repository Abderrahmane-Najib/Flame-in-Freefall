"""Minimal .xlsx reader (standard library only): returns {sheet name: list of rows}.

Cell values come back as strings exactly as stored (numbers unformatted, dates as Excel serials).
Good enough for the PSI workbooks; no formulas are evaluated (cached values are read).
"""

from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
       "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
_M = "{%s}" % _NS["m"]


def _col(ref: str) -> int:
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group():
        n = n * 26 + ord(ch) - 64
    return n - 1


def read_xlsx(path: str | Path) -> dict[str, list[list[str]]]:
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", _NS):
            shared.append("".join(t.text or "" for t in si.iter(_M + "t")))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
    sheets: dict[str, list[list[str]]] = {}
    for s in wb.find("m:sheets", _NS):
        target = rels[s.get("{%s}id" % _NS["r"])].lstrip("/")
        if not target.startswith("xl/"):
            target = "xl/" + target
        rows = []
        for row in ET.fromstring(z.read(target)).iter(_M + "row"):
            vals: dict[int, str] = {}
            for c in row.findall("m:c", _NS):
                t, v = c.get("t"), c.find("m:v", _NS)
                if t == "inlineStr":
                    vals[_col(c.get("r"))] = "".join(x.text or "" for x in c.iter(_M + "t"))
                elif v is not None:
                    vals[_col(c.get("r"))] = shared[int(v.text)] if t == "s" else (v.text or "")
            rows.append([vals.get(i, "") for i in range(max(vals) + 1)] if vals else [])
        sheets[s.get("name")] = rows
    return sheets
