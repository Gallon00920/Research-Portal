"""PowerPoint decks (.pptx, and .ppt where a converter can open it), read slide by slide like the
other uploads: what is text is kept as text, and what is a picture stays a picture.

The .pptx itself says exactly what every shape is, so it is read directly (it is a zip of XML):
  - the slide title (title placeholder)              -> a heading
  - text boxes and text placeholders with sentences  -> paragraphs and bullet lists
  - tables                                           -> real tables
  - charts, pictures, SmartArt, and diagrams drawn    -> pictures, cropped from the slide as it
    from shapes (filled boxes with short labels,         renders, at the exact place the file
    arrows, connectors, tiles of key figures)            gives for them
The crops need the slide rendered: the deck is converted to PDF with LibreOffice (`soffice`, on
Linux servers) or, on Windows, PowerPoint. Without either, pictures are taken from the file's own
media, a chart becomes a table of its data, and a shape diagram is left out; the rest is the same.
"""
from __future__ import annotations

import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from lxml import etree

from .common import build_exhibits, guess_language

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "dc": "http://purl.org/dc/elements/1.1/",
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "dgm": "http://schemas.openxmlformats.org/drawingml/2006/diagram",
}
R_ID = "{%s}id" % NS["r"]
R_EMBED = "{%s}embed" % NS["r"]
SKIP_PH = {"dt", "ftr", "sldNum", "hdr"}
TITLE_PH = {"title", "ctrTitle"}
SHAPE_TEXT_GEOMS = {"rect", "roundRect", "snip1Rect", "snip2SameRect", "round1Rect", "round2SameRect", None}
WEB_IMAGES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}


# ------------------------------------------------------------------ the package
class Deck:
    def __init__(self, path: Path):
        self.z = zipfile.ZipFile(path)
        self.names = set(self.z.namelist())
        pres = self.xml("ppt/presentation.xml")
        sz = pres.find("p:sldSz", NS)
        self.cx = int(sz.get("cx")) if sz is not None else 12192000
        self.cy = int(sz.get("cy")) if sz is not None else 6858000
        rels = self.rels("ppt/presentation.xml")
        self.slides = []
        for sid in pres.findall("p:sldIdLst/p:sldId", NS):
            target = rels.get(sid.get(R_ID))
            if target and target in self.names:
                self.slides.append(target)

    def xml(self, name: str):
        return etree.fromstring(self.z.read(name))

    def rels(self, part: str) -> dict[str, str]:
        """relationship id -> part name (resolved against the part's folder)."""
        folder = PurePosixPath(part).parent
        rel_name = str(folder / "_rels" / (PurePosixPath(part).name + ".rels"))
        if rel_name not in self.names:
            return {}
        out = {}
        for r in self.xml(rel_name).findall("rel:Relationship", NS):
            if r.get("TargetMode") == "External":
                continue
            out[r.get("Id")] = _norm(str(folder / r.get("Target")))
        return out

    def title(self) -> str:
        if "docProps/core.xml" not in self.names:
            return ""
        t = self.xml("docProps/core.xml").find("dc:title", NS)
        return " ".join((t.text or "").split()) if t is not None else ""


def _norm(path: str) -> str:
    parts: list[str] = []
    for p in path.split("/"):
        if p == "..":
            if parts:
                parts.pop()
        elif p and p != ".":
            parts.append(p)
    return "/".join(parts)


# ------------------------------------------------------------------ shapes
def _xfrm(el):
    """(x, y, cx, cy, chx, chy, chcx, chcy) of a shape or group transform, in EMU."""
    x = el if etree.QName(el).localname == "xfrm" else el.find(".//a:xfrm", NS)
    if x is None:
        return None
    off, ext = x.find("a:off", NS), x.find("a:ext", NS)
    if off is None or ext is None:
        return None
    vals = [int(off.get("x")), int(off.get("y")), int(ext.get("cx")), int(ext.get("cy"))]
    choff, chext = x.find("a:chOff", NS), x.find("a:chExt", NS)
    if choff is not None and chext is not None:
        vals += [int(choff.get("x")), int(choff.get("y")), int(chext.get("cx")), int(chext.get("cy"))]
    return vals


