"""Uploaded pictures (slides, screenshots of pages) are read like the pages of a slide deck: the
text becomes headings, paragraphs and bullet lists, every table becomes a real table (its cells
read by Claude, its cropped picture kept as the full-size view), and every chart, diagram and
picture is kept whole as a cropped image. Several pictures uploaded together are one report, one slide
after the other in the order given.

A picture has no text layer, so Claude reads it (vision, structured output): the text in reading
order, and a rough box around each figure. The crops do not trust those boxes to the pixel: the
picture is cut into its own blocks along blank gutters (panels, tables, tiles, text lines; a
framed panel is opened up into its parts), and a figure is the union of the blocks Claude's box
covers. So a crop follows the slide's real edges and never takes a sliver of the next panel.

Without an Anthropic key (or when Claude cannot be reached, or with AI_MOCK=1) a picture is kept
whole as one slide, so an upload never fails for want of the API.
"""
from __future__ import annotations

import base64
import html
import io
import json
import os
import re
import sys
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from .common import build_exhibits, guess_language

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")
MAX_SIDE = 3200        # larger photos are scaled down: the reader never shows more than this
SEND_SIDE = 2000       # the copy sent to Claude (coordinates are relative, so size does not matter)
DEFAULT_MODEL = "claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"

_STR = {"type": "string"}
_BOX = {
    "type": "object",
    "properties": {k: {"type": "integer"} for k in ("x0", "y0", "x1", "y1")},
    "required": ["x0", "y0", "x1", "y1"],
    "additionalProperties": False,
}
LAYOUT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": _STR,
        "language": {"type": "string", "enum": ["en", "cn"]},
        "blocks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["heading", "paragraph", "bullets", "note", "figure"]},
                    "text": _STR,
                    "items": {"type": "array", "items": _STR},
                    "kind": {"type": "string", "enum": ["chart", "table", "diagram", "picture", "none"]},
                    "caption": _STR,
                    "box": _BOX,
                    "rows": {"type": "array", "items": {"type": "array", "items": _STR}},
                    "marks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "row": {"type": "integer"},
                                "col": {"type": "integer"},
                                "mark": {"type": "string", "enum": ["shade", "highlight", "bold"]},
                            },
                            "required": ["row", "col", "mark"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["type", "text", "items", "kind", "caption", "box", "rows", "marks"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "language", "blocks"],
    "additionalProperties": False,
}

PROMPT = """This image is one page of an investment report or one slide of a fund presentation.
Turn it into structured content for a report reader, the way a slide deck page is read:
the text becomes text, and every chart, table, diagram or picture is kept as an image.

Return:
- "title": the slide or page title as printed (empty if there is none).
- "language": "cn" if the body text is mainly Chinese, else "en".
- "blocks": everything on the page in reading order (top to bottom; a page in columns is read
  column by column, left column first). Each block is one of:
  - "heading": a section heading, or the title bar printed over a panel. Put it in "text".
  - "paragraph": running text, transcribed exactly in "text" (join wrapped lines into one
    paragraph), including a highlighted conclusion or key-takeaway box.
  - "bullets": a bulleted or numbered list; each item, transcribed exactly, in "items".
  - "note": a footnote, source line or disclaimer, in "text".
  - "figure": a chart (bar, line, pie, donut, area, scatter, waterfall...), a table of figures
    (any grid of rows and columns, including a heat map or sensitivity table), a panel of
    key-figure tiles, a diagram or org chart, a map, a photo or any other picture. Set "kind" to
    chart / table / diagram / picture, "caption" to its title as printed (empty if none), and
    "box" to the rectangle that encloses ALL of it: axes and axis labels, legend, data labels,
    column headers, every row, its own footnote. A table and the chart drawn right under it in
    the same panel are two figures.
    For a table (kind "table") also transcribe every cell into "rows": the first row is the
    column headers, then one list per row, all rows as long as the header, cells exactly as
    printed (a cell printed on two lines keeps a "\n"; an empty cell is ""). A panel of
    key-figure tiles is a table too: header ["指标", "数值"] (or ["Metric", "Value"] for an
    English page), then one row per tile with its label and its figure. In "marks" list the cells
    the table sets apart by colour or weight, by "row" and "col" index into "rows" (0-based,
    the header row is row 0): "shade" for a tinted cell (a heat map's coloured cells, a band of
    rows in a light colour), "highlight" for the one or few cells picked out in a strong colour,
    "bold" for a figure printed in bold or colour within plain cells. Plain zebra striping is not
    a mark. For other figures "rows" and "marks" are empty.
- "box" coordinates are on a 0-1000 scale of the image: x0,y0 = top-left, x1,y1 = bottom-right,
  x from the left edge, y from the top edge. Give a box only for figures; use 0,0,0,0 for text blocks.

Rules:
- Text that is part of a figure (chart labels, legend entries, table cells, tile figures and
  their labels, labels inside a diagram) belongs to the figure: do not transcribe it again.
- Transcribe the text faithfully in its original language; do not summarise, translate or add.
- Leave out page furniture: logos, page numbers, "confidential" banners, the slide title (it goes in "title").
- Fields that do not apply to a block are empty strings, an empty list, kind "none", box 0,0,0,0,
  empty "rows" and "marks".
"""


