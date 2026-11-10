"""Render a parsed table (list of rows) to a PNG so it can be viewed like a figure."""
from __future__ import annotations

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont  # type: ignore
except Exception:  # pragma: no cover
    Image = None  # type: ignore

FONT_CANDIDATES = [
    ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc"),      # Microsoft YaHei (CJK + Latin)
    ("C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/simhei.ttf"),
    ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),  # Linux (Docker)
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]
SIZE = 22
PAD_X, PAD_Y = 16, 11
MAX_COL = 460
MAX_TOTAL = 2600
HEADER_BG = (12, 43, 78)
HEADER_FG = (255, 255, 255)
ZEBRA = (237, 243, 250)
LINE = (217, 225, 235)
INK = (22, 34, 47)
CAP = (49, 70, 92)


def _fonts():
    for reg, bold in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(reg, SIZE), ImageFont.truetype(bold, SIZE), ImageFont.truetype(bold, SIZE + 2)
        except Exception:
            continue
    f = ImageFont.load_default()
    return f, f, f


def _wrap(text: str, font, draw, max_w: int) -> list[str]:
    lines: list[str] = []
    for para in (text or "").split("\n"):
        if not para:
            lines.append("")
            continue
        # word wrap for Latin, character wrap for CJK
        tokens = para.split(" ") if " " in para else list(para)
        joiner = " " if " " in para else ""
        cur = ""
        for tok in tokens:
            cand = (cur + joiner + tok) if cur else tok
            if draw.textlength(cand, font=font) <= max_w or not cur:
                cur = cand
                # a single over-long token: hard wrap by characters
                while draw.textlength(cur, font=font) > max_w and len(cur) > 1:
                    cut = len(cur)
                    while cut > 1 and draw.textlength(cur[:cut], font=font) > max_w:
                        cut -= 1
                    lines.append(cur[:cut])
                    cur = cur[cut:]
            else:
                lines.append(cur)
                cur = tok
        lines.append(cur)
    return lines or [""]


def render_table_png(rows: list[list[str]], out_path: Path, caption: str = "", header: bool = True) -> bool:
    if Image is None or not rows:
        return False
    font, bold, cap_font = _fonts()
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    ncols = max(len(r) for r in rows)
    rows = [list(r) + [""] * (ncols - len(r)) for r in rows]

    # natural column widths
    widths = [0] * ncols
    for r in rows:
        for j, c in enumerate(r):
            for line in (c or "").split("\n"):
                widths[j] = max(widths[j], int(probe.textlength(line, font=bold)) + 2 * PAD_X)
    widths = [min(w, MAX_COL) for w in widths]
    widths = [max(w, 90) for w in widths]
    if sum(widths) > MAX_TOTAL:
        scale = MAX_TOTAL / sum(widths)
        widths = [max(90, int(w * scale)) for w in widths]

    # wrap cells and compute row heights
    line_h = SIZE + 8
    wrapped: list[list[list[str]]] = []
    heights: list[int] = []
    for i, r in enumerate(rows):
        f = bold if (header and i == 0) else font
        cells = [_wrap(c, f, probe, widths[j] - 2 * PAD_X) for j, c in enumerate(r)]
        wrapped.append(cells)
        heights.append(max(len(c) for c in cells) * line_h + 2 * PAD_Y)

    cap_lines = _wrap(caption, cap_font, probe, sum(widths)) if caption else []
    cap_h = (len(cap_lines) * (SIZE + 10) + 14) if cap_lines else 0
    W = sum(widths) + 2
    H = sum(heights) + cap_h + 2
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    y = 0
    for line in cap_lines:
        d.text((2, y + 4), line, font=cap_font, fill=CAP)
        y += SIZE + 10
    if cap_lines:
        y += 14
    for i, cells in enumerate(wrapped):
        is_head = header and i == 0
        bg = HEADER_BG if is_head else (ZEBRA if i % 2 == 0 else (255, 255, 255))
        d.rectangle([0, y, W, y + heights[i]], fill=bg)
        x = 0
        for j, lines in enumerate(cells):
            ty = y + PAD_Y
            for line in lines:
                d.text((x + PAD_X, ty), line, font=bold if is_head else font, fill=HEADER_FG if is_head else INK)
                ty += line_h
            x += widths[j]
            d.line([x, y, x, y + heights[i]], fill=LINE, width=1)
        y += heights[i]
        d.line([0, y, W, y], fill=LINE, width=1)
    d.rectangle([0, cap_h, W - 1, H - 1], outline=LINE, width=1)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    im.save(out_path, format="PNG")
    return True