def _paragraphs(tx) -> list[dict[str, Any]]:
    out = []
    if tx is None:
        return out
    for p in tx.findall("a:p", NS):
        parts = []
        for node in p:
            tag = etree.QName(node).localname
            if tag in ("r", "fld"):
                t = node.find("a:t", NS)
                if t is not None and t.text:
                    parts.append(t.text)
            elif tag == "br":
                parts.append("\n")
        text = "".join(parts).strip()
        if not text:
            continue
        ppr = p.find("a:pPr", NS)
        level = int(ppr.get("lvl", "0")) if ppr is not None else 0
        bullet = None
        if ppr is not None:
            if ppr.find("a:buNone", NS) is not None:
                bullet = False
            elif ppr.find("a:buChar", NS) is not None or ppr.find("a:buAutoNum", NS) is not None:
                bullet = True
        sizes = [int(r.get("sz")) for r in p.findall(".//a:rPr", NS) if r.get("sz", "").isdigit()]
        out.append({"text": text, "level": level, "bullet": bullet, "size": max(sizes) / 100 if sizes else 0})
    return out


def _filled(sp) -> bool:
    sppr = sp.find("p:spPr", NS)
    if sppr is not None:
        for tag in ("solidFill", "gradFill", "pattFill", "blipFill"):
            if sppr.find("a:" + tag, NS) is not None:
                return True
        if sppr.find("a:noFill", NS) is not None:
            return False
    if sp.find("p:nvSpPr/p:cNvSpPr", NS) is not None and sp.find("p:nvSpPr/p:cNvSpPr", NS).get("txBox") == "1":
        return False
    ref = sp.find("p:style/a:fillRef", NS)
    return ref is not None and ref.get("idx", "0") != "0"


def flatten(deck: Deck, slide: str) -> list[dict[str, Any]]:
    """Every shape of a slide with its box in slide EMU (groups resolved), in document order."""
    root = deck.xml(slide)
    rels = deck.rels(slide)
    tree = root.find("p:cSld/p:spTree", NS)
    items: list[dict[str, Any]] = []

    def walk(parent, tf):
        for el in parent:
            tag = etree.QName(el).localname
            if tag == "grpSp":
                g = _xfrm(el.find("p:grpSpPr", NS))
                walk(el, (g, tf))
                continue
            if tag not in ("sp", "pic", "graphicFrame", "cxnSp"):
                continue
            box = _xfrm(el.find("p:xfrm", NS) if tag == "graphicFrame" else el.find("p:spPr", NS) if tag != "pic" else el.find("p:spPr", NS))
            if box is None:
                continue
            x, y, cx, cy = box[:4]
            t = tf
            while t is not None:  # map through the enclosing groups, innermost first
                g, t = t
                if g and len(g) == 8 and g[6] and g[7]:
                    sx, sy = g[2] / g[6], g[3] / g[7]
                    x, y, cx, cy = g[0] + (x - g[4]) * sx, g[1] + (y - g[5]) * sy, cx * sx, cy * sy
            item: dict[str, Any] = {"tag": tag, "box": (x, y, x + cx, y + cy)}
            if tag == "sp":
                ph = el.find("p:nvSpPr/p:nvPr/p:ph", NS)
                item["ph"] = (ph.get("type") or "body") if ph is not None else None
                geom = el.find("p:spPr/a:prstGeom", NS)
                item["geom"] = geom.get("prst") if geom is not None else None
                item["filled"] = _filled(el)
                item["paras"] = _paragraphs(el.find("p:txBody", NS))
            elif tag == "pic":
                blip = el.find(".//a:blip", NS)
                item["media"] = rels.get(blip.get(R_EMBED)) if blip is not None else None
            elif tag == "graphicFrame":
                gd = el.find("a:graphic/a:graphicData", NS)
                uri = gd.get("uri", "") if gd is not None else ""
                if uri.endswith("/table"):
                    item["tag"] = "table"
                    item["rows"] = _table_rows(gd.find("a:tbl", NS))
                elif uri.endswith("/chart"):
                    item["tag"] = "chart"
                    ch = gd.find("c:chart", NS)
                    item["part"] = rels.get(ch.get(R_ID)) if ch is not None else None
                elif uri.endswith("/diagram"):
                    item["tag"] = "diagram"
                    ids = gd.find("dgm:relIds", NS)
                    item["part"] = rels.get(ids.get("{%s}dm" % NS["r"])) if ids is not None else None
                else:
                    item["tag"] = "object"
            items.append(item)

    walk(tree, None)
    return items