class ImageReadError(Exception):
    pass


# ------------------------------------------------------------------ entry points
def parse_image(path: Path, image_dir: Path) -> dict[str, Any]:
    return parse_images([Path(path)], image_dir)


def parse_image_zip(path: Path, image_dir: Path) -> dict[str, Any]:
    """Several pictures uploaded together are kept as one zip (source.zip), in upload order."""
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(path) as zf:
        names = sorted(n for n in zf.namelist() if Path(n).suffix.lower() in IMAGE_EXTS and not n.endswith("/"))
        if not names:
            raise ValueError("the zip holds no pictures")
        paths = []
        for i, name in enumerate(names):
            out = Path(tmp) / f"{i:03d}{Path(name).suffix.lower()}"
            out.write_bytes(zf.read(name))
            paths.append(out)
        return parse_images(paths, image_dir)


def parse_images(paths: list[Path], image_dir: Path) -> dict[str, Any]:
    image_dir = Path(image_dir)
    image_dir.mkdir(parents=True, exist_ok=True)
    pictures = [_load(p) for p in paths]
    # the slides are read at the same time: each is one Claude request of half a minute or so
    with ThreadPoolExecutor(max_workers=min(4, len(pictures))) as pool:
        layouts = list(pool.map(_try_layout, [im for im, _fmt in pictures]))

    multi = len(pictures) > 1
    blocks: list[dict[str, Any]] = []
    titles: list[str] = []
    languages: list[str] = []
    read = 0
    reasons: list[str] = []
    for n, ((im, fmt), (layout, reason)) in enumerate(zip(pictures, layouts), start=1):
        prefix = f"s{n}_" if multi else ""
        slide: list[dict[str, Any]] = []
        title = ""
        if layout is not None:
            slide, title, language = _slide_blocks(im, layout, image_dir, prefix)
            if slide:
                read += 1
                languages.append(language)
            else:
                reason = "Claude found nothing on the picture"
        if not slide:
            reasons.append(reason)
            slide = [_whole_picture(im, fmt, image_dir, prefix)]
        titles.append(title)
        if multi:
            if n > 1:
                blocks.append({"type": "pagebreak"})
            if title:
                blocks.append({"type": "heading", "level": 1, "text": title})
        blocks.extend(slide)

    body = _body_text(blocks)
    language = max(set(languages), key=languages.count) if languages else (guess_language(body) if body.strip() else "")
    stats = {
        "blocks": len(blocks),
        "images": sum(1 for b in blocks if b["type"] == "image"),
        "tables": sum(1 for b in blocks if b["type"] == "table"),
        "chars": len(body.strip()),
        "pages": len(pictures),
        "read_by": "claude" if read else "",
    }
    if reasons:
        stats["whole_slide_reason"] = reasons[0][:200]
    return {
        "title": _report_title(titles),
        "keywords": [],
        "language": language,
        "blocks": blocks,
        "exhibits": build_exhibits(blocks),
        "stats": stats,
    }


