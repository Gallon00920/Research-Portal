from pathlib import Path
from typing import Any

from .common import auto_keywords, guess_language
from .image_parser import IMAGE_EXTS

# what an upload may be: Word and PDF reports are read for their text, tables and figures; a
# picture (portfolio management's AID analysis) is read like a slide: text as text, charts,
# tables and pictures kept whole (parsers/image_parser.py); a PowerPoint deck (a special topic)
# likewise, slide by slide: text as text, tables as tables, charts and pictures kept whole
# (parsers/pptx_parser.py)
REPORT_EXTS = (".docx", ".pdf")
DECK_EXTS = (".pptx", ".ppt")
UPLOAD_EXTS = REPORT_EXTS + DECK_EXTS + IMAGE_EXTS
SLIDES_EXT = ".zip"  # the source of several pictures uploaded together, in upload order


def fill_from_file_name(parsed: dict[str, Any], source_name: str) -> dict[str, Any]:
    """A picture whose title or language Claude could not read (no key, or a picture without
    text) takes them from its file name, so the report is never untitled or language-less."""
    if Path(source_name or "").suffix.lower() not in IMAGE_EXTS + (SLIDES_EXT,):
        return parsed
    if not parsed.get("title"):
        parsed["title"] = " ".join(Path(source_name).stem.replace("_", " ").split())
    if parsed.get("language") not in ("en", "cn"):
        parsed["language"] = guess_language(parsed["title"]) if parsed["title"] else "en"
    return parsed


def parse_report(path: Path, image_dir: Path) -> dict[str, Any]:
    """Dispatch on file extension. Returns the parsed document dict."""
    ext = Path(path).suffix.lower()
    if ext == ".docx":
        from .docx_parser import parse_docx

        result = parse_docx(path, image_dir)
    elif ext == ".pdf":
        from .pdf_parser import parse_pdf

        result = parse_pdf(path, image_dir)
    elif ext in DECK_EXTS:
        from .pptx_parser import parse_pptx

        result = parse_pptx(path, image_dir)
    elif ext in IMAGE_EXTS:
        from .image_parser import parse_image

        result = parse_image(path, image_dir)
    elif ext == ".zip":  # several pictures uploaded together: one report, one slide each
        from .image_parser import parse_image_zip

        result = parse_image_zip(path, image_dir)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Upload a .docx, .pdf or .pptx report, or an image.")
    if not result.get("keywords"):
        text = " ".join(_text(b) for b in result["blocks"])
        result["keywords"] = auto_keywords(text, result.get("language", "en"))
    _render_tables(result, Path(image_dir))
    return result


def _render_tables(result: dict[str, Any], image_dir: Path):
    """Give every table block a PNG rendering so it can open in the lightbox."""
    from .table_image import render_table_png

    by_n = {e["n"]: e for e in result.get("exhibits", [])}

    def visit(blocks):
        for b in blocks:
            if b.get("type") == "layout":
                for c in b["cells"]:
                    visit(c)
            elif b.get("type") == "table" and b.get("exhibit") and not b.get("src"):  # a table from a picture keeps its crop
                name = f"tbl_{b['exhibit']:03d}.png"
                try:
                    ok = render_table_png(b["rows"], image_dir / name, caption=b.get("caption") or "", header=b.get("header", True))
                except Exception:
                    ok = False
                if ok:
                    b["src"] = name
                    if b["exhibit"] in by_n:
                        by_n[b["exhibit"]]["src"] = name

    visit(result.get("blocks", []))


def _text(b: dict[str, Any]) -> str:
    if b.get("type") in ("paragraph", "heading", "callout"):
        return b.get("text", "")
    if b.get("type") == "layout":
        return " ".join(_text(x) for c in b["cells"] for x in c)
    return ""