def _table_rows(tbl) -> list[list[str]]:
    rows = []
    if tbl is None:
        return rows
    for tr in tbl.findall("a:tr", NS):
        row = []
        for tc in tr.findall("a:tc", NS):
            if tc.get("hMerge") == "1" or tc.get("vMerge") == "1":
                row.append("")
                continue
            row.append("\n".join(p["text"] for p in _paragraphs(tc.find("a:txBody", NS))))
        rows.append(row)
    n = max((len(r) for r in rows), default=0)
    rows = [r + [""] * (n - len(r)) for r in rows if any(c.strip() for c in r)]
    return rows


def _chart_rows(deck: Deck, part: str | None) -> tuple[str, list[list[str]]]:
    """A chart as a table of its cached data: (title, rows), first column the categories."""
    if not part or part not in deck.names:
        return "", []
    root = deck.xml(part)
    title = " ".join(t.text or "" for t in root.findall("c:chart/c:title//a:t", NS)).strip()
    cats: list[str] = []
    cols: list[tuple[str, dict[int, str]]] = []
    for ser in root.iter("{%s}ser" % NS["c"]):
        name = " ".join(v.text or "" for v in ser.findall("c:tx//c:v", NS)).strip() or f"Series {len(cols) + 1}"
        cat_pts = ser.findall("c:cat//c:pt", NS) or ser.findall("c:xVal//c:pt", NS)
        if cat_pts and not cats:
            cats = [None] * (max(int(p.get("idx", 0)) for p in cat_pts) + 1)
            for p in cat_pts:
                v = p.find("c:v", NS)
                cats[int(p.get("idx", 0))] = v.text if v is not None else ""
        vals = {}
        for p in ser.findall("c:val//c:pt", NS) or ser.findall("c:yVal//c:pt", NS):
            v = p.find("c:v", NS)
            if v is not None and v.text is not None:
                vals[int(p.get("idx", 0))] = _fmt(v.text)
        cols.append((name, vals))
    if not cols:
        return title, []
    n = max([len(cats)] + [max(v, default=-1) + 1 for _, v in cols])
    rows = [[""] + [c for c, _ in cols]]
    for i in range(n):
        rows.append([(cats[i] if i < len(cats) and cats[i] is not None else str(i + 1))] + [v.get(i, "") for _, v in cols])
    return title, rows


def _fmt(v: str) -> str:
    try:
        f = float(v)
    except ValueError:
        return v
    return f"{f:,.4f}".rstrip("0").rstrip(".") if abs(f) < 1e15 else v


def _diagram_items(deck: Deck, part: str | None) -> list[str]:
    if not part or part not in deck.names:
        return []
    texts = []
    for pt in deck.xml(part).iter("{%s}pt" % NS["dgm"]):
        t = " ".join(x.text or "" for x in pt.findall(".//a:t", NS)).strip()
        if t:
            texts.append(t)
    return texts