def _load(path: Path):
    from PIL import Image, ImageOps

    with Image.open(path) as raw:
        raw.load()
        fmt = (raw.format or "").upper()
        im = ImageOps.exif_transpose(raw)  # phone photos carry their rotation in EXIF
    if max(im.size) > MAX_SIDE:
        im.thumbnail((MAX_SIDE, MAX_SIDE))
    im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") and fmt != "JPEG" else "RGB")
    return im, fmt


def _try_layout(im) -> tuple[dict[str, Any] | None, str]:
    try:
        return read_layout(im), ""
    except Exception as exc:  # noqa: BLE001  (no key, network, refusal, bad answer): keep the picture whole
        print(f"image parser: the picture is kept whole as one slide ({exc})", file=sys.stderr)
        return None, str(exc)


def _report_title(titles: list[str]) -> str:
    """One slide: its title. Several: what their titles share ("Progress 2Q26 更新" from
    "Progress 2Q26 更新 - 融资到期" and "Progress 2Q26 更新 — 退出路径"), else the first title."""
    titles = [t for t in titles if t]
    if not titles:
        return ""
    if len(titles) == 1:
        return titles[0]
    common = os.path.commonprefix(titles)
    common = re.sub(r"[\s\-–—:：|·,，]+$", "", common).strip()
    if len(common) >= 4 and not re.search(r"[《(（\[【]$", common):
        return common
    return titles[0]


def _body_text(blocks: list[dict[str, Any]]) -> str:
    text = " ".join(b.get("text", "") for b in blocks if b["type"] in ("heading", "paragraph"))
    return text + " " + " ".join(html.unescape(x) for b in blocks if b["type"] == "list" for x in b["items"])


# ------------------------------------------------------------------ Claude
def read_layout(im) -> dict[str, Any]:
    """Ask Claude for the picture's text and figure boxes (structured output)."""
    if os.environ.get("AI_MOCK", "").strip().lower() in {"1", "true", "yes"}:
        raise ImageReadError("AI_MOCK is set")
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        raise ImageReadError("ANTHROPIC_API_KEY is not set, so the text of a picture cannot be read")
    import anthropic

    try:
        import truststore  # type: ignore  (TLS-inspecting corporate proxies)

        truststore.inject_into_ssl()
    except Exception:
        pass

    send = im.convert("RGB")
    if max(send.size) > SEND_SIDE:
        send = send.copy()
        send.thumbnail((SEND_SIDE, SEND_SIDE))
    buf = io.BytesIO()
    send.save(buf, "JPEG", quality=90)
    request: dict[str, Any] = {
        "model": os.environ.get("IMAGE_PARSE_MODEL", "").strip() or os.environ.get("AI_MODEL", "").strip() or DEFAULT_MODEL,
        "max_tokens": 16000,
        "output_config": {"effort": "high", "format": {"type": "json_schema", "schema": LAYOUT_SCHEMA}},
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.standard_b64encode(buf.getvalue()).decode("ascii")}},
                {"type": "text", "text": PROMPT},
            ],
        }],
    }
    client = anthropic.Anthropic(timeout=600, max_retries=2)
    try:
        # if a safety classifier declines, the API re-runs the request on a fallback model
        response = client.beta.messages.create(betas=[FALLBACK_BETA], fallbacks="default", **request)
    except anthropic.APIError as exc:
        raise ImageReadError(f"Claude could not read the picture: {exc}") from exc
    if response.stop_reason == "refusal":
        raise ImageReadError("Claude declined to read the picture")
    if response.stop_reason == "max_tokens":
        raise ImageReadError("the picture holds more text than fits in one answer")
    text = next((b.text for b in response.content if getattr(b, "type", "") == "text"), "")
    try:
        layout = json.loads(text)
    except ValueError as exc:
        raise ImageReadError("Claude's answer was not valid JSON") from exc
    if not isinstance(layout, dict) or not isinstance(layout.get("blocks"), list):
        raise ImageReadError("Claude's answer has no blocks")
    return layout


