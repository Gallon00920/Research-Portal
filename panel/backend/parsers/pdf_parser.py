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

# PyMuPDF 2.x runs the optional pymupdf_layout model inside text extraction when that package
# is installed: seconds per page, and a different reading of the page from machines without
# it. This parser does its own layout analysis, so the model stays off.
if hasattr(fitz, "_layout_enabled"):
    fitz._layout_enabled = False
if hasattr(fitz, "no_recommend_layout"):
    fitz.no_recommend_layout()

BULLET_RE = re.compile(r"^(?:[•·▪◦●○■□➢➤►]\s*|[\-–—]\s+)")  # a dash is a bullet only with a space after it ("-end" is a hyphenation, "-2.5%" a figure)
BULLET_ONLY_RE = re.compile(r"^[•·▪◦●○■□➢➤►\-–—]$")
PAGE_NO_RE = re.compile(r"^(page\s*)?\d{1,3}(\s*(/|of)\s*\d{1,3})?$|^(confidential|strictly confidential)\s*[-–|]?\s*\d{0,3}$", re.I)
NOTE_RE = re.compile(r"^(source|sources|资料来源|来源|note|notes|注)[:：]", re.I)
DATE_RE = re.compile(r"^(\d{1,2}\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}|^\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|^\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}", re.I)
# private-use glyphs that Word's symbol fonts use for bullets and check marks
GLYPHS = {"": "•", "": "•", "": "•", "": "✓", "": "✗", "": "◆", "": "•", "": "•"}


# a value label of a chart: 149, $149, 12.5%, (3.2), 2.1x, -39
VALUE_RE = re.compile(r"^[-+−(]?[$€£¥]?\d[\d,.]*%?[)xX]?$")
# a figure as a panel states it: an amount, a percentage, a multiple, a decimal or a thousands number
# (a footnote marker such as "(22)" or a year is not one)
PANEL_VALUE_RE = re.compile(r"^[-+−(]?[$€£¥]\s?\d|^[-+−(]?\d[\d,.]*\s?(%|x|bn|mm|bps|m|k|b)\)?$|^\(?[-+−]?\d{1,3}(,\d{3})+\)?$|^\(?[-+−]?\d+\.\d+\)?$", re.I)
# a figure on a slide: an amount, a percentage, a multiple, a date
SLIDE_NUM_RE = re.compile(r"^\(?[-–−]?[$€£¥]?\d[\d,]*(\.\d+)?%?(bn|mm|m|k|x)?\)?$|^\d{1,2}/\d{1,2}/\d{2,4}$", re.I)
# a line led by a figure with its unit ("$115.1B Direct Lending", "~90 deals", "860+ sponsors", "40%+")
FIG_LEAD_RE = re.compile(r"^[~≈]?[$€£¥]\d|^[~≈]?\d[\d,.]*\s*(%|x|bps|bn|mm|m|k|b|\+)(?=[\s+]|$)|^\d{1,3}(,\d{3})+(?=\s|$)", re.I)


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


