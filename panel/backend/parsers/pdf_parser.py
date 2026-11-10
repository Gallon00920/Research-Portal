"""Parse a PDF report into the same block list the docx parser produces."""
from __future__ import annotations

import html
import re
import statistics
from pathlib import Path
from typing import Any

from .common import attach_captions, build_exhibits, guess_language, is_caption

try:
    import pymupdf as fitz  # type: ignore
except Exception:  # pragma: no cover
    import fitz  # type: ignore


def _rect_overlap(a, b) -> float:
    x0, y0 = max(a.x0, b.x0), max(a.y0, b.y0)
    x1, y1 = min(a.x1, b.x1), min(a.y1, b.y1)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    inter = (x1 - x0) * (y1 - y0)
    return inter / max(1e-6, (a.x1 - a.x0) * (a.y1 - a.y0))


class PdfParser:
    def __init__(self, path: Path, image_dir: Path):
        self.path = Path(path)
        self.image_dir = Path(image_dir)
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.blocks: list[dict[str, Any]] = []
        self._img_n = 0

    def parse(self) -> dict[str, Any]:
        doc = fitz.open(str(self.path))
        sizes: list[float] = []
        pages_data = []
        for page in doc:
            d = page.get_text("dict")
            for b in d["blocks"]:
                if b.get("type") != 0:
                    continue
                for line in b["lines"]:
                    for span in line["spans"]:
                        if span["text"].strip():
                            sizes.append(round(span["size"], 1))
            pages_data.append(d)
        body_size = statistics.median(sizes) if sizes else 10.0

        for pno, page in enumerate(doc):
            self._parse_page(page, pages_data[pno], body_size)
            if pno < len(doc) - 1:
                self.blocks.append({"type": "pagebreak"})

        blocks = attach_captions(self.blocks)
        exhibits = build_exhibits(blocks)
        text = " ".join(b.get("text", "") for b in blocks if b.get("type") in ("paragraph", "heading"))
        meta = doc.metadata or {}
        title = (meta.get("title") or "").strip()
        if not title or len(title) < 4:
            for b in blocks:
                if b["type"] == "heading":
                    title = b["text"]
                    break
        title = title or self.path.stem
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

    def _parse_page(self, page, d, body_size: float):
        items: list[tuple[float, float, dict[str, Any]]] = []  # (y, x, block)
        covered: list[Any] = []

        # tables first so their text is not duplicated as paragraphs
        try:
            tabs = page.find_tables()
            for t in tabs.tables:
                rows = t.extract()
                rows = [[(c or "").strip() for c in r] for r in rows if any((c or "").strip() for c in r)]
                if len(rows) >= 2 and max(len(r) for r in rows) >= 2:
                    rect = fitz.Rect(t.bbox)
                    covered.append(rect)
                    items.append((rect.y0, rect.x0, {"type": "table", "rows": rows, "header": True, "caption": "", "exhibit": None, "note": ""}))
        except Exception:
            pass

        # images (rendered from the page region so vector charts also work)
        try:
            infos = page.get_image_info(xrefs=True)
        except Exception:
            infos = []
        seen = set()
        for info in infos:
            rect = fitz.Rect(info["bbox"])
            if rect.width < 40 or rect.height < 40:
                continue
            key = (round(rect.x0), round(rect.y0), round(rect.x1), round(rect.y1))
            if key in seen:
                continue
            seen.add(key)
            try:
                pix = page.get_pixmap(clip=rect, dpi=150)
                self._img_n += 1
                name = f"img_{self._img_n:03d}.png"
                pix.save(str(self.image_dir / name))
            except Exception:
                continue
            covered.append(rect)
            items.append((rect.y0, rect.x0, {"type": "image", "src": name, "caption": "", "exhibit": None, "width": rect.width, "height": rect.height, "note": ""}))

        # vector drawings clusters (charts drawn as paths)
        try:
            clusters = page.cluster_drawings()
        except Exception:
            clusters = []
        for rect in clusters:
            if rect.width < 120 or rect.height < 80:
                continue
            if any(_rect_overlap(rect, c) > 0.5 for c in covered):
                continue
            try:
                pix = page.get_pixmap(clip=rect, dpi=150)
                self._img_n += 1
                name = f"img_{self._img_n:03d}.png"
                pix.save(str(self.image_dir / name))
            except Exception:
                continue
            covered.append(rect)
            items.append((rect.y0, rect.x0, {"type": "image", "src": name, "caption": "", "exhibit": None, "width": rect.width, "height": rect.height, "note": ""}))

        # text
        for b in d["blocks"]:
            if b.get("type") != 0:
                continue
            rect = fitz.Rect(b["bbox"])
            if any(_rect_overlap(rect, c) > 0.6 for c in covered):
                continue
            lines_txt = []
            max_size = 0.0
            bold = False
            for line in b["lines"]:
                t = "".join(s["text"] for s in line["spans"])
                if t.strip():
                    lines_txt.append(t.strip())
                for s in line["spans"]:
                    if s["text"].strip():
                        max_size = max(max_size, s["size"])
                        if "bold" in (s.get("font") or "").lower() or (s.get("flags", 0) & 16):
                            bold = True
            text = " ".join(lines_txt).strip()
            if not text:
                continue
            esc = html.escape(text)
            if max_size >= body_size * 1.35 and len(text) < 160:
                level = 1 if max_size >= body_size * 1.7 else 2
                items.append((rect.y0, rect.x0, {"type": "heading", "level": level, "text": text}))
            elif bold and len(text) < 120 and max_size >= body_size * 1.05:
                items.append((rect.y0, rect.x0, {"type": "heading", "level": 3, "text": text}))
            elif is_caption(text):
                items.append((rect.y0, rect.x0, {"type": "paragraph", "html": esc, "text": text, "style": "caption"}))
            elif re.match(r"^(source|资料来源|来源|note|注)[:：]", text, re.I) or max_size <= body_size * 0.8:
                items.append((rect.y0, rect.x0, {"type": "paragraph", "html": esc, "text": text, "style": "note"}))
            elif re.match(r"^[•·▪◦\-–]\s", text):
                items.append((rect.y0, rect.x0, {"type": "list", "ordered": False, "items": [html.escape(re.sub(r"^[•·▪◦\-–]\s*", "", t)) for t in lines_txt]}))
            else:
                items.append((rect.y0, rect.x0, {"type": "paragraph", "html": esc, "text": text, "style": None}))

        items.sort(key=lambda it: (round(it[0] / 8), it[1]))
        for _, _, blk in items:
            # merge consecutive bullet blocks into one list
            if blk["type"] == "list" and self.blocks and self.blocks[-1]["type"] == "list" and self.blocks[-1]["ordered"] == blk["ordered"]:
                self.blocks[-1]["items"].extend(blk["items"])
                continue
            self.blocks.append(blk)


def parse_pdf(path: Path, image_dir: Path) -> dict[str, Any]:
    return PdfParser(path, image_dir).parse()
