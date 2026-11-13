"""Parse a PDF report into the same block list the docx parser produces.

Fund reports arrive in every layout: letters with underlined headings and charts pasted as
images (Bayview), portrait reports with banded tables and vector donut charts (Apollo), slide
decks with a watermark on every page (Bain Capital). The parser therefore:

- drops running headers, footers, watermarks and page numbers: a line (digits normalised) that
  appears on at least half of the pages, three or more, is not content;
- reads text line by line: large text is a heading, so is a bold or underlined short line, and
  so is a short first line of a block that is followed by a sentence (a letter's section title);
- keeps bullets together: a bullet glyph on its own line marks the next line, and the lines of
  one bullet are joined;
- takes tables from PyMuPDF's ruled-line detection and keeps only real ones (enough filled
  cells); a one-cell first row, the coloured band above a table, becomes its caption;
- never rewrites a chart as a table: the line finder also "finds" bar charts (bar edges read as
  cell borders) and line charts (gridlines read as rules), so every candidate is tested first.
  Diagonal or curved paths inside it, a column of value labels in one cell, bars that do not
  sit on the table's rows, or a rotated axis title next to it make it a chart, and it is
  rendered to a picture instead; a candidate that runs across body paragraphs is dropped;
- joins the pieces of a banded table (shaded rows, no ruled lines) that the line finder
  returns one shaded row at a time, and reads the joined table's rows from its bands and its
  columns from the gaps in the text; a dark title band becomes the caption;
- finds charts drawn as vector paths by clustering the drawings itself (PyMuPDF's clustering
  leaves a donut chart in pieces), grows the region to its axis labels and legend, and renders
  it to PNG, as it does for pasted images; text inside a chart or table is not repeated as
  paragraphs;
- picks the title from the largest text on the first page.
"""
from __future__ import annotations

import html
import math
import re
import statistics
from pathlib import Path
from typing import Any

from .common import attach_captions, build_exhibits, guess_language, is_caption

try:
    import pymupdf as fitz  # type: ignore
except Exception:  # pragma: no cover
    import fitz  # type: ignore

BULLET_RE = re.compile(r"^[•·▪◦●○■□➢➤►\-–—]\s*")
BULLET_ONLY_RE = re.compile(r"^[•·▪◦●○■□➢➤►\-–—]$")
PAGE_NO_RE = re.compile(r"^(page\s*)?\d{1,3}(\s*(/|of)\s*\d{1,3})?$|^(confidential|strictly confidential)\s*[-–|]?\s*\d{0,3}$", re.I)
NOTE_RE = re.compile(r"^(source|sources|资料来源|来源|note|notes|注)[:：]", re.I)
DATE_RE = re.compile(r"^(\d{1,2}\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}|^\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|^\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}", re.I)
# private-use glyphs that Word's symbol fonts use for bullets and check marks
GLYPHS = {"": "•", "": "•", "": "•", "": "✓", "": "✗", "": "◆", "": "•", "": "•"}


# a value label of a chart: 149, $149, 12.5%, (3.2), 2.1x, -39
VALUE_RE = re.compile(r"^[-+−(]?[$€£¥]?\d[\d,.]*%?[)xX]?$")


def _clean(text: str) -> str:
    for k, v in GLYPHS.items():
        text = text.replace(k, v)
    return re.sub(r"\s+", " ", text).strip()


def _overlap(a, b) -> float:
    """How much of rect a lies inside rect b (0..1)."""
    x0, y0 = max(a.x0, b.x0), max(a.y0, b.y0)
    x1, y1 = min(a.x1, b.x1), min(a.y1, b.y1)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    return (x1 - x0) * (y1 - y0) / max(1e-6, (a.x1 - a.x0) * (a.y1 - a.y0))


def _norm(text: str) -> str:
    return re.sub(r"\d+", "#", re.sub(r"\s+", " ", text)).strip().lower()


def _luma(color) -> float:
    """Perceived brightness of an RGB fill (0 dark .. 1 white); no fill counts as white."""
    if not color:
        return 1.0
    r, g, b = (list(color) + [0, 0, 0])[:3]
    return 0.299 * r + 0.587 * g + 0.114 * b


def _fill_rects(page) -> list[tuple[Any, Any]]:
    """Every filled rectangle drawn on the page as (rect, fill colour): row shading, title
    bands, bars of a bar chart, legend swatches. A rectangle drawn again in the same colour
    inside another one (cell padding) is left out."""
    try:
        drawings = page.get_drawings()
    except Exception:
        return []
    raw = []
    for d in drawings:
        if not d.get("fill"):
            continue
        for it in d["items"]:
            if it[0] == "re" and it[1].width > 2.5 and it[1].height > 2.5:
                raw.append((fitz.Rect(it[1]), tuple(d["fill"])))
    out = []
    for r, col in raw:
        if any(o is not r and oc == col and _overlap(r, o) > 0.97 and (o.width * o.height) > 1.02 * (r.width * r.height) for o, oc in raw):
            continue
        out.append((r, col))
    return out