# ------------------------------------------------------------------ rendering (LibreOffice / PowerPoint)
def _soffice() -> str | None:
    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return found
    for p in (r"C:\Program Files\LibreOffice\program\soffice.exe", r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
              "/usr/bin/soffice", "/usr/lib/libreoffice/program/soffice", "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        if Path(p).is_file():
            return p
    return None


def to_pdf(path: Path, out_dir: Path) -> tuple[Path | None, str]:
    """The deck rendered to PDF, and which program did it ("" and None when none could)."""
    if os.environ.get("PPTX_CONVERTER", "").strip().lower() == "none":
        return None, ""
    out_dir.mkdir(parents=True, exist_ok=True)
    office = _soffice()
    if office:
        try:
            subprocess.run([office, "--headless", "--norestore", "--convert-to", "pdf", "--outdir", str(out_dir), str(path)],
                           capture_output=True, timeout=240, check=False,
                           env=dict(os.environ, HOME=os.environ.get("HOME") or str(out_dir)))
            pdf = out_dir / (path.stem + ".pdf")
            if pdf.is_file() and pdf.stat().st_size:
                return pdf, "LibreOffice"
        except Exception as exc:  # noqa: BLE001
            print(f"pptx: LibreOffice could not convert {path.name}: {exc}", file=sys.stderr)
    if sys.platform == "win32" and shutil.which("powershell"):
        pdf = out_dir / (path.stem + ".pdf")
        script = (
            "$ErrorActionPreference='Stop'; $app = New-Object -ComObject PowerPoint.Application; "
            "try { $p = $app.Presentations.Open($env:PPTX_SRC, -1, 0, 0); $p.SaveAs($env:PPTX_OUT, 32); $p.Close() } "
            "finally { $app.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($app) }"
        )
        try:
            subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script], capture_output=True, timeout=240,
                           check=False, env=dict(os.environ, PPTX_SRC=str(path.resolve()), PPTX_OUT=str(pdf.resolve())))
            if pdf.is_file() and pdf.stat().st_size:
                return pdf, "PowerPoint"
        except Exception as exc:  # noqa: BLE001
            print(f"pptx: PowerPoint could not convert {path.name}: {exc}", file=sys.stderr)
    return None, ""


# ------------------------------------------------------------------ one slide
def _text_of(item) -> str:
    return " ".join(p["text"] for p in item.get("paras") or [])


def _is_prose(item, slide_w: int) -> bool:
    """A text shape that reads as text: sentences, or several lines of some length."""
    text = _text_of(item)
    if not text:
        return False
    if item.get("geom") not in SHAPE_TEXT_GEOMS:
        return False  # text on an arrow, chevron, circle...: a diagram
    n = len(text)
    paras = item.get("paras") or []
    if n >= 40 or (len(paras) >= 2 and n >= 24):
        return True
    if re.search(r"[；;。，,：:、]", text) and (n >= 18 or (n >= 12 and len(re.findall(r"\d", text)) < 0.15 * n)):
        return True  # a sentence, short as it is (a card's one-line body); a key figure's note is mostly figures
    # a single short line spanning much of the slide is a heading or a caption
    return n >= 8 and (item["box"][2] - item["box"][0]) > 0.45 * slide_w and not item.get("filled")


def _contains(outer, inner, slack: float = 0.0) -> bool:
    return (outer[0] - slack <= inner[0] and outer[1] - slack <= inner[1] and inner[2] <= outer[2] + slack and inner[3] <= outer[3] + slack)


def _near(a, b, gap: float) -> bool:
    return a[0] - gap <= b[2] and b[0] - gap <= a[2] and a[1] - gap <= b[3] and b[1] - gap <= a[3]


