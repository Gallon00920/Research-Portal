from pathlib import Path
from typing import Any

from .common import auto_keywords


def parse_report(path: Path, image_dir: Path) -> dict[str, Any]:
    """Dispatch on file extension. Returns the parsed document dict."""
    ext = Path(path).suffix.lower()
    if ext == ".docx":
        from .docx_parser import parse_docx

        result = parse_docx(path, image_dir)
    elif ext == ".pdf":
        from .pdf_parser import parse_pdf

        result = parse_pdf(path, image_dir)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Upload a .docx or .pdf report.")
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
            elif b.get("type") == "table" and b.get("exhibit"):
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