class PdfParser:
    def __init__(self, path: Path, image_dir: Path):
        self.path = Path(path)
        self.image_dir = Path(image_dir)
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.blocks: list[dict[str, Any]] = []
        self._img_n = 0

    # ------------------------------------------------------------------ document
    def parse(self) -> dict[str, Any]:
        doc = fitz.open(str(self.path))
        pages_data = [page.get_text("dict") for page in doc]
        lines_by_page = [self._lines(d) for d in pages_data]
        sizes = [ln["size"] for lines in lines_by_page for ln in lines if ln["text"].strip()]
        body_size = statistics.median(sizes) if sizes else 10.0
        repeated = self._repeated(lines_by_page)

        for pno, page in enumerate(doc):
            self._parse_page(page, lines_by_page[pno], body_size, repeated)
            if pno < len(doc) - 1:
                self.blocks.append({"type": "pagebreak"})

        blocks = attach_captions(self.blocks)
        exhibits = build_exhibits(blocks)
        text = " ".join(b.get("text", "") for b in blocks if b.get("type") in ("paragraph", "heading"))
        meta = doc.metadata or {}
        title = self._title(lines_by_page[0] if lines_by_page else [], repeated, body_size, meta.get("title") or "")
        kws = [k.strip() for k in re.split(r"[;,，；]", meta.get("keywords") or "") if k.strip()]
        return {
            "title": title,
            "keywords": kws,
            "language": guess_language(text),
            "blocks": blocks,
            "exhibits": exhibits,
            "stats": {
                "blocks": len(blocks),
                "images": sum(1 for b in blocks if b["type"] == "image"),
                "tables": sum(1 for b in blocks if b["type"] == "table"),
                "chars": len(text),
                "pages": len(doc),
            },
        }

    @staticmethod
    def _lines(d) -> list[dict[str, Any]]:
        """Every text line of a page with its size, weight, bbox and the block it came from."""
        out = []
        for bi, b in enumerate(d["blocks"]):
            if b.get("type") != 0:
                continue
            for li, line in enumerate(b["lines"]):
                spans = [s for s in line["spans"] if s["text"].strip()]
                if not spans:
                    continue
                text = _clean("".join(s["text"] for s in line["spans"]))
                bold = all(("bold" in (s.get("font") or "").lower()) or (s.get("flags", 0) & 16) for s in spans)
                d0 = (line.get("dir") or (1, 0))[0]
                out.append({"text": text, "size": max(s["size"] for s in spans), "bold": bold, "rot": abs(d0) < 0.9,
                            "rect": fitz.Rect(line["bbox"]), "block": bi, "line": li, "block_rect": fitz.Rect(b["bbox"])})
        return out

    @staticmethod
    def _repeated(lines_by_page) -> set[str]:
        """Normalised texts that recur on at least half of the pages (three or more): running
        headers and footers, confidentiality lines, watermarks."""
        n = len(lines_by_page)
        if n < 3:
            return set()
        count: dict[str, int] = {}
        for lines in lines_by_page:
            for key in {_norm(ln["text"]) for ln in lines if len(ln["text"].strip()) >= 4}:
                count[key] = count.get(key, 0) + 1
        need = max(3, math.ceil(n / 2))
        return {k for k, c in count.items() if c >= need}

    @staticmethod
    def _skip_line(ln, repeated: set[str]) -> bool:
        text = ln["text"].strip()
        if not text:
            return True
        if PAGE_NO_RE.match(text):
            return True
        return _norm(text) in repeated

    def _title(self, lines, repeated, body_size, meta_title: str) -> str:
        """The largest text on the first page, with the large lines right under it (a fund name
        and the report name); else the file's own title, else the file name."""
        # a running header is often the document's own name, so repeated lines count here;
        # page numbers, dates, e-mail watermarks and reference codes do not
        cand = [ln for ln in lines if len(ln["text"]) >= 4 and not PAGE_NO_RE.match(ln["text"]) and not DATE_RE.match(ln["text"])
                and "@" not in ln["text"] and len(re.sub(r"[^A-Za-z一-鿿]", "", ln["text"])) >= 0.5 * len(ln["text"])]
        if cand:
            top = max(ln["size"] for ln in cand)
            if top >= body_size * 1.25:
                big = sorted([ln for ln in cand if ln["size"] >= top * 0.75], key=lambda ln: (ln["rect"].y0, ln["rect"].x0))
                start = next(i for i, ln in enumerate(big) if ln["size"] >= top - 0.5)
                parts, prev = [big[start]["text"]], big[start]
                for ln in big[start + 1:]:
                    # the next big line joins the title unless it is a sentence or a salutation
                    if len(parts) >= 2 or ln["rect"].y0 - prev["rect"].y1 > prev["size"] * 1.4 or re.search(r"[,:;，：；]$", ln["text"]) or re.search(r"[.。]$", parts[-1]):
                        break
                    parts.append(ln["text"])
                    prev = ln
                title = re.sub(r"\s+", " ", " ".join(parts)).strip()
                title = re.sub(r"\s*[（(][^()（）]{12,}[)）]", "", title)  # an aside: (together with its subsidiaries, …)
                if 4 <= len(title) <= 160:
                    return title
        meta_title = re.sub(r"\s*[（(][^()（）]{12,}[)）]\s*$", "", meta_title.strip())
        if len(meta_title) >= 4 and not re.search(r"\.(docx?|pptx?|pdf)$|^(microsoft|powerpoint|untitled)", meta_title, re.I):
            return meta_title
        return self.path.stem

    # ------------------------------------------------------------------ page
    def _parse_page(self, page, lines, body_size: float, repeated: set[str]):
        items: list[tuple[float, float, dict[str, Any]]] = []  # (y, x, block)
        covered: list[Any] = []
        page_area = page.rect.width * page.rect.height

        # tables: ruled-line detection. The finder also returns charts (bar edges and gridlines
        # read as cell borders) and, on a page with a chart, a "table" that runs across the
        # paragraphs, so every candidate is tested first; a chart is rendered to a picture and
        # never rewritten as a table. The text of each cell is read from the page inside the
        # cell's box (extract() loses spaces and decimal points)
        try:
            tabs = page.find_tables(strategy="lines")
        except Exception:
            tabs = None
        cands = list(tabs.tables) if tabs else []
        # words of running headers and watermarks never belong to a cell (a bare figure does);
        # "words" and "dict" number blocks and lines the same way
        junk = {(ln["block"], ln["line"]) for ln in lines if _norm(ln["text"]) in repeated}
        words = [w for w in page.get_text("words") if (w[5], w[6]) not in junk] if cands else []
        shapes, rules = self._shapes(page)
        fills = _fill_rects(page) if cands else []
        tables: list[tuple[Any, dict[str, Any], bool]] = []  # (rect, table, confirmed)
        seeds: list[Any] = []  # charts the finder mistook for tables
        pictures: list[Any] = []  # tables that could not be read: shown as pictures
        kept = []
        for t in cands:
            kind = self._candidate_kind(page, t, fitz.Rect(t.bbox), lines, words, fills)
            if kind == "chart":
                seeds.append(fitz.Rect(t.bbox))
            elif kind == "table":
                kept.append(t)
        for group in self._band_groups(kept, lines, body_size, fills):
            # a banded table (two or more shaded rows) is read from its shading; the finder's
            # own cells serve a ruled table, and a banded one its shading could not read
            taken = [r for r, _, _ in tables]
            rect, table = self._banded_table(page, group, words, lines, fills, body_size, min_bands=2, taken=taken)
            if table:
                tables.append((rect, table, True))
                continue
            if len(group) > 1:
                pictures.append(rect)
                continue
            t = group[0]
            rect = fitz.Rect(t.bbox)
            table = self._clean_table(self._table_rows(page, t, words))
            if not table:
                # a lone shaded row with unshaded rows around it
                rect, table = self._banded_table(page, group, words, lines, fills, body_size, min_bands=1, taken=taken)
                if table:
                    tables.append((rect, table, True))
                continue
            # a few "rows" full of drawn shapes that are not cell shading is a chart with a frame
            cells = [fitz.Rect(c) for c in (t.cells or []) if c]
            loose = [s for s in shapes if _overlap(s, rect) > 0.8 and not any(_overlap(s, c) > 0.85 and _overlap(c, s) > 0.85 for c in cells)]
            if len(table["rows"]) <= 3 and len(loose) >= 12:
                continue
            tables.append((rect, table, len(table["rows"]) >= 4))
        # charts drawn as vector paths. A "table" that is really the frame of a chart (a few
        # rows, inside a chart region many times its size) gives way to the chart
        strong = [r for r, _, ok in tables if ok]
        chart_rects = self._chart_regions(page, lines, strong, repeated, shapes, rules, seeds)
        table_rects = []
        for rect, table, ok in tables:
            area = rect.width * rect.height
            if not ok and any(_overlap(rect, c) > 0.8 and c.width * c.height > 2.5 * area for c in chart_rects):
                continue
            # the short title line just above the table is its caption, unless the band gave one
            if not table["caption"]:
                above = [ln for ln in lines if 0 <= rect.y0 - ln["rect"].y1 <= 14 and ln["rect"].x0 >= rect.x0 - 6 and ln["rect"].x1 <= rect.x1 + 6
                         and len(ln["text"]) <= 90 and _norm(ln["text"]) not in repeated and ln["size"] < body_size * 1.35
                         and not re.search(r"[.。,，;；]$", ln["text"]) and not ln["text"][:1].islower() and not BULLET_RE.match(ln["text"])]
                if above:
                    cap = max(above, key=lambda ln: ln["rect"].y1)
                    table["caption"] = cap["text"]
                    covered.append(cap["rect"])
            table_rects.append(rect)
            covered.append(rect)
            items.append((rect.y0, rect.x0, {"type": "table", "rows": table["rows"], "header": True, "caption": table["caption"], "exhibit": None, "note": ""}))
        chart_rects = [c for c in chart_rects if not any(_overlap(c, t) > 0.5 or _overlap(t, c) > 0.5 for t in table_rects)]
        for rect in pictures:
            if not any(_overlap(rect, c) > 0.6 for c in covered):
                self._add_image(page, rect, items, covered)

        # pasted images (photos, charts saved as pictures)
        seen = set()
        try:
            infos = page.get_image_info(xrefs=True)
        except Exception:
            infos = []
        for info in infos:
            rect = fitz.Rect(info["bbox"]) & page.rect
            if rect.width < 40 or rect.height < 40 or rect.width * rect.height > 0.9 * page_area:
                continue
            key = (round(rect.x0), round(rect.y0), round(rect.x1), round(rect.y1))
            if key in seen or any(_overlap(rect, c) > 0.6 for c in covered):
                continue
            seen.add(key)
            # a tiny logo in a corner is decoration, a wide or tall picture is content
            if rect.width < 90 and rect.height < 90 and (rect.y0 < page.rect.height * 0.12 or rect.y1 > page.rect.height * 0.9):
                continue
            self._add_image(page, rect, items, covered)

        for rect in chart_rects:
            if any(_overlap(rect, c) > 0.6 for c in covered):
                continue
            self._add_image(page, rect, items, covered)

        # text, line by line
        underlines = self._underlines(page)
        for blk in self._text_blocks(lines, covered, repeated, body_size, underlines, page):
            items.append(blk)

        items.sort(key=lambda it: (round(it[0] / 8), it[1]))
        for _, _, blk in items:
            if blk["type"] == "list" and self.blocks and self.blocks[-1]["type"] == "list" and self.blocks[-1]["ordered"] == blk["ordered"]:
                self.blocks[-1]["items"].extend(blk["items"])
                continue
            self.blocks.append(blk)

    def _add_image(self, page, rect, items, covered):
        try:
            pix = page.get_pixmap(clip=rect, dpi=150)
            self._img_n += 1
            name = f"img_{self._img_n:03d}.png"
            pix.save(str(self.image_dir / name))
        except Exception:
            return
        covered.append(rect)
        items.append((rect.y0, rect.x0, {"type": "image", "src": name, "caption": "", "exhibit": None, "width": rect.width, "height": rect.height, "note": ""}))

    # ------------------------------------------------------------------ tables
    @staticmethod
    def _table_rows(page, t, words) -> list[list[str]]:
        """The table's cells: every word whose centre lies in the cell's box, in reading order
        (extract() loses spaces and decimal points; a text box picks up the rows next door)."""
        rows = []
        try:
            for row in t.rows:
                cells = []
                for c in row.cells:
                    if c is None:
                        cells.append("")
                        continue
                    r = fitz.Rect(c)
                    inside = [w for w in words if r.x0 <= (w[0] + w[2]) / 2 <= r.x1 and r.y0 <= (w[1] + w[3]) / 2 <= r.y1]
                    inside.sort(key=lambda w: (round(w[1] / 3), w[0]))
                    cells.append(_clean(" ".join(w[4] for w in inside)))
                rows.append(cells)
        except Exception:
            rows = [[_clean(c or "") for c in r] for r in t.extract()]
        return rows

    @staticmethod
    def _clean_table(rows) -> dict[str, Any] | None:
        """Tidy the cells (line breaks between the lines of a cell stay) and keep the table
        only if it is one: two or more rows and columns, enough of the cells filled."""
        rows = [["\n".join(s for s in (_clean(x) for x in (c or "").split("\n")) if s) for c in r] for r in rows]
        rows = [r for r in rows if any(r)]
        if len(rows) < 2:
            return None
        ncol = max(len(r) for r in rows)
        rows = [r + [""] * (ncol - len(r)) for r in rows]
        # drop columns that are empty everywhere
        keep = [j for j in range(ncol) if any(r[j] for r in rows)]
        rows = [[r[j] for j in keep] for r in rows]
        if not rows or len(rows[0]) < 2:
            return None
        caption = ""
        # a coloured band above the table reads as a first row with one cell: it is the caption
        if sum(1 for c in rows[0] if c) == 1 and len(rows) >= 3:
            caption = next(c for c in rows[0] if c)
            rows = rows[1:]
        filled = sum(1 for r in rows for c in r if c)
        if filled < 0.4 * len(rows) * len(rows[0]) or not any(sum(1 for c in r if c) >= 2 for r in rows):
            return None
        return {"rows": rows, "caption": caption}

    def _candidate_kind(self, page, t, rect, lines, words, fills) -> str:
        """'table', 'chart' or 'junk' for one candidate of the ruled-line table finder.

        A chart is never rewritten as a table: a line or area chart has diagonal segments or
        curves inside the box, a bar chart has bars that do not sit on the table's rows and
        often a column of value labels read into one cell, and most have a rotated axis title
        next to them. A candidate that runs across body paragraphs (the gridlines of a chart
        made a "table" of the page) is junk; the chart itself is found from its drawings."""
        cells = [fitz.Rect(c) for c in (t.cells or []) if c]
        wide = [ln for ln in lines if ln["rect"].intersects(rect) and ln["rect"].width > 0.6 * page.rect.width
                and not any(_overlap(ln["rect"], c) > 0.9 for c in cells)]
        if len(wide) >= 2:
            return "junk"
        diag = curves = 0
        try:
            drawings = page.get_drawings()
        except Exception:
            drawings = []
        for d in drawings:
            if d["rect"].is_empty or _overlap(d["rect"], rect) < 0.5:
                continue
            for it in d["items"]:
                if it[0] == "c":
                    pts = it[1:5]
                    if max(p.x for p in pts) - min(p.x for p in pts) > 8 or max(p.y for p in pts) - min(p.y for p in pts) > 8:
                        curves += 1  # an arc of a donut or a curve of a line chart, not a rounded corner
                elif it[0] == "l" and abs(it[1].x - it[2].x) > 1.5 and abs(it[1].y - it[2].y) > 1.5:
                    diag += 1
        if diag >= 3 or curves >= 2:
            return "chart"
        # bars: filled rectangles that are not the shading of a row. The cells of a shaded row
        # share one vertical extent and together span the table; bars do not. The thin strips
        # drawn around shaded cells (padding) are not bars
        inside = [r for r, _ in fills if _overlap(r, rect) > 0.5 and r.height >= 6 and r.width >= 4]
        loose = [r for r in inside if r.width < 0.5 * rect.width and not self._row_band(r, inside, rect)]
        if len(loose) >= 4 and len(loose) >= 0.4 * len(inside):
            return "chart"
        # value labels printed on the bars
        labels = sum(1 for w in words if VALUE_RE.match(w[4]) and any(r.contains(fitz.Point((w[0] + w[2]) / 2, (w[1] + w[3]) / 2)) for r in loose))
        if labels >= 3:
            return "chart"
        near = fitz.Rect(rect.x0 - 30, rect.y0 - 30, rect.x1 + 30, rect.y1 + 30)
        if any(ln["rot"] and len(ln["text"]) >= 4 and near.intersects(ln["rect"]) for ln in lines):
            return "chart"
        return "table"

    @staticmethod
    def _row_band(r, fills, box) -> bool:
        """Whether filled rectangle r is (part of) the shading of a row: a chain of touching
        rectangles of about the same vertical extent (cell by cell) that spans the box. The
        bars of a bar chart stand apart from each other and differ in height."""
        chain = [r]
        x0, x1 = r.x0, r.x1
        grown = True
        while grown:
            grown = False
            for o in fills:
                if any(o is c for c in chain):
                    continue
                inter = min(o.y1, r.y1) - max(o.y0, r.y0)
                if inter <= 0 or inter / (max(o.y1, r.y1) - min(o.y0, r.y0)) < 0.6:
                    continue
                if o.x0 <= x1 + 2 and o.x1 >= x0 - 2:  # touches or overlaps the chain
                    chain.append(o)
                    x0, x1 = min(x0, o.x0), max(x1, o.x1)
                    grown = True
        return x1 - x0 >= 0.8 * box.width

    @staticmethod
    def _title_band(rect, fills) -> bool:
        """Whether a dark band spanning the box sits at its top (the title of a table)."""
        return any(_luma(c) < 0.5 and r.width >= 0.9 * rect.width and abs(r.y0 - rect.y0) <= 3 and r.height >= 8 for r, c in fills)

    def _band_groups(self, cands, lines, body_size, fills) -> list[list[Any]]:
        """The finder's candidates grouped into tables. A banded table (shaded rows, no ruled
        lines) comes back one shaded row at a time: pieces that share the left and right
        edge and follow each other with nothing but the table's own text in between are one
        table. A dark title band starts a new one."""
        groups: list[list[Any]] = []
        for t in sorted(cands, key=lambda t: (t.bbox[1], t.bbox[0])):
            r = fitz.Rect(t.bbox)
            if groups:
                last = fitz.Rect(groups[-1][-1].bbox)
                same = abs(last.x0 - r.x0) <= 8 and abs(last.x1 - r.x1) <= 8 and -2 <= r.y0 - last.y1 <= 120
                if same and not self._title_band(r, fills):
                    gap = fitz.Rect(min(last.x0, r.x0), last.y1, max(last.x1, r.x1), r.y0)
                    between = [ln for ln in lines if gap.height > 0 and _overlap(ln["rect"], gap) > 0.5]
                    foreign = any(ln["rect"].x0 < gap.x0 - 4 or ln["rect"].x1 > gap.x1 + 4 or ln["size"] >= body_size * 1.2
                                  or is_caption(ln["text"]) or NOTE_RE.match(ln["text"]) for ln in between)
                    if not foreign:
                        groups[-1].append(t)
                        continue
            groups.append([t])
        return groups

    def _banded_table(self, page, group, words, lines, fills, body_size, min_bands: int, taken=()):
        """Read a banded table from its shading: every band is a row, so is every gap between
        two bands, and a header or footer row without shading just outside the bands joins
        when its words sit in separate cells. Columns are the gaps in the text that run
        through every row. Returns (rect, table); table is None when there are fewer bands
        than asked for or the text does not read as a table (the caller then shows the
        picture, or reads the finder's cells)."""
        rects = [fitz.Rect(t.bbox) for t in group]
        box = fitz.Rect(min(r.x0 for r in rects), min(r.y0 for r in rects), max(r.x1 for r in rects), max(r.y1 for r in rects))
        # bands: filled rectangles sharing a vertical extent (row shading is often drawn cell
        # by cell), kept when they span the box; the box grows to them (the finder's box of a
        # banded table often stops short of a column)
        bands: list[list[Any]] = []  # [rect, luma]
        for r, c in sorted((rc for rc in fills if _overlap(rc[0], box) > 0.4 and rc[0].height >= 6), key=lambda rc: rc[0].y0):
            for b in bands:
                inter = min(b[0].y1, r.y1) - max(b[0].y0, r.y0)
                if inter > 0 and inter / (max(b[0].y1, r.y1) - min(b[0].y0, r.y0)) >= 0.6:
                    b[0] |= r
                    b[1] = min(b[1], _luma(c))
                    break
            else:
                bands.append([fitz.Rect(r), _luma(c)])
        bands = sorted((b for b in bands if b[0].width >= 0.8 * box.width and b[0].width <= 1.3 * box.width), key=lambda b: b[0].y0)
        if len(bands) < min_bands:
            return box, None
        for b in bands:
            box |= b[0]
        band_h = statistics.median(b[0].height for b in bands)
        # footnote markers (tiny digits) are not cell text
        heights = [w[3] - w[1] for w in words if _overlap(fitz.Rect(w[:4]), box) > 0.5]
        wh = statistics.median(heights) if heights else 8.0
        words = [w for w in words if not (w[3] - w[1] < 0.65 * wh and re.fullmatch(r"[\d,]+", w[4]))]
        in_x = lambda w: box.x0 - 4 <= (w[0] + w[2]) / 2 <= box.x1 + 4  # noqa: E731

        headings = [ln["rect"] for ln in lines if ln["size"] >= body_size * 1.2]

        def cell_row(y0, y1) -> bool:
            """Whether the words in the strip y0..y1 sit in separate cells (a gap of 10pt+),
            which a paragraph or a title line never does. A heading's words do not count."""
            ws = sorted((w for w in words if in_x(w) and y0 <= (w[1] + w[3]) / 2 <= y1
                         and not any(_overlap(fitz.Rect(w[:4]), h) > 0.5 for h in headings)), key=lambda w: w[0])
            if not ws:
                return False
            end, gap = ws[0][2], 0.0
            for w in ws[1:]:
                gap = max(gap, w[0] - end)
                end = max(end, w[2])
            return gap >= 10

        # a header row above the first band (unless that band is the table's dark title) and
        # a last row under the last band, both unshaded; neither reaches into a heading or
        # into a table read before
        top, bottom = bands[0][0].y0, bands[-1][0].y1
        stop = [h for h in headings] + list(taken)
        if bands[0][1] >= 0.5:
            y0 = max([top - 1.6 * band_h] + [s.y1 + 1 for s in stop if s.y1 <= top and s.y1 > top - 1.6 * band_h and s.x1 > box.x0 and s.x0 < box.x1])
            if top - y0 >= 6 and cell_row(y0, top - 1):
                top = y0
        y1 = min([bottom + 1.6 * band_h] + [s.y0 - 1 for s in stop if s.y0 >= bottom and s.y0 < bottom + 1.6 * band_h and s.x1 > box.x0 and s.x0 < box.x1])
        if y1 - bottom >= 6 and cell_row(bottom + 1, y1):
            bottom = y1
        box = fitz.Rect(box.x0, min(box.y0, top), box.x1, max(box.y1, bottom)) & page.rect
        rows_y: list[tuple[float, float]] = []
        caption = ""
        prev = box.y0
        for i, (r, luma) in enumerate(bands):
            if r.y0 - prev >= 6:
                rows_y.append((prev, r.y0))
            if i == 0 and luma < 0.5 and r.y0 - box.y0 < 6 and not cell_row(r.y0, r.y1):
                caption = _clean(" ".join(w[4] for w in sorted((w for w in words if in_x(w) and r.y0 <= (w[1] + w[3]) / 2 <= r.y1), key=lambda w: w[0])))
            else:
                rows_y.append((r.y0, r.y1))
            prev = r.y1
        if box.y1 - prev >= 6:
            rows_y.append((prev, box.y1))
        body = [w for w in words if in_x(w) and any(y0 <= (w[1] + w[3]) / 2 <= y1 for y0, y1 in rows_y)]
        # columns: the gaps in the text that run through every row (8pt and more; the space
        # between two words of a cell is about 3pt)
        spans = sorted((w[0] - 2, w[2] + 2) for w in body)
        runs: list[list[float]] = []
        for x0, x1 in spans:
            if runs and x0 <= runs[-1][1]:
                runs[-1][1] = max(runs[-1][1], x1)
            else:
                runs.append([x0, x1])
        bounds = [box.x0 - 4] + [(a[1] + b[0]) / 2 for a, b in zip(runs, runs[1:]) if b[0] - a[1] >= 4] + [box.x1 + 4]
        if len(bounds) < 3:
            return box, None
        rows = []
        for y0, y1 in rows_y:
            row = []
            for x0, x1 in zip(bounds, bounds[1:]):
                ws = sorted((w for w in body if y0 <= (w[1] + w[3]) / 2 <= y1 and x0 <= (w[0] + w[2]) / 2 <= x1), key=lambda w: (w[1] + w[3]) / 2)
                text_lines: list[list[Any]] = []
                for w in ws:  # words of one line: centres within 3pt
                    if text_lines and abs((w[1] + w[3]) / 2 - (text_lines[-1][0][1] + text_lines[-1][0][3]) / 2) <= 3:
                        text_lines[-1].append(w)
                    else:
                        text_lines.append([w])
                texts = [_clean(" ".join(w[4] for w in sorted(tl, key=lambda w: w[0]))) for tl in text_lines]
                # a bullet glyph on a baseline of its own marks the line after it
                merged: list[str] = []
                for s in texts:
                    if merged and BULLET_ONLY_RE.match(merged[-1]):
                        merged[-1] = merged[-1] + " " + s
                    else:
                        merged.append(s)
                row.append("\n".join(s for s in merged if s))
            rows.append(row)
        table = self._clean_table(rows)
        if table:
            table["caption"] = table["caption"] or caption
        return box, table

    # ------------------------------------------------------------------ charts
    @staticmethod
    def _shapes(page) -> tuple[list[Any], list[Any]]:
        """The page's vector drawings split into filled shapes (bars, slices, markers, cell
        shading) and thin rules (axes, borders, underlines); page backgrounds and title bands
        are left out."""
        try:
            drawings = page.get_drawings()
        except Exception:
            return [], []
        page_area = page.rect.width * page.rect.height
        shapes, rules = [], []
        for d in drawings:
            r = d["rect"]
            if r.is_empty or r.width * r.height > 0.5 * page_area:
                continue  # page background
            if r.width <= 2.5 or r.height <= 2.5:
                if max(r.width, r.height) >= 12:
                    rules.append(r)
                continue
            if r.width >= 0.8 * page.rect.width and r.height < 40:
                continue  # a title band or a divider, not a chart
            shapes.append(r)
        return shapes, rules

    @staticmethod
    def _grow(page, box, lines, rules, repeated):
        """Grow a chart's box to the axis lines and to the short labels (ticks, legend, axis
        titles) around it, never to its caption. A body paragraph never belongs to a chart:
        when a wide line of text crosses the box (a drawing's box ran past the chart), the
        box is cut back at that line, on the side away from the chart's centre."""
        centre = (box.y0 + box.y1) / 2
        for _ in range(2):
            near = fitz.Rect(box.x0 - 24, box.y0 - 24, box.x1 + 24, box.y1 + 24)
            for r in rules:
                if near.intersects(r) and r.width < page.rect.width * 0.8:
                    box |= r
            for ln in lines:
                if ln["rect"].width < page.rect.width * 0.4 and len(ln["text"]) < 70 and near.intersects(ln["rect"]) and _norm(ln["text"]) not in repeated and not is_caption(ln["text"]):
                    box |= ln["rect"]
        for ln in sorted(lines, key=lambda ln: abs((ln["rect"].y0 + ln["rect"].y1) / 2 - centre), reverse=True):
            r = ln["rect"]
            if r.width >= page.rect.width * 0.6 and r.intersects(box) and r.y1 - r.y0 > 0 and (min(r.y1, box.y1) - max(r.y0, box.y0)) > 0.5 * r.height:
                if (r.y0 + r.y1) / 2 > centre:
                    box.y1 = min(box.y1, r.y0 - 2)
                else:
                    box.y0 = max(box.y0, r.y1 + 2)
        return box & page.rect

    def _chart_regions(self, page, lines, table_rects, repeated, all_shapes, rules, seeds=()) -> list[Any]:
        """Regions of vector drawings that make a chart: filled shapes (bars, slices, markers)
        clustered together, grown to the axis lines and the labels around them. A seed is a
        chart the table finder mistook for a table; it becomes a region of its own when its
        drawings did not cluster into one."""
        # cell shading of a confirmed table is not a chart piece; the frame of a chart that
        # the table finder mistook for a table still is
        shapes = [r for r in all_shapes if not any(_overlap(r, t) > 0.7 for t in table_rects)]
        # cluster shapes that sit within 18pt of each other
        clusters: list[list[Any]] = []
        for r in shapes:
            grown = fitz.Rect(r.x0 - 18, r.y0 - 18, r.x1 + 18, r.y1 + 18)
            hit = [c for c in clusters if any(grown.intersects(s) for s in c)]
            merged = [r]
            for c in hit:
                merged.extend(c)
                clusters.remove(c)
            clusters.append(merged)
        regions = []
        for c in clusters:
            box = fitz.Rect(c[0])
            for s in c[1:]:
                box |= s
            if len(c) < 3 and (box.width < 120 or box.height < 80):
                continue  # a lone decoration
            box = self._grow(page, box, lines, rules, repeated)
            if box.width < 100 or box.height < 60:
                continue
            if any(_overlap(box, t) > 0.5 for t in table_rects):
                continue
            regions.append((fitz.Rect(box.x0 - 4, box.y0 - 4, box.x1 + 4, box.y1 + 4) & page.rect, len(c)))
        # a region inside a bigger one is the same chart
        regions.sort(key=lambda rn: -(rn[0].width * rn[0].height))
        out: list[Any] = []
        for r, n in regions:
            if not any(_overlap(r, o) > 0.7 for o in out):
                out.append(r)
        for seed in seeds:
            if any(_overlap(seed, o) > 0.5 or _overlap(o, seed) > 0.5 for o in out):
                continue
            box = self._grow(page, fitz.Rect(seed), lines, rules, repeated)
            out.append(fitz.Rect(box.x0 - 4, box.y0 - 4, box.x1 + 4, box.y1 + 4) & page.rect)
        return out

    # ------------------------------------------------------------------ text
    @staticmethod
    def _underlines(page) -> list[Any]:
        try:
            drawings = page.get_drawings()
        except Exception:
            return []
        return [d["rect"] for d in drawings if d["rect"].height <= 2 and 15 <= d["rect"].width <= page.rect.width * 0.7]

    @staticmethod
    def _underlined(ln, underlines) -> bool:
        r = ln["rect"]
        for u in underlines:
            if r.y1 - 1.5 <= u.y0 <= r.y1 + 4 and min(r.x1, u.x1) - max(r.x0, u.x0) >= 0.6 * r.width and u.width <= 1.6 * r.width:
                return True
        return False

    def _text_blocks(self, lines, covered, repeated, body_size, underlines, page):
        """Group a page's lines into headings, paragraphs, lists and notes."""
        out = []
        by_block: dict[int, list[dict[str, Any]]] = {}
        for ln in lines:
            if self._skip_line(ln, repeated) or any(_overlap(ln["rect"], c) > 0.6 for c in covered):
                continue
            by_block.setdefault(ln["block"], []).append(ln)
        for bi, blines in sorted(by_block.items()):
            # a bullet glyph on its own line marks the line after it
            merged: list[dict[str, Any]] = []
            pending_bullet = False
            for ln in blines:
                if BULLET_ONLY_RE.match(ln["text"]):
                    pending_bullet = True
                    continue
                if pending_bullet:
                    ln = dict(ln, text="• " + BULLET_RE.sub("", ln["text"]))
                    pending_bullet = False
                merged.append(ln)
            if not merged:
                continue
            rect = merged[0]["block_rect"]
            i = 0
            while i < len(merged):
                ln = merged[i]
                text, size = ln["text"], ln["size"]
                kind = self._line_kind(ln, merged, i, body_size, underlines)
                if kind == "heading":
                    level = 1 if size >= body_size * 1.7 else (2 if size >= body_size * 1.35 else 3)
                    # a heading wrapped over several lines: the following lines of the same size
                    j = i + 1
                    while j < len(merged) and abs(merged[j]["size"] - size) < 0.6 and self._line_kind(merged[j], merged, j, body_size, underlines) == "heading" and not BULLET_RE.match(merged[j]["text"]):
                        text += " " + merged[j]["text"]
                        j += 1
                    out.append((ln["rect"].y0, ln["rect"].x0, {"type": "heading", "level": level, "text": text}))
                    i = j
                    continue
                if BULLET_RE.match(text):
                    items = []
                    while i < len(merged) and (BULLET_RE.match(merged[i]["text"]) or items):
                        t = merged[i]["text"]
                        if BULLET_RE.match(t):
                            items.append(BULLET_RE.sub("", t))
                        else:
                            items[-1] = items[-1] + " " + t  # the bullet's continuation line
                        i += 1
                    out.append((ln["rect"].y0, ln["rect"].x0, {"type": "list", "ordered": False, "items": [html.escape(x) for x in items]}))
                    continue
                # a paragraph: this line and the following plain lines of the block
                j = i + 1
                while j < len(merged) and self._line_kind(merged[j], merged, j, body_size, underlines) == "text" and not BULLET_RE.match(merged[j]["text"]):
                    j += 1
                para = " ".join(m["text"] for m in merged[i:j]).strip()
                small = max(m["size"] for m in merged[i:j]) <= body_size * 0.8
                esc = html.escape(para)
                if is_caption(para):
                    out.append((ln["rect"].y0, rect.x0, {"type": "paragraph", "html": esc, "text": para, "style": "caption"}))
                elif NOTE_RE.match(para) or small:
                    out.append((ln["rect"].y0, rect.x0, {"type": "paragraph", "html": esc, "text": para, "style": "note"}))
                else:
                    out.append((ln["rect"].y0, rect.x0, {"type": "paragraph", "html": esc, "text": para, "style": None}))
                i = j
        return out

    def _line_kind(self, ln, blines, i, body_size, underlines) -> str:
        """'heading' or 'text' for one line of a block."""
        text, size = ln["text"], ln["size"]
        if BULLET_RE.match(text) or DATE_RE.match(text) or len(re.sub(r"[^A-Za-z一-鿿]", "", text)) < 3:
            return "text"  # bullets, dates, footnote markers and bare figures are never headings
        if size >= body_size * 1.35 and len(text) < 160:
            return "heading"
        short = len(text) < 110 and not re.search(r"[.。;；,，:：]$", text)
        if short and ln["bold"] and size >= body_size * 1.02 and (len(blines) == 1 or not blines[min(i + 1, len(blines) - 1)]["bold"] or i == 0):
            return "heading"
        if short and self._underlined(ln, underlines):
            return "heading"
        # a letter's section title: a short first line, narrower than its block, followed by a
        # line that starts a sentence
        if i == 0 and len(blines) >= 2 and len(text) < 60 and short and ln["rect"].width < 0.7 * ln["block_rect"].width:
            nxt = blines[1]["text"]
            dangling = re.search(r"\b(of|and|or|the|a|an|to|for|in|on|with|by|at|from|as|is|are|&)$", text, re.I)
            if nxt[:1].isupper() and not text[:1].islower() and not re.match(r"^\d", text) and not dangling:
                return "heading"
        return "text"


def parse_pdf(path: Path, image_dir: Path) -> dict[str, Any]:
    return PdfParser(path, image_dir).parse()