def _slide_parts(deck: Deck, slide: str, repeated_media: set[str]) -> tuple[str, list[dict[str, Any]]]:
    """(slide title, [{kind, box, ...}]) for one slide: text, tables and the regions to picture."""
    W, H = deck.cx, deck.cy
    items = flatten(deck, slide)
    title = ""
    parts: list[dict[str, Any]] = []
    graphics: list[dict[str, Any]] = []
    prose: list[dict[str, Any]] = []
    for it in items:
        tag, box = it["tag"], it["box"]
        if box[2] - box[0] <= 0 or box[3] - box[1] <= 0 or box[2] < 0 or box[3] < 0 or box[0] > W or box[1] > H:
            continue  # off the slide
        if tag == "sp":
            if it.get("ph") in SKIP_PH:
                continue
            text = _text_of(it)
            if it.get("ph") in TITLE_PH and text:
                title = title or " ".join(text.split())
                continue
            if re.fullmatch(r"\d{1,3}", text.strip()) and (box[1] > 0.85 * H or box[3] < 0.15 * H):
                continue  # a page number
            if _is_prose(it, W):
                prose.append(it)
            elif text or it.get("filled") or it.get("geom") not in SHAPE_TEXT_GEOMS:
                graphics.append(it)
        elif tag == "cxnSp":
            graphics.append(it)
        elif tag == "pic":
            area = (box[2] - box[0]) * (box[3] - box[1])
            if it.get("media") in repeated_media or area < 0.025 * W * H:
                continue  # a logo or an icon
            graphics.append(it)
        elif tag in ("chart", "diagram", "object"):
            graphics.append(it)
        elif tag == "table" and it.get("rows"):
            parts.append({"kind": "table", "box": box, "rows": it["rows"]})
    if not title:
        # no title placeholder: a title typed into a text box is a line of words (not a key figure)
        # at the very top spanning much of the slide, else the largest-font line of words near the top
        words = re.compile(r"[A-Za-z\u4e00-\u9fff]")
        top = [it for it in items if it["tag"] == "sp" and it.get("ph") not in SKIP_PH and _text_of(it)
               and len(_text_of(it)) <= 90 and not it.get("filled") and words.search(_text_of(it))]
        banner = [it for it in top if it["box"][1] < 0.1 * H and it["box"][2] - it["box"][0] >= 0.45 * W]
        best = min(banner, key=lambda it: it["box"][1]) if banner else None
        if best is None:
            sized = [(max((pp.get("size") or 0) for pp in it["paras"]), it) for it in top if it["box"][1] < 0.22 * H]
            sized = [x for x in sized if x[0] >= 20]
            best = max(sized, key=lambda x: (x[0], -x[1]["box"][1]))[1] if sized else None
        if best is not None:
            title = " ".join(_text_of(best).split())
            prose = [q for q in prose if q is not best]
            graphics = [q for q in graphics if q is not best]
    # a filled shape behind text is a panel, not a picture: the text inside it is read as text
    graphics = [g for g in graphics if not (g["tag"] == "sp" and not _text_of(g) and g.get("filled")
                                             and any(_contains(g["box"], p["box"], 0.01 * W) for p in prose))]
    # prose inside a picture region (a callout of a chart) stays in the picture
    regions = _cluster([g for g in graphics], 0.012 * W)
    keep_prose = []
    for p in prose:
        inside = next((r for r in regions if _contains(r["box"], p["box"], 0.004 * W) and r["n_graphic"] >= 3), None)
        if inside:
            inside["members"].append(p)
        else:
            keep_prose.append(p)
    for p in keep_prose:
        parts.append({"kind": "text", "box": p["box"], "paras": p["paras"], "placeholder": p.get("ph") is not None,
                      "filled": p.get("filled")})
    pictured = []
    for r in regions:
        members = r["members"]
        labels = [m for m in members if m["tag"] == "sp" and _text_of(m)]
        media = any(m["tag"] in ("chart", "pic", "diagram", "object") for m in members)
        tiles = [m for m in members if m["tag"] == "sp" and m.get("filled") and not _decor(m, W, H)
                 and (_text_of(m) or any(_contains(m["box"], q["box"], 0.004 * W) for q in labels if q is not m))]
        solid = [m for m in members if not _decor(m, W, H)]
        if not media and len(solid) == 1 and _text_of(solid[0]):
            tiles = []  # one framed box holding only its own words: a heading, not a picture
        if media or tiles:
            pictured.append({"kind": "region", "box": r["box"], "members": members})
            continue
        # a cluster of loose labels and decorations (a heading beside a coloured dot, a divider
        # line, an accent bar): the labels are text, the decorations are dropped
        for m in labels:
            parts.append({"kind": "text", "box": m["box"], "paras": m["paras"], "placeholder": False, "filled": False})
    pictured = _merge_rows(pictured, W, H)
    # a picture stops where text read as text, or a table, begins above or below it
    others = [q for q in parts if q["kind"] in ("text", "table")]
    for r in pictured:
        x0, y0, x1, y1 = r["box"]
        for q in others:
            a = q["box"]
            if a[2] <= x0 or a[0] >= x1 or a[3] <= y0 or a[1] >= y1:
                continue
            if a[1] >= y0 + 0.4 * (y1 - y0):
                y1 = min(y1, a[1] - 0.008 * H)  # clear of the crop's padding too
            elif a[3] <= y0 + 0.6 * (y1 - y0):
                y0 = max(y0, a[3] + 0.008 * H)
        if y1 - y0 > 0.03 * H:
            r["box"] = [x0, y0, x1, y1]
            parts.append(r)
    return title, _reading_order(parts, 0.008 * H, 0.012 * W)