# ------------------------------------------------------------------ one slide
def _slide_blocks(im, layout: dict[str, Any], image_dir: Path, prefix: str) -> tuple[list[dict[str, Any]], str, str]:
    w, h = im.size
    tree = page_tree(im)
    gray = im.convert("L")
    margin = max(3, round(0.004 * max(w, h)))
    blocks: list[dict[str, Any]] = []
    figures: list[tuple[list[int], dict[str, Any]]] = []
    for raw in layout.get("blocks") or []:
        kind = raw.get("type")
        text = " ".join(str(raw.get("text") or "").split())
        if kind == "figure":
            box = raw.get("box") or {}
            try:
                x0, y0, x1, y1 = (max(0, min(1000, int(box.get(k, 0)))) for k in ("x0", "y0", "x1", "y1"))
            except (TypeError, ValueError):
                continue
            if x1 - x0 < 8 or y1 - y0 < 8:
                continue
            claude = (x0 * w // 1000, y0 * h // 1000, -(-x1 * w // 1000), -(-y1 * h // 1000))
            px = figure_box(tree, claude, gray, margin)
            if not px:
                continue
            block = {"type": "image", "src": "", "caption": " ".join(str(raw.get("caption") or "").split()),
                     "exhibit": None, "note": "", "figure_kind": raw.get("kind") or ""}
            # a figure that overlaps one already kept is the same figure: keep the union
            twin = next((f for f in figures if _overlap(f[0], px) > 0.25), None)
            if twin:
                b = twin[0]
                b[:] = [min(b[0], px[0]), min(b[1], px[1]), max(b[2], px[2]), max(b[3], px[3])]
                if block["caption"] and not twin[1]["caption"]:
                    twin[1]["caption"] = block["caption"]
                continue
            table = _table_cells(raw) if raw.get("kind") == "table" else None
            if table:
                block["_table"] = table
            figures.append((px, block))
            blocks.append(block)
        elif kind == "heading" and text:
            blocks.append({"type": "heading", "level": 2, "text": text})
        elif kind == "bullets":
            items = [" ".join(str(x).split()) for x in raw.get("items") or [] if str(x).strip()]
            if not items and text:
                items = [text]
            if items:
                blocks.append({"type": "list", "ordered": False, "items": [html.escape(x) for x in items]})
        elif kind in ("paragraph", "note") and text:
            blocks.append({"type": "paragraph", "html": html.escape(text), "text": text, "style": "note" if kind == "note" else None})

    for n, (px, block) in enumerate(figures, start=1):
        crop = im.crop(tuple(px))
        name = f"img_{prefix}{n:03d}.png"
        crop.save(image_dir / name, "PNG", optimize=True)
        block.update(src=name, width=crop.width, height=crop.height)
        table = block.pop("_table", None)
        if table:
            # a real table, read by Claude; the cropped picture stays as its full-size view (the
            # lightbox), so the original can always be checked against the transcription
            rows, marks = table
            caption = block.get("caption", "")
            block.clear()
            block.update({"type": "table", "rows": rows, "header": True, "caption": caption,
                          "exhibit": None, "note": "", "src": name, "marks": marks})

    title = " ".join(str(layout.get("title") or "").split())
    body = _body_text(blocks)
    language = layout.get("language") if layout.get("language") in ("en", "cn") else guess_language(title + " " + body)
    return blocks, title, language


def _table_cells(raw: dict[str, Any]) -> tuple[list[list[str]], list[list[Any]]] | None:
    """The cells Claude read for a table, squared up (every row as long as the longest), and its
    marked cells as [row, col, mark]. None when there is no real grid (fewer than 2 rows or columns)."""
    rows = [[str(c if c is not None else "").strip() for c in r] for r in raw.get("rows") or [] if isinstance(r, list)]
    rows = [r for r in rows if any(r)]
    if len(rows) < 2:
        return None
    ncols = max(len(r) for r in rows)
    if ncols < 2:
        return None
    rows = [r + [""] * (ncols - len(r)) for r in rows]
    marks = []
    for m in raw.get("marks") or []:
        try:
            r, c, kind = int(m.get("row")), int(m.get("col")), str(m.get("mark"))
        except (TypeError, ValueError, AttributeError):
            continue
        if 0 <= r < len(rows) and 0 <= c < ncols and kind in ("shade", "highlight", "bold"):
            marks.append([r, c, kind])
    return rows, marks


def _whole_picture(im, fmt: str, image_dir: Path, prefix: str) -> dict[str, Any]:
    if fmt == "JPEG":
        name = f"img_{prefix}001.jpg"
        im.convert("RGB").save(image_dir / name, "JPEG", quality=90)
    else:
        name = f"img_{prefix}001.png"
        im.save(image_dir / name, "PNG", optimize=True)
    return {"type": "image", "src": name, "caption": "", "exhibit": None, "note": "", "slide": True,
            "pixel_width": im.width, "pixel_height": im.height}


# ------------------------------------------------------------------ the picture's own blocks
def content_mask(im, threshold: int = 16):
    """White where the picture has ink: an edge between two colours (text, lines, the border of
    a filled box, even a light grey panel or tile on white). A flat fill is empty."""
    from PIL import ImageDraw, ImageFilter

    edges = im.convert("L").filter(ImageFilter.FIND_EDGES)
    mask = edges.point(lambda v: 255 if v > threshold else 0)
    w, h = mask.size
    ImageDraw.Draw(mask).rectangle([0, 0, w - 1, h - 1], outline=0, width=3)  # the filter's own border
    return mask


def _profile(mask, box: tuple[int, int, int, int], axis: str) -> list[float]:
    """Ink per row (axis "y") or per column ("x") of the box: 0 means blank."""
    from PIL import Image

    region = mask.crop(box).convert("F")
    w, h = region.size
    return list(region.resize((1, h) if axis == "y" else (w, 1), resample=Image.Resampling.BOX).getdata())


def _runs(profile: list[float], min_gap: int) -> list[tuple[int, int]]:
    """The inked stretches of a profile, split where a blank stretch is at least min_gap long."""
    runs: list[tuple[int, int]] = []
    start = None
    blank = 0
    for i, v in enumerate(profile):
        if v > 0:
            if start is None:
                start = i
            elif blank >= min_gap:
                runs.append((start, i - blank))
                start = i
            blank = 0
        elif start is not None:
            blank += 1
    if start is not None:
        runs.append((start, len(profile) - blank))
    return runs


def _ink(mask, box: tuple[int, int, int, int]) -> float:
    """Share of the box's pixels that are ink."""
    from PIL import ImageStat

    if box[2] <= box[0] or box[3] <= box[1]:
        return 0.0
    return ImageStat.Stat(mask.crop(box)).mean[0] / 255


def page_tree(im, mask=None) -> dict[str, Any]:
    """The picture cut into blocks along blank gutters (recursive X-Y cut). Each node is
    {"box": (x0, y0, x1, y1) tight around its ink, "children": [...]}. A block that cannot be cut
    (a bordered or filled panel, whose edges hide the gutters inside) is opened up: a few pixels
    in from its edges it is cut again, so a panel holding a list and a chart has both as children."""
    mask = mask or content_mask(im)
    w, h = mask.size
    min_gap = max(4, round(0.0045 * max(w, h)))  # the blank strip that separates two blocks
    insets = sorted({2, 4, 7, max(8, round(0.004 * max(w, h)))})

    def cut(box: tuple[int, int, int, int], depth: int, open_up: bool = True) -> dict[str, Any] | None:
        tight = mask.crop(box).getbbox()
        if not tight:
            return None
        box = (box[0] + tight[0], box[1] + tight[1], box[0] + tight[2], box[1] + tight[3])
        if (box[2] - box[0]) * (box[3] - box[1]) < 25:
            return None  # a speck: noise, a corner pixel of a panel
        node: dict[str, Any] = {"box": box, "children": []}
        if depth > 16:
            return node
        for axis in ("y", "x"):
            runs = _runs(_profile(mask, box, axis), min_gap)
            if len(runs) > 1:
                for a, b in runs:
                    sub = (box[0], box[1] + a, box[2], box[1] + b) if axis == "y" else (box[0] + a, box[1], box[0] + b, box[3])
                    child = cut(sub, depth + 1)
                    if child:
                        node["children"].append(child)
                return node
        # a block with no gutter across it may be a framed or filled panel: its border lines run
        # the whole length and hide the gutters inside. Step in past them and try again.
        if open_up and box[2] - box[0] > 40 and box[3] - box[1] > 40:
            for d in insets:
                inner = (box[0] + d, box[1] + d, box[2] - d, box[3] - d)
                if inner[2] - inner[0] < 20 or inner[3] - inner[1] < 20:
                    break
                child = cut(inner, depth + 1, open_up=False)
                if child and child["children"]:
                    node["children"] = child["children"]
                    break
        return node

    return cut((0, 0, w, h), 0) or {"box": (0, 0, w, h), "children": []}


def _covered(a: tuple[int, ...], b: tuple[int, ...]) -> float:
    """How much of box a lies inside box b."""
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    area = (a[2] - a[0]) * (a[3] - a[1]) or 1
    return ix * iy / area


def figure_box(tree: dict[str, Any], claude: tuple[int, int, int, int], gray, margin: int) -> list[int] | None:
    """The crop of a figure: the blocks of the picture that Claude's box covers. A block almost
    wholly inside the box is taken whole; one only partly inside is opened up and its parts are
    judged in turn; a block with no parts is taken when most of it is inside. The crop is the
    union of what was taken, with a small margin that only ever spans plain page background."""
    w, h = gray.size
    pad = round(0.01 * max(w, h))  # Claude's box is rough: judge against a slightly larger one
    box = (claude[0] - pad, claude[1] - pad, claude[2] + pad, claude[3] + pad)
    picked: list[tuple[int, int, int, int]] = []

    def visit(node: dict[str, Any]):
        share = _covered(node["box"], box)
        if share <= 0:
            return
        if share >= 0.95 or (not node["children"] and share >= 0.6):
            picked.append(node["box"])
            return
        for child in node["children"]:
            visit(child)

    visit(tree)
    if not picked:
        return None
    x0, y0 = min(b[0] for b in picked), min(b[1] for b in picked)
    x1, y1 = max(b[2] for b in picked), max(b[3] for b in picked)
    bg = _page_background(gray)

    def plain(x0_, y0_, x1_, y1_) -> bool:
        if x1_ <= x0_ or y1_ <= y0_:
            return False
        lo, hi = gray.crop((x0_, y0_, x1_, y1_)).getextrema()
        return abs(lo - bg) <= 12 and abs(hi - bg) <= 12

    for _ in range(margin):  # breathing room, but only into blank page
        if y0 > 0 and plain(x0, y0 - 1, x1, y0):
            y0 -= 1
        if y1 < h and plain(x0, y1, x1, y1 + 1):
            y1 += 1
        if x0 > 0 and plain(x0 - 1, y0, x0, y1):
            x0 -= 1
        if x1 < w and plain(x1, y0, x1 + 1, y1):
            x1 += 1
    return [x0, y0, x1, y1]


def _page_background(gray) -> int:
    """The page's own colour: the most common value along the picture's border."""
    w, h = gray.size
    edge = list(gray.crop((0, 0, w, 3)).getdata()) + list(gray.crop((0, h - 3, w, h)).getdata())
    edge += list(gray.crop((0, 0, 3, h)).getdata()) + list(gray.crop((w - 3, 0, w, h)).getdata())
    return max(set(edge), key=edge.count)


def _overlap(a: list[int], b: list[int]) -> float:
    """Intersection over the smaller box's area."""
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    small = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1])) or 1
    return ix * iy / small