def _fill_rects(drawings) -> list[tuple[Any, Any]]:
    """Every filled rectangle drawn on the page as (rect, fill colour): row shading, title
    bands, bars of a bar chart, legend swatches. A rectangle drawn again in the same colour
    inside another one (cell padding) is left out."""
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
        self._drawings: list[Any] = []  # the current page's vector drawings
        self._image_infos: list[list[dict[str, Any]]] = []  # the pasted images of every page
        self._repeated_images: set[tuple[int, int, int, int]] = set()

    @staticmethod
    def _image_key(rect) -> tuple[int, int, int, int]:
        return (round(rect.x0 / 4), round(rect.y0 / 4), round(rect.x1 / 4), round(rect.y1 / 4))

    # ------------------------------------------------------------------ document
    def parse(self) -> dict[str, Any]:
        doc = fitz.open(str(self.path))
        pages_data = [page.get_text("dict") for page in doc]
        lines_by_page = [self._lines(d) for d in pages_data]
        # the body size is the size of the median character (a median over lines is dragged
        # down by pages of small table text)
        sizes = sorted((ln["size"], len(ln["text"])) for lines in lines_by_page for ln in lines if ln["text"].strip())
        half, acc, body_size = sum(n for _, n in sizes) / 2, 0, 10.0
        for size, n in sizes:
            acc += n
            if acc >= half:
                body_size = size
                break
        repeated = self._repeated(lines_by_page)
        # pasted images, read once per page; one at the same place on at least half of the
        # pages (three or more) is a banner or a logo, not a figure
        self._image_infos = []
        for page in doc:
            try:
                self._image_infos.append(page.get_image_info(xrefs=True))
            except Exception:
                self._image_infos.append([])
        count: dict[tuple[int, int, int, int], int] = {}
        for infos in self._image_infos:
            for key in {self._image_key(fitz.Rect(i["bbox"])) for i in infos}:
                count[key] = count.get(key, 0) + 1
        self._repeated_images = {k for k, c in count.items() if c >= max(3, math.ceil(len(doc) / 2))} if len(doc) >= 3 else set()

        # a slide deck (landscape pages) is read slide by slide, see _parse_slide
        deck = len(doc) >= 2 and sum(1 for page in doc if page.rect.width > page.rect.height) >= 0.8 * len(doc)
        for pno, page in enumerate(doc):
            before = len(self.blocks)
            if deck:
                self._parse_slide(page, pno, lines_by_page[pno], body_size, repeated)
            else:
                self._parse_page(page, lines_by_page[pno], body_size, repeated)
            if pno < len(doc) - 1 and len(self.blocks) > before:
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

    @classmethod
    def _lines(cls, d) -> list[dict[str, Any]]:
        """Every text line of a page with its size, weight, bbox and the block it came from.
        Some PDFs place every word on its own (each word a block of one line): their lines
        and paragraphs are rebuilt from the word positions."""
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
                out.append({"text": text, "raw": "".join(s["text"] for s in line["spans"]), "size": max(s["size"] for s in spans),
                            "bold": bold, "rot": abs(d0) < 0.9, "rect": fitz.Rect(line["bbox"]), "block": bi, "line": li,
                            "block_rect": fitz.Rect(b["bbox"]), "src": [(bi, li)], "nlines": len(b["lines"])})
        # fragmented text: lines that have a neighbour on the same baseline right next to them
        # (a word or part of a word each), or mostly single-word blocks
        single = sum(1 for ln in out if " " not in ln["text"].strip() and ln["nlines"] == 1)
        by_row = sorted(out, key=lambda ln: (round(ln["rect"].y1), ln["rect"].x0))
        adjacent = 0
        for a, b in zip(by_row, by_row[1:]):
            if abs(a["rect"].y1 - b["rect"].y1) <= 2 and -2 <= b["rect"].x0 - a["rect"].x1 <= 0.7 * max(a["size"], b["size"]):
                adjacent += 1
        if len(out) >= 8 and (single >= 0.6 * len(out) or adjacent >= 0.2 * len(out)):
            out = cls._rebuild_lines(out)
        return out

    @staticmethod
    def _rebuild_lines(frags) -> list[dict[str, Any]]:
        """Join word fragments into lines: fragments that overlap vertically form a row (a
        superscript footnote marker sits in its line), the row is read left to right, and a
        gap wider than 0.7 of the font size splits it (a column); fragments that touch (a
        number and its % sign) are joined without a space. Lines that follow each other
        closely then form blocks (paragraphs)."""
        # rows: fragments whose vertical centres lie within half a font size of the row's
        # (a superscript sits a little higher, the next text line a whole line lower)
        rows: list[list[dict[str, Any]]] = []
        centres: list[float] = []
        for f in sorted(frags, key=lambda ln: ((ln["rect"].y0 + ln["rect"].y1) / 2, ln["rect"].x0)):
            yc = (f["rect"].y0 + f["rect"].y1) / 2
            for row, c in zip(rows, centres):
                if abs(yc - c) <= 0.45 * min(f["size"], row[0]["size"]) and f["rot"] == row[0]["rot"]:
                    row.append(f)
                    break
            else:
                rows.append([f])
                centres.append(yc)
        lines: list[dict[str, Any]] = []
        for row in rows:
            row.sort(key=lambda x: x["rect"].x0)
            big = max(x["size"] for x in row)
            # the fragments' widths are often wrong (a font whose advance widths differ from
            # the glyphs drawn): fragments overlap, or leave a gap where there is none. Only
            # where the next fragment starts is exact, and that is scale * width + a space:
            # the scale is fitted across the row (a robust slope, so a column gap or a wide
            # justified space does not pull it) and the widths are corrected by it
            pairs = [(a["rect"].width, b["rect"].x0 - a["rect"].x0, a["size"]) for a, b in zip(row, row[1:])
                     if a["rect"].width > 2 and len(a["text"].strip()) >= 2 and not a["rot"] and 0.5 <= (b["rect"].x0 - a["rect"].x0) / a["rect"].width <= 2]
            scale = 1.0
            if len(pairs) >= 2:
                slopes = [(d2 - d1) / (w2 - w1) for i, (w1, d1, _) in enumerate(pairs) for (w2, d2, _) in pairs[i + 1:] if abs(w2 - w1) >= 4]
                if slopes:
                    scale = statistics.median(slopes)
            elif len(pairs) == 1:
                w, delta, sz = pairs[0]
                scale = (delta - 0.25 * sz) / w
            if not (0.7 <= scale <= 1.4) or abs(scale - 1) <= 0.04:
                scale = 1.0
            if scale != 1.0:
                for f in row:
                    f["rect"] = fitz.Rect(f["rect"].x0, f["rect"].y0, f["rect"].x0 + f["rect"].width * scale, f["rect"].y1)
            cur: dict[str, Any] | None = None
            for f in row:
                r = f["rect"]
                if f["size"] < 0.7 * big and re.fullmatch(r"[\d,]+", f["text"]) and cur is not None:
                    cur["src"].extend(f["src"])
                    cur["rect"] = cur["rect"] | r  # a superscript footnote marker: the line goes on after it
                    continue
                if cur is not None:
                    gap = r.x0 - cur["rect"].x1
                    size = max(f["size"], cur["size"])
                    numbered = re.fullmatch(r"\(?\d{1,2}[.)]?|[•·▪◦●○■□➢➤►\-–—]", cur["text"]) and gap <= 3 * size
                    # an overlap is never a column boundary (columns do not overlap), only a width
                    # the fit left too wide, so any gap up to a space-and-a-bit joins
                    if (gap <= 0.7 * size or numbered) and not f["rot"]:
                        hyphen = f["raw"].strip() == "-" or (cur["raw"].rstrip().endswith("-") and cur["raw"].rstrip()[-2:-1].isalpha())
                        tight = gap <= 0.08 * size or hyphen or re.match(r"[.,;:)\]%’”'\"]", f["raw"].lstrip()) or re.search(r"[(\[“‘$]$", cur["raw"].rstrip())
                        glue = "" if tight or cur["raw"].endswith(" ") or f["raw"].startswith(" ") else " "
                        cur["raw"] += glue + f["raw"]
                        cur["text"] = _clean(cur["raw"])
                        cur["size"] = max(cur["size"], f["size"])
                        cur["bold"] = cur["bold"] and f["bold"]
                        cur["rect"] = cur["rect"] | r
                        cur["src"].extend(f["src"])
                        continue
                cur = dict(f, src=list(f["src"]), rect=fitz.Rect(r))
                lines.append(cur)
        lines.sort(key=lambda ln: (ln["rect"].y0, ln["rect"].x0))
        # blocks: a line joins a recent block when it follows its last line closely and
        # overlaps it in x (the columns of a page interleave, so the last few blocks are tried)
        blocks: list[list[dict[str, Any]]] = []
        for ln in lines:
            joined = False
            for blk in blocks[-8:][::-1]:
                prev = blk[-1]
                gap = ln["rect"].y0 - prev["rect"].y1
                overlap_x = min(ln["rect"].x1, prev["rect"].x1) - max(ln["rect"].x0, prev["rect"].x0)
                if -2 <= gap <= 0.6 * max(ln["size"], prev["size"]) and overlap_x > 0 and abs(ln["size"] - prev["size"]) < 1.5:
                    blk.append(ln)
                    joined = True
                    break
            if not joined:
                blocks.append([ln])
        out = []
        for bi, blk in enumerate(blocks):
            rect = fitz.Rect(blk[0]["rect"])
            for ln in blk[1:]:
                rect |= ln["rect"]
            for li, ln in enumerate(blk):
                out.append(dict(ln, block=bi, line=li, block_rect=rect, nlines=len(blk)))
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
        try:
            self._drawings = page.get_drawings()  # read once per page: it is the slow call
        except Exception:
            self._drawings = []

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
        junk = {pair for ln in lines if _norm(ln["text"]) in repeated for pair in ln["src"]}
        words = [w for w in page.get_text("words") if (w[5], w[6]) not in junk] if cands else []
        shapes, rules, dividers = self._shapes(page, self._drawings)
        fills = _fill_rects(self._drawings) if cands else []
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
            if table and len(table["rows"]) <= 2 and (max(c.count("\n") for r in table["rows"] for c in r) >= 2
                                                      or any(c[:1].islower() or c.endswith(".") for c in table["rows"][0])):
                continue  # a panel of label/value lines boxed by rules, or a box drawn over a sentence: not a table
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
        chart_rects = self._chart_regions(page, lines, strong, repeated, shapes, rules, dividers, seeds)
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
        # a drawing without any label and smaller than about 160pt square is an icon, not a chart
        chart_rects = [c for c in chart_rects if c.width * c.height >= 25000 or sum(1 for ln in lines if _overlap(ln["rect"], c) > 0.8) >= 2]
        # a table shown as a picture and the chart regions next to it are joined the same way
        chart_rects = self._join_regions(chart_rects + pictures, lines)
        pictures = []
        for rect in pictures:
            if not any(_overlap(rect, c) > 0.6 for c in covered):
                self._add_image(page, rect, items, covered)

        # a cover page (the first page, with hardly any text) shows a picture or a decoration,
        # not a figure: nothing on it becomes an exhibit
        cover = page.number == 0 and sum(len(ln["text"]) for ln in lines) < 400
        if cover:
            chart_rects, pictures = [], []

        # vector charts first: the slices of a donut or the logos of a panel are often pasted
        # bitmaps inside the chart's region, and must not come out again one by one
        for rect in chart_rects:
            if any(_overlap(rect, c) > 0.6 for c in covered):
                continue
            self._add_image(page, rect, items, covered)

        # pasted images (photos, charts saved as pictures). Bitmaps that touch each other are
        # the pieces of one picture (a chart drawn slice by slice, a wall of logos)
        infos = [] if cover else (self._image_infos[page.number] if page.number < len(self._image_infos) else [])
        pasted: list[Any] = []
        for info in infos:
            rect = fitz.Rect(info["bbox"]) & page.rect
            if rect.width < 12 or rect.height < 12 or rect.width * rect.height > 0.9 * page_area:
                continue
            if self._image_key(rect) in self._repeated_images:
                continue  # the same picture at the same place on most pages: a banner or a logo
            if rect.height >= 0.9 * page.rect.height and rect.width < 0.35 * page.rect.width:
                continue  # a decorative side band
            if any(_overlap(rect, c) > 0.6 for c in covered):
                continue
            pasted.append(rect)
        merged = True
        while merged:
            merged = False
            for i in range(len(pasted)):
                for j in range(i + 1, len(pasted)):
                    a, b = pasted[i], pasted[j]
                    if a.x0 - 6 <= b.x1 and b.x0 - 6 <= a.x1 and a.y0 - 6 <= b.y1 and b.y0 - 6 <= a.y1:
                        pasted[i] = a | b
                        pasted.pop(j)
                        merged = True
                        break
                if merged:
                    break
        for rect in pasted:
            if rect.width < 40 or rect.height < 40:
                continue
            # a small bitmap (under about 120pt square) is an icon or a logo, not a figure
            if rect.width * rect.height < 15000 and max(rect.width, rect.height) < 160:
                continue
            inside = [ln for ln in lines if _overlap(ln["rect"], rect) > 0.8]
            if rect.width * rect.height > 0.5 * page_area and len(inside) >= 12:
                continue  # a page background with the text set over it (a slide of bitmap only still counts)
            if inside and sum(ln["rect"].height for ln in inside) >= 0.5 * rect.height:
                continue  # text drawn as bitmaps, or a bitmap behind a paragraph: the text fills it, a chart's labels are sparse
            self._add_image(page, rect, items, covered)

        # boxed layouts that are not prose (tiles of key figures, labelled boxes, diagrams of
        # shapes with short labels) are kept as pictures: read as text they come out as fragments
        if not cover:
            for rect in self._panel_regions(page, lines, covered, repeated, body_size):
                if not any(_overlap(rect, c) > 0.6 for c in covered):
                    self._add_image(page, rect, items, covered)

        # text, line by line
        underlines = self._underlines(page, self._drawings)
        for blk in self._text_blocks(lines, covered, repeated, body_size, underlines, page):
            items.append(blk)

        items.sort(key=lambda it: (round(it[0] / 8), it[1]))
        for _, _, blk in items:
            if blk["type"] == "list" and self.blocks and self.blocks[-1]["type"] == "list" and self.blocks[-1]["ordered"] == blk["ordered"]:
                self.blocks[-1]["items"].extend(blk["items"])
                continue
            self.blocks.append(blk)

    # ------------------------------------------------------------------ boxed panels
    def _panel_regions(self, page, lines, covered, repeated, body_size: float) -> list[Any]:
        """The page's boxed panels: filled boxes whose text is short labels and figures rather
        than sentences (a strip of key-figure tiles, a sidebar of metrics, a diagram), grouped
        when they sit together. A table's bands, a decorative side band, a call-out of sentences
        and a lone label chip are not panels."""
        w, h = page.rect.width, page.rect.height
        page_area = w * h
        boxes: list[tuple[Any, int]] = []
        for r, _col in _fill_rects(self._drawings):
            area = r.width * r.height
            if r.width < 40 or r.height < 2.2 * body_size or area < 0.003 * page_area or area > 0.6 * page_area:
                continue
            if r.width > 0.6 * w and r.height < 3.5 * body_size:
                continue  # a title or header band of a table
            if r.height >= 0.9 * h and r.width < 0.35 * w:
                continue  # a decorative side band
            if any(_overlap(r, c) > 0.5 for c in covered):
                continue
            inside = [ln for ln in lines if _overlap(ln["rect"], r) > 0.8 and not self._skip_line(ln, repeated)]
            if not inside:
                continue
            short = sum(1 for ln in inside if len(ln["text"].split()) <= 5 or VALUE_RE.match(ln["text"].strip()))
            if short < 0.8 * len(inside):
                continue  # a call-out of sentences stays text
            boxes.append((r, len(inside)))
        if not boxes:
            return []
        # tiles in a strip or a grid belong together: boxes within 24pt of each other are one panel
        groups: list[list[tuple[Any, int]]] = []
        for r, n in boxes:
            near = [g for g in groups if any(a.x0 - 24 <= r.x1 and r.x0 - 24 <= a.x1 and a.y0 - 24 <= r.y1 and r.y0 - 24 <= a.y1 for a, _ in g)]
            if not near:
                groups.append([(r, n)])
                continue
            near[0].append((r, n))
            for g in near[1:]:
                near[0].extend(g)
                g.clear()
        out = []
        kept = [ln for ln in lines if not self._skip_line(ln, repeated)]
        for g in groups:
            if not g or (len(g) < 2 and g[0][1] < 2):
                continue  # one box with one label: a chip or a heading band, not a panel
            box = fitz.Rect(min(r.x0 for r, _ in g), min(r.y0 for r, _ in g), max(r.x1 for r, _ in g), max(r.y1 for r, _ in g))
            inside = sum(n for _, n in g)
            # label boxes beside rows of text (a column of section labels next to bullets) belong
            # to that text, not to a panel: the text beside the boxes outweighs the text in them
            beside = [ln for ln in kept if box.y0 <= (ln["rect"].y0 + ln["rect"].y1) / 2 <= box.y1
                      and (ln["rect"].x0 >= box.x1 - 2 or ln["rect"].x1 <= box.x0 + 2)]
            if len(beside) >= inside:
                continue
            # a panel holds figures: a tile or a sidebar states numbers. Boxes of words only (a
            # shaded cell with a name in it, a column of labels, a diagram of named shapes) are not
            # pictured, so a dense filing never loses a cell to a crop
            with_value = sum(1 for r, _ in g if any(PANEL_VALUE_RE.match(ln["text"].strip()) for ln in kept if _overlap(ln["rect"], r) > 0.8))
            if with_value < 1 or (len(g) < 2 and not any(n >= 2 for _, n in g)):
                continue
            out.append(fitz.Rect(box.x0 - 3, box.y0 - 3, box.x1 + 3, box.y1 + 3) & page.rect)
        return self._join_regions(out, lines)

    # ------------------------------------------------------------------ slide decks
    # A deck is kept as slides: the slide's title becomes a heading, and a slide that carries
    # tables, charts or tiles of figures is kept as one picture of its body (everything between
    # the title and the footer), so nothing drawn is lost or rewritten as text. A slide of prose
    # (a review, endnotes, disclosures) is read as text like a report page. The cover is the
    # document's title only.
    def _parse_slide(self, page, pno: int, lines, body_size: float, repeated: set[str]):
        w, h = page.rect.width, page.rect.height
        kept = [ln for ln in lines if not self._skip_line(ln, repeated)]
        if pno == 0 and (len(page.get_text("text")) < 400 or len(kept) <= 12):
            return  # the cover: a title, a date, a disclaimer line
        try:
            self._drawings = page.get_drawings()
        except Exception:
            self._drawings = []
        # the title: the largest text in the top part of the slide (one or two lines of it)
        top = [ln for ln in kept if ln["rect"].y1 <= 0.24 * h]
        title, title_bottom = "", 0.0
        if top:
            big = max(ln["size"] for ln in top)
            tl = sorted((ln for ln in top if ln["size"] >= big - 0.5), key=lambda ln: (round(ln["rect"].y0), ln["rect"].x0))
            title = _clean(" ".join(ln["text"] for ln in tl))
            title_bottom = max(ln["rect"].y1 for ln in tl)
        # the footer: the disclaimer, the ticker and the page number along the bottom edge
        footer = [ln for ln in lines if ln["rect"].y0 >= 0.9 * h and ln["text"].strip()]
        footer_top = min((ln["rect"].y0 for ln in footer), default=h)
        # a slide of figures: filled shapes below the title (table bands, bars, tiles), a share of
        # numeric words, or a pasted picture that is not the deck's logo
        # filled shapes of some size (a table band, a bar, a tile); the pieces of a logo are not counted
        fills = [d for d in self._drawings if d.get("fill") and d["rect"].width > 3 and d["rect"].height > 3 and d["rect"].y0 >= title_bottom
                 and d["rect"].width * d["rect"].height >= 0.0015 * w * h]
        words = [t[4].strip(",;:") for t in page.get_text("words") if t[1] >= title_bottom and t[3] <= footer_top]
        numeric = sum(1 for t in words if SLIDE_NUM_RE.match(t)) / len(words) if words else 0.0
        # a pasted picture of some size (a chart saved as a bitmap); words drawn as bitmaps are small
        pictures = [i for i in self._image_infos[pno] if self._image_key(fitz.Rect(i["bbox"])) not in self._repeated_images
                    and fitz.Rect(i["bbox"]).width * fitz.Rect(i["bbox"]).height > 0.05 * w * h and min(fitz.Rect(i["bbox"]).width, fitz.Rect(i["bbox"]).height) >= 60]
        # a chart with few bars has few fills: its text is all short labels (a slide of prose is not)
        kept_body = [ln for ln in kept if ln["rect"].y0 >= title_bottom - 1 and ln["rect"].y0 < footer_top]
        short = sum(1 for ln in kept_body if len(ln["text"].split()) <= 4) / len(kept_body) if kept_body else 0.0
        # columns of figures with their captions ("$115.1B Direct Lending") are a layout, not prose
        figure_lines = sum(1 for ln in kept_body if FIG_LEAD_RE.match(ln["text"].strip()) and len(ln["text"].split()) <= 6)
        # a layout in lanes: lines starting in three or more columns spread across the slide (tiles with
        # captions, labelled rows with side notes); prose and its indented bullets start in one or two
        lanes: dict[int, int] = {}
        for ln in kept_body:
            lanes[round(ln["rect"].x0 / 20)] = lanes.get(round(ln["rect"].x0 / 20), 0) + 1
        cols = sorted(k for k, n in lanes.items() if n >= 3)
        # a layout has a few columns; text drawn word by word (bitmap fonts) starts everywhere
        laned = 3 <= len(cols) <= 6 and (cols[-1] - cols[0]) * 20 >= 0.4 * w
        graphic = len(fills) >= 6 or numeric >= 0.25 or bool(pictures) or (len(fills) >= 3 and short >= 0.85) or figure_lines >= 5 or laned
        if not graphic:
            self._parse_page(page, lines, body_size, repeated)
            return
        if title:
            self.blocks.append({"type": "heading", "level": 1, "text": title})
        # the body: everything drawn or written between the title and the footer
        boxes = [ln["rect"] for ln in kept if ln["rect"].y0 >= title_bottom - 1 and ln["rect"].y1 <= footer_top + 1]
        boxes += [d["rect"] for d in self._drawings if d["rect"].y0 >= title_bottom - 1 and d["rect"].y1 <= footer_top + 1 and d["rect"].width < 0.98 * w]
        boxes += [fitz.Rect(i["bbox"]) for i in pictures]
        if not boxes:
            return
        body = fitz.Rect(min(b.x0 for b in boxes), min(b.y0 for b in boxes), max(b.x1 for b in boxes), max(b.y1 for b in boxes))
        body = fitz.Rect(max(0, body.x0 - 8), max(title_bottom + 2, body.y0 - 8), min(w, body.x1 + 8), min(footer_top - 2, body.y1 + 8))
        if body.width < 40 or body.height < 40:
            return
        items: list[tuple[float, float, dict[str, Any]]] = []
        self._add_image(page, body, items, [])
        for _, _, blk in items:
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
                    inside.sort(key=lambda w: ((w[1] + w[3]) / 2, w[0]))
                    tls: list[list[Any]] = []
                    for w in inside:  # the lines of the cell
                        if tls and abs((w[1] + w[3]) / 2 - (tls[-1][0][1] + tls[-1][0][3]) / 2) <= 3:
                            tls[-1].append(w)
                        else:
                            tls.append([w])
                    cells.append("\n".join(_clean(" ".join(w[4] for w in sorted(tl, key=lambda w: w[0]))) for tl in tls))
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
        # a column holding nothing but currency signs belongs to the figures on its right, one
        # of percent signs or closing brackets to the figures on its left (financial statements
        # set "$", "1,234", "%" in cells of their own)
        j = 0
        while j < len(rows[0]) if rows else False:
            col = [r[j] for r in rows]
            filled = [c for c in col if c]
            if filled and all(c in ("$", "€", "£", "¥", "US$") for c in filled) and j + 1 < len(rows[0]):
                for r in rows:
                    if r[j] and r[j + 1]:
                        r[j + 1] = r[j] + r[j + 1]
                    r.pop(j)
                continue
            if filled and all(c in ("%", ")", "%)") for c in filled) and j > 0:
                for r in rows:
                    if r[j] and r[j - 1]:
                        r[j - 1] = r[j - 1] + r[j]
                    r.pop(j)
                continue
            j += 1
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
        if rect.width * rect.height > 0.8 * page.rect.width * page.rect.height:
            return "junk"  # the page itself (a sidebar or a frame split it into "cells")
        wide = [ln for ln in lines if ln["rect"].intersects(rect) and ln["rect"].width > 0.6 * page.rect.width
                and not any(_overlap(ln["rect"], c) > 0.9 for c in cells)]
        if len(wide) >= 2:
            return "junk"
        diag = curves = 0
        for d in self._drawings:
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
            if i > 0 and luma < 0.5 and not cell_row(r.y0, r.y1):
                box.y1 = r.y0  # the dark title band of the next section: the table ends above it
                break
            if r.y0 - prev >= 6:
                rows_y.append((prev, r.y0))
            if i == 0 and luma < 0.5 and r.y0 - box.y0 < 6 and not cell_row(r.y0, r.y1):
                caption = _clean(" ".join(w[4] for w in sorted((w for w in words if in_x(w) and r.y0 <= (w[1] + w[3]) / 2 <= r.y1), key=lambda w: w[0])))
            else:
                rows_y.append((r.y0, r.y1))
            prev = r.y1
        if box.y1 - prev >= 6:
            rows_y.append((prev, box.y1))
        # a sentence inside a row (a note under the title band, running across the columns) is
        # not cell text: it becomes the table's note
        notes: list[str] = []
        dropped: set[int] = set()
        for y0, y1 in rows_y:
            ws = sorted((w for w in words if in_x(w) and y0 <= (w[1] + w[3]) / 2 <= y1), key=lambda w: ((w[1] + w[3]) / 2, w[0]))
            tls: list[list[Any]] = []
            for w in ws:
                if tls and abs((w[1] + w[3]) / 2 - (tls[-1][0][1] + tls[-1][0][3]) / 2) <= 3:
                    tls[-1].append(w)
                else:
                    tls.append([w])
            for tl in tls:
                tl.sort(key=lambda w: w[0])
                end, gap = tl[0][2], 0.0
                for w in tl[1:]:
                    gap = max(gap, w[0] - end)
                    end = max(end, w[2])
                if gap < 10 and tl[-1][2] - tl[0][0] >= 0.6 * box.width and len(tl) >= 6:
                    notes.append(_clean(" ".join(w[4] for w in tl)))
                    dropped.update(id(w) for w in tl)
        words = [w for w in words if id(w) not in dropped]

        def sentence_row(y0, y1) -> bool:
            """A row whose words run on without a cell gap across most of the box: a note or a
            sentence above or below the table, not a row of it."""
            ws = sorted((w for w in words if in_x(w) and y0 <= (w[1] + w[3]) / 2 <= y1), key=lambda w: w[0])
            return bool(ws) and not cell_row(y0, y1) and ws[-1][2] - ws[0][0] >= 0.6 * box.width

        while rows_y and sentence_row(*rows_y[0]):
            rows_y.pop(0)
        while rows_y and sentence_row(*rows_y[-1]):
            rows_y.pop()
        if not rows_y:
            return box, None
        box = fitz.Rect(box.x0, min(box.y0, rows_y[0][0]) if caption else rows_y[0][0], box.x1, rows_y[-1][1])
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
            table["note"] = " ".join(notes)
        return box, table

    # ------------------------------------------------------------------ charts
    @staticmethod
    def _shapes(page, drawings) -> tuple[list[Any], list[Any], list[Any]]:
        """The page's vector drawings split into filled shapes (bars, slices, markers, cell
        shading), thin rules (axes, borders, underlines) and dividers (bands and rules across
        the page, which separate the sections of a slide); page backgrounds are left out."""
        page_area = page.rect.width * page.rect.height
        shapes, rules = [], []
        dividers = []
        for d in drawings:
            r = d["rect"]
            if r.is_empty or r.width * r.height > 0.5 * page_area:
                continue  # page background
            if r.width <= 2.5 or r.height <= 2.5:
                if max(r.width, r.height) >= 12:
                    rules.append(r)
                    if r.width >= 0.8 * page.rect.width:
                        dividers.append(r)
                continue
            if r.width >= 0.8 * page.rect.width and r.height < 40:
                dividers.append(r)
                continue  # a title band or a divider, not a chart
            if not d.get("color") and _luma(d.get("fill")) > 0.97:
                continue  # an invisible panel background (white, no border) joins nothing
            if r.width * r.height > 0.15 * page_area or (r.height >= 0.9 * page.rect.height and r.width < 0.35 * page.rect.width):
                continue  # a slide panel or a side band: a backdrop for text, which would chain every chart on the page
            shapes.append(r)
        return shapes, rules, dividers

    @staticmethod
    def _grow(page, box, lines, rules, repeated, dividers=()):
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
                if ln["rect"].width < page.rect.width * 0.4 and len(ln["text"]) < 70 and near.intersects(ln["rect"]) and _norm(ln["text"]) not in repeated and not is_caption(ln["text"]) \
                        and not (ln["bold"] and len(ln["text"]) > 12):  # a bold title belongs to the next chart or section, not to this one
                    yc = (ln["rect"].y0 + ln["rect"].y1) / 2
                    if any(min(box.y1, yc) <= (dv.y0 + dv.y1) / 2 <= max(box.y0, yc) for dv in dividers):
                        continue  # a section divider lies between the chart and the line
                    box |= ln["rect"]
        for ln in sorted(lines, key=lambda ln: abs((ln["rect"].y0 + ln["rect"].y1) / 2 - centre), reverse=True):
            r = ln["rect"]
            if r.width >= page.rect.width * 0.6 and r.intersects(box) and r.y1 - r.y0 > 0 and (min(r.y1, box.y1) - max(r.y0, box.y0)) > 0.5 * r.height:
                if (r.y0 + r.y1) / 2 > centre:
                    box.y1 = min(box.y1, r.y0 - 2)
                else:
                    box.y0 = max(box.y0, r.y1 + 2)
        return box & page.rect

    def _chart_regions(self, page, lines, table_rects, repeated, all_shapes, rules, dividers=(), seeds=()) -> list[Any]:
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
            box = self._grow(page, box, lines, rules, repeated, dividers)
            if box.width < 100 or box.height < 60:
                continue
            if any(_overlap(box, t) > 0.5 for t in table_rects):
                continue
            # a call-out: one or two filled panels with sentences on them (a chart's labels are short)
            inside = [ln["text"] for ln in lines if _overlap(ln["rect"], box) > 0.8]
            if len(c) <= 2 and inside and sum(len(x) for x in inside) >= 80 and sum(len(x) for x in inside) / len(inside) >= 40:
                continue
            regions.append((fitz.Rect(box.x0 - 4, box.y0 - 4, box.x1 + 4, box.y1 + 4) & page.rect, len(c)))
        # regions that overlap are one chart (its parts clustered apart, a region inside a
        # bigger one): they are joined into their union until none overlap
        regions.sort(key=lambda rn: -(rn[0].width * rn[0].height))
        out = self._join_regions([fitz.Rect(r) for r, n in regions], lines)
        for seed in seeds:
            if any(_overlap(seed, o) > 0.5 or _overlap(o, seed) > 0.5 for o in out):
                continue
            box = self._grow(page, fitz.Rect(seed), lines, rules, repeated, dividers)
            out.append(fitz.Rect(box.x0 - 4, box.y0 - 4, box.x1 + 4, box.y1 + 4) & page.rect)
        return out

    @staticmethod
    def _join_regions(out: list[Any], lines) -> list[Any]:
        """Join the rectangles that are parts of one figure into their union, until none are:
        rectangles that overlap, and parts that sit stacked or side by side."""
        joined = True
        while joined:
            joined = False
            for i in range(len(out)):
                for j in range(i + 1, len(out)):
                    a, b = out[i], out[j]
                    inter = a & b
                    overlapping = not inter.is_empty and inter.get_area() > 0.3 * min(a.get_area(), b.get_area())
                    # stacked or side-by-side parts of one figure: a small gap, aligned on the other axis
                    x_share = min(a.x1, b.x1) - max(a.x0, b.x0)
                    y_share = min(a.y1, b.y1) - max(a.y0, b.y0)
                    v_gap, h_gap = max(a.y0, b.y0) - min(a.y1, b.y1), max(a.x0, b.x0) - min(a.x1, b.x1)
                    stacked = (v_gap <= 8 and x_share >= 0.6 * min(a.width, b.width)) or (h_gap <= 8 and y_share >= 0.6 * min(a.height, b.height))
                    # the same-width parts of one table or chart may sit further apart (an unshaded
                    # row between the shaded ones), unless a title in between starts another figure
                    if not stacked and v_gap <= 40 and x_share >= 0.9 * min(a.width, b.width):
                        top, bottom = min(a.y1, b.y1), max(a.y0, b.y0)
                        # a title runs across the figure; a bold row label of a table ("Core Expenses") does not
                        titled = any(ln["bold"] and ln["rect"].width >= 0.5 * min(a.width, b.width) and top <= (ln["rect"].y0 + ln["rect"].y1) / 2 <= bottom
                                     and ln["rect"].x1 > min(a.x0, b.x0) and ln["rect"].x0 < max(a.x1, b.x1) for ln in lines)
                        stacked = not titled
                    if overlapping or stacked:
                        out[i] = a | b
                        out.pop(j)
                        joined = True
                        break
                if joined:
                    break
        return out

    # ------------------------------------------------------------------ text
    @staticmethod
    def _underlines(page, drawings) -> list[Any]:
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
        para_like = len(blines) >= 3 and sum(len(b["text"]) for b in blines) > 200 and all(abs(b["size"] - size) < 1 for b in blines)
        if size >= body_size * 1.35 and len(text) < 110 and not para_like and not re.search(r"[.。;；,，]$", text):
            return "heading"
        short = len(text) < 110 and not re.search(r"[.。;；,，:：]$", text)
        if short and ln["bold"] and size >= body_size * 1.02 and (len(blines) == 1 or not blines[min(i + 1, len(blines) - 1)]["bold"] or i == 0):
            return "heading"
        if short and self._underlined(ln, underlines):
            return "heading"
        # a letter's section title: a short first line, narrower than its block, followed by a
        # line that starts a sentence
        if i == 0 and len(blines) >= 2 and len(text) < 60 and short and ln["rect"].width < 0.7 * ln["block_rect"].width and ln["rect"].x0 - ln["block_rect"].x0 < 12:
            nxt = blines[1]["text"]
            dangling = re.search(r"\b(of|and|or|the|a|an|to|for|in|on|with|by|at|from|as|is|are|&)$", text, re.I)
            if nxt[:1].isupper() and not text[:1].islower() and not re.match(r"^\d", text) and not dangling and not re.search(r"[,，/]", text):
                return "heading"
        return "text"


def parse_pdf(path: Path, image_dir: Path) -> dict[str, Any]:
    return PdfParser(path, image_dir).parse()