def _reading_order(parts: list[dict[str, Any]], gap_y: float, gap_x: float, depth: int = 0) -> list[dict[str, Any]]:
    """Parts in reading order: split at a horizontal gap into rows (top first), a row at a vertical
    gap into columns (left first), and so on; a card layout reads card by card."""
    if len(parts) <= 1 or depth > 12:
        return sorted(parts, key=lambda q: (q["box"][1], q["box"][0]))
    # columns first when the region is a row of full-height columns (cards side by side): each
    # column is read top to bottom before the next; otherwise rows first
    top, bottom = min(q["box"][1] for q in parts), max(q["box"][3] for q in parts)
    cols = _split(parts, 0, gap_x)
    if len(cols) > 1 and all(max(q["box"][3] for q in c) - min(q["box"][1] for q in c) >= 0.6 * (bottom - top) for c in cols):
        out = []
        for c in cols:
            out += _reading_order(c, gap_y, gap_x, depth + 1)
        return out
    for axis, gap in ((1, gap_y), (0, gap_x)):
        spans = sorted(((q["box"][axis], q["box"][axis + 2], q) for q in parts), key=lambda t: t[0])
        groups, cur, end = [], [spans[0][2]], spans[0][1]
        for a, b, q in spans[1:]:
            if a > end + gap:
                groups.append(cur); cur = [q]
            else:
                cur.append(q)
            end = max(end, b)
        groups.append(cur)
        if len(groups) > 1:
            out = []
            for g in groups:
                out += _reading_order(g, gap_y, gap_x, depth + 1)
            return out
    return sorted(parts, key=lambda q: (q["box"][1], q["box"][0]))


def _decor(m, W: int, H: int) -> bool:
    """A decoration: a line or thin bar, or a small shape with no text (a dot, an icon frame)."""
    x0, y0, x1, y1 = m["box"]
    w, h = x1 - x0, y1 - y0
    if m["tag"] == "cxnSp" or min(w / W, h / H) < 0.008:
        return True
    text = _text_of(m).strip()
    if len(text) <= 3 and re.fullmatch(r"[\dA-Za-z①-⑳•·\-.)）]*", text) and w * h < 0.015 * W * H:
        return True  # a numbered badge or a bullet dot
    return not text and w * h < 0.015 * W * H


def _merge_rows(regions: list[dict[str, Any]], W: int, H: int) -> list[dict[str, Any]]:
    """Pictures that sit side by side in a row with the same height (a strip of key-figure tiles)
    become one picture."""
    regions = sorted(regions, key=lambda r: (r["box"][1], r["box"][0]))
    out: list[dict[str, Any]] = []
    for r in regions:
        prev = out[-1] if out else None
        if prev is not None:
            a, b = prev["box"], r["box"]
            ha, hb = a[3] - a[1], b[3] - b[1]
            if (abs(a[1] - b[1]) < 0.03 * H and abs(ha - hb) < 0.2 * max(ha, hb) and 0 <= b[0] - a[2] < 0.08 * W):
                prev["box"] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                prev["members"] = prev["members"] + r["members"]
                continue
        out.append(dict(r, box=list(r["box"])))
    return out


def _split(parts, axis: int, gap: float) -> list[list[dict[str, Any]]]:
    spans = sorted(((q["box"][axis], q["box"][axis + 2], q) for q in parts), key=lambda t: t[0])
    groups, cur, end = [], [spans[0][2]], spans[0][1]
    for a, b, q in spans[1:]:
        if a > end + gap:
            groups.append(cur); cur = [q]
        else:
            cur.append(q)
        end = max(end, b)
    groups.append(cur)
    return groups


def _cluster(items: list[dict[str, Any]], gap: float) -> list[dict[str, Any]]:
    regions: list[dict[str, Any]] = []
    for it in items:
        box = list(it["box"])
        hit = [r for r in regions if _near(r["box"], box, gap)]
        merged = {"box": box, "members": [it], "n_graphic": 1}
        for r in hit:
            merged["box"] = [min(merged["box"][0], r["box"][0]), min(merged["box"][1], r["box"][1]),
                             max(merged["box"][2], r["box"][2]), max(merged["box"][3], r["box"][3])]
            merged["members"] += r["members"]
            merged["n_graphic"] += r["n_graphic"]
            regions.remove(r)
        regions.append(merged)
    # merging can make a region reach another: repeat until stable
    changed = True
    while changed:
        changed = False
        for i, a in enumerate(regions):
            for b in regions[i + 1:]:
                if _near(a["box"], b["box"], gap):
                    a["box"] = [min(a["box"][0], b["box"][0]), min(a["box"][1], b["box"][1]), max(a["box"][2], b["box"][2]), max(a["box"][3], b["box"][3])]
                    a["members"] += b["members"]; a["n_graphic"] += b["n_graphic"]
                    regions.remove(b)
                    changed = True
                    break
            if changed:
                break
    return regions


# ------------------------------------------------------------------ the report
def parse_pptx(path: Path, image_dir: Path) -> dict[str, Any]:
    path, image_dir = Path(path), Path(image_dir)
    image_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="pptx-"))
    try:
        if path.suffix.lower() == ".ppt":
            # the old binary format: only a converter can open it; read the PDF it makes
            pdf, by = to_pdf(path, tmp)
            if not pdf:
                raise ValueError("an old .ppt file needs LibreOffice (or PowerPoint) on the server; save it as .pptx and upload that")
            from .pdf_parser import parse_pdf

            result = parse_pdf(pdf, image_dir)
            result["stats"]["rendered_by"] = by
            return result
        try:
            deck = Deck(path)
        except (zipfile.BadZipFile, KeyError, etree.XMLSyntaxError) as exc:
            raise ValueError("not a readable .pptx file") from exc
        pdf, by = to_pdf(path, tmp)
        doc = None
        if pdf:
            import fitz

            doc = fitz.open(str(pdf))
            if len(doc) != len(deck.slides):  # hidden slides etc.: positions would not match pages
                print(f"pptx: {len(doc)} rendered pages for {len(deck.slides)} slides; pictures come from the file", file=sys.stderr)
                doc, by = None, ""
        return _build(deck, doc, by, image_dir)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _build(deck: Deck, doc, rendered_by: str, image_dir: Path) -> dict[str, Any]:
    # media on half or more of the slides (a logo, a banner) is page furniture
    from collections import Counter

    count: Counter = Counter()
    for s in deck.slides:
        for v in set(deck.rels(s).values()):
            if v.startswith("ppt/media/"):
                count[v] += 1
    repeated = {m for m, c in count.items() if len(deck.slides) >= 3 and c >= max(3, len(deck.slides) // 2)}

    blocks: list[dict[str, Any]] = []
    titles: list[str] = []
    n_img = 0
    multi = len(deck.slides) > 1
    for si, slide in enumerate(deck.slides):
        title, parts = _slide_parts(deck, slide, repeated)
        titles.append(title)
        slide_blocks: list[dict[str, Any]] = []
        page = doc[si] if doc is not None else None
        scale = (page.rect.width / deck.cx) if page is not None else 0
        for part in parts:
            kind = part["kind"]
            if kind == "text":
                slide_blocks.extend(_text_blocks(part))
            elif kind == "table":
                slide_blocks.append({"type": "table", "rows": part["rows"], "header": True, "caption": "", "exhibit": None, "note": ""})
            elif kind == "region":
                cap = _region_caption(part, deck)
                if page is not None:
                    import fitz

                    x0, y0, x1, y1 = part["box"]
                    pad = 0.004 * deck.cx
                    rect = fitz.Rect((x0 - pad) * scale, (y0 - pad) * scale, (x1 + pad) * scale, (y1 + pad) * scale) & page.rect
                    if rect.width < 8 or rect.height < 8:
                        continue
                    n_img += 1
                    name = f"img_{n_img:03d}.png"
                    pix = page.get_pixmap(clip=rect, dpi=170)
                    pix.save(str(image_dir / name))
                    slide_blocks.append({"type": "image", "src": name, "caption": cap, "exhibit": None, "note": "",
                                         "width": rect.width, "height": rect.height})
                else:
                    slide_blocks.extend(_unrendered(part, deck, image_dir, lambda: _next_name(image_dir)))
        if multi and (title or slide_blocks):
            if blocks:
                blocks.append({"type": "pagebreak"})
            if title:
                blocks.append({"type": "heading", "level": 1, "text": title})
        elif title and not multi:
            blocks.append({"type": "heading", "level": 1, "text": title})
        blocks.extend(slide_blocks)

    body = " ".join(b.get("text", "") for b in blocks if b["type"] in ("heading", "paragraph"))
    body += " " + " ".join(html.unescape(x) for b in blocks if b["type"] == "list" for x in b["items"])
    report_title = next((t for t in titles if t), "") or deck.title()
    return {
        "title": report_title,
        "keywords": [],
        "language": guess_language(body) if body.strip() else "en",
        "blocks": blocks,
        "exhibits": build_exhibits(blocks),
        "stats": {"blocks": len(blocks), "images": sum(1 for b in blocks if b["type"] == "image"),
                  "tables": sum(1 for b in blocks if b["type"] == "table"), "chars": len(body.strip()),
                  "pages": len(deck.slides), "rendered_by": rendered_by or "none (pictures from the file)"},
    }


def _next_name(image_dir: Path) -> str:
    n = len(list(image_dir.glob("img_*"))) + 1
    return f"img_{n:03d}"


def _text_blocks(part) -> list[dict[str, Any]]:
    paras = part["paras"]
    out: list[dict[str, Any]] = []
    bulleted = [p for p in paras if p["bullet"] or (p["bullet"] is None and part.get("placeholder") and len(paras) > 1)]
    if part.get("filled") and not bulleted:
        out.append({"type": "callout", "text": "\n".join(p["text"] for p in paras)})
        return out
    run: list[str] = []
    for p in paras:
        is_b = p["bullet"] or (p["bullet"] is None and part.get("placeholder") and len(paras) > 1)
        if is_b:
            run.append(html.escape(p["text"]))
            continue
        if run:
            out.append({"type": "list", "ordered": False, "items": run}); run = []
        t = " ".join(p["text"].split())
        out.append({"type": "paragraph", "html": html.escape(t), "text": t, "style": None})
    if run:
        out.append({"type": "list", "ordered": False, "items": run})
    return out


def _region_caption(part, deck) -> str:
    """A chart's own title, when the region is one chart."""
    charts = [m for m in part["members"] if m["tag"] == "chart"]
    if len(charts) == 1 and len(part["members"]) <= 3:
        return _chart_rows(deck, charts[0].get("part"))[0]
    return ""


def _unrendered(part, deck, image_dir: Path, new_name) -> list[dict[str, Any]]:
    """Without a rendered slide: pictures from the file's media, charts as tables of their data,
    SmartArt as a list of its text; shapes drawn on the slide are left out."""
    out: list[dict[str, Any]] = []
    for m in sorted(part["members"], key=lambda m: (m["box"][1], m["box"][0])):
        if m["tag"] == "pic" and m.get("media") in deck.names and Path(m["media"]).suffix.lower() in WEB_IMAGES:
            name = new_name() + Path(m["media"]).suffix.lower()
            (image_dir / name).write_bytes(deck.z.read(m["media"]))
            out.append({"type": "image", "src": name, "caption": "", "exhibit": None, "note": ""})
        elif m["tag"] == "chart":
            title, rows = _chart_rows(deck, m.get("part"))
            if len(rows) >= 2:
                out.append({"type": "table", "rows": rows, "header": True, "caption": title, "exhibit": None, "note": ""})
        elif m["tag"] == "diagram":
            items = _diagram_items(deck, m.get("part"))
            if items:
                out.append({"type": "list", "ordered": False, "items": [html.escape(x) for x in items]})
    return out
