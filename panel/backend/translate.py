"""A report's twin in the other language (Chinese <-> English), translated by Claude.

Every piece of text of the report (headings, paragraphs with their inline formatting, list items,
table cells, captions and notes, the title and keywords) is sent to Claude in numbered batches and
put back in place; pictures, charts and the source file are kept as they are, and tables drawn as
pictures for the full-size view are redrawn in the new language. The twin is an ordinary report
folder whose meta says what it was translated from ("translated_from": the original's id).

    strings = collect(content, meta, "cn")            # what needs translating
    done = translate_strings(strings, "cn", "en")     # Claude (AI_MOCK=1: placeholders)
    twin_dir = build_twin(src_dir, dst_dir, "en", done)

The server (server.py) runs this in the background after every upload, and on request
(POST /api/reports/<id>/translate); `python translate.py <report id> ...` does it from the shell.
"""
from __future__ import annotations

import copy
import html
import json
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import ai_assist

LANG_NAME = {"en": "English", "cn": "Simplified Chinese"}
CJK = re.compile(r"[㐀-鿿豈-﫿]")
LATIN_WORD = re.compile(r"[A-Za-z]{2,}")
# keys whose string values (at any depth of a block) are text a reader sees
TEXT_KEYS = {"text", "html", "caption", "note", "title", "items", "rows", "label", "subtitle"}
META_KEYS = ("title", "subtitle", "masthead", "coverage")
BATCH_CHARS = 5000  # source characters per Claude call
PARALLEL = 4


def other(lang: str) -> str:
    return "en" if lang == "cn" else "cn"


def needs(text: str, src: str) -> bool:
    """A string worth sending: Chinese text going to English, or English words going to Chinese
    (figures, tickers and dates alone are kept as they are)."""
    if not isinstance(text, str) or not text.strip():
        return False
    return bool(CJK.search(text)) if src == "cn" else bool(LATIN_WORD.search(_plain(text)))


def _plain(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s or ""))


def _walk(node: Any, fn: Callable[[str], str], inside: bool = False) -> Any:
    """Apply fn to every reader-visible string: values under TEXT_KEYS (and everything nested in
    them, such as table rows), recursing through the blocks (layout cells hold blocks too)."""
    if isinstance(node, str):
        return fn(node) if inside else node
    if isinstance(node, list):
        return [_walk(x, fn, inside) for x in node]
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if k in ("src", "type", "anchor", "style", "id", "marks", "header", "level", "ordered", "exhibit", "n", "width", "height"):
                out[k] = v
            else:
                out[k] = _walk(v, fn, inside or k in TEXT_KEYS)
        return out
    return node


def collect(content: dict[str, Any], meta: dict[str, Any], src: str) -> list[str]:
    """The distinct strings of the report that need translating, in reading order."""
    seen: dict[str, None] = {}

    def take(s: str) -> str:
        if needs(s, src):
            seen.setdefault(s, None)
        return s

    for k in META_KEYS:
        if isinstance(meta.get(k), str):
            take(meta[k])
    for kw in meta.get("keywords") or []:
        take(kw)
    blocks = copy.deepcopy(content.get("blocks", []))
    for b in _blocks(blocks):
        if b.get("type") == "paragraph" and b.get("html"):
            b.pop("text", None)  # the plain text is made again from the translated markup
    _walk(blocks, take)
    _walk(content.get("exhibits", []), take)
    return list(seen)


# ------------------------------------------------------------------ Claude
SYSTEM = """You translate the text of an investment research report from {src} into {dst} for Junson Capital's alternative investment team.

You receive a JSON object mapping ids to strings: headings, paragraphs, list items, table cells, captions and keywords of one report, in reading order. Return a JSON object with exactly the same ids, each mapped to its translation, and nothing else (no commentary, no code fence).

Rules:
- Translate faithfully and completely in a professional financial register; do not summarise, add or drop anything.
- Keep every number, percentage, date, currency amount, ticker, fund and company name, index name (S&P 500, Nasdaq) and abbreviation (bps, YoY, QoQ, IRR, NAV, AUM, CLO, BDC) exactly as written; write Chinese company names in their usual English form when going to English.
- Keep inline HTML tags (<strong>, <em>, <u>, <a href=...>, <sup>, <sub>, <br>) and HTML entities (&amp;) around the same words they wrap; never add tags.
- Keep section numbering and list markers (I., 2.1, (a), 1)) as they are.
- A string that is already in {dst}, or is only figures or a name, comes back unchanged.
- Chinese output uses Simplified Chinese with full-width punctuation; English output uses US spelling."""


def _batches(strings: list[str]) -> list[list[str]]:
    out, cur, size = [], [], 0
    for s in strings:
        if cur and size + len(s) > BATCH_CHARS:
            out.append(cur)
            cur, size = [], 0
        cur.append(s)
        size += len(s)
    if cur:
        out.append(cur)
    return out


def _parse_json(text: str) -> dict[str, str]:
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON object in the reply")
    data = json.loads(m.group(0))
    if not isinstance(data, dict):
        raise ValueError("the reply is not a JSON object")
    return {str(k): v for k, v in data.items() if isinstance(v, str)}


def _translate_batch(client, batch: list[str], src: str, dst: str) -> dict[str, str]:
    payload = {str(i + 1): s for i, s in enumerate(batch)}
    system = SYSTEM.format(src=LANG_NAME[src], dst=LANG_NAME[dst])
    last: Exception | None = None
    for _ in range(3):
        try:
            with client.messages.stream(model=ai_assist.model_name(), max_tokens=32000, system=system,
                                        messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]) as stream:
                msg = stream.get_final_message()
            text = "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text")
            got = _parse_json(text)
            return {batch[int(k) - 1]: v for k, v in got.items() if k.isdigit() and 1 <= int(k) <= len(batch) and v.strip()}
        except (ValueError, json.JSONDecodeError) as exc:  # a malformed reply: ask again
            last = exc
        except Exception as exc:
            raise ai_assist._api_error(exc)
    raise ai_assist.AIError(f"Claude did not return a usable translation: {last}")


def _mock(batch: list[str], dst: str) -> dict[str, str]:
    tag = "[EN] " if dst == "en" else "[中文] "
    return {s: tag + s for s in batch}


def translate_strings(strings: list[str], src: str, dst: str) -> dict[str, str]:
    """original -> translation for every string; a string Claude left out keeps its original."""
    if not strings:
        return {}
    batches = _batches(strings)
    if ai_assist.mock():
        out: dict[str, str] = {}
        for b in batches:
            out.update(_mock(b, dst))
        return out
    client = ai_assist._client()
    out = {}
    with ThreadPoolExecutor(max_workers=min(PARALLEL, len(batches))) as pool:
        for part in pool.map(lambda b: _translate_batch(client, b, src, dst), batches):
            out.update(part)
    return out


# ------------------------------------------------------------------ the twin folder
def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def apply(content: dict[str, Any], meta: dict[str, Any], done: dict[str, str], dst: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Translated copies of the content and the meta (ids, dates and pictures unchanged)."""
    tr = lambda s: done.get(s, s)  # noqa: E731
    content = _walk(copy.deepcopy(content), tr)
    for b in _blocks(content.get("blocks", [])):
        if b.get("type") == "paragraph" and b.get("html"):
            b["text"] = " ".join(_plain(b["html"]).split())  # the plain text follows the translated markup
    meta = copy.deepcopy(meta)
    for k in META_KEYS:
        if isinstance(meta.get(k), str):
            meta[k] = tr(meta[k])
    if meta.get("keywords"):
        meta["keywords"] = list(dict.fromkeys(tr(k) for k in meta["keywords"]))
    meta["language"] = dst
    return content, meta


def _blocks(blocks: list[dict[str, Any]]):
    for b in blocks:
        yield b
        if b.get("type") == "layout":
            for cell in b.get("cells", []):
                yield from _blocks(cell)


def build_twin(src_dir: Path, dst_dir: Path, done: dict[str, str], new_id: str, by: str) -> dict[str, Any]:
    """Write the translated twin of the report in src_dir to dst_dir; returns its meta."""
    from parsers import _render_tables

    meta = json.loads((src_dir / "meta.json").read_text(encoding="utf-8"))
    content = json.loads((src_dir / "content.json").read_text(encoding="utf-8"))
    src = meta.get("language") or "cn"
    content, twin = apply(content, meta, done, other(src))
    shutil.copytree(src_dir, dst_dir)
    # tables drawn as pictures (tbl_NNN.png) are drawn again with the translated cells; a table read
    # from a picture keeps that picture
    for b in _blocks(content.get("blocks", [])):
        if b.get("type") == "table" and re.fullmatch(r"tbl_\d+\.png", b.get("src") or ""):
            (dst_dir / "images" / b["src"]).unlink(missing_ok=True)
            b.pop("src", None)
    for e in content.get("exhibits", []):
        if re.fullmatch(r"tbl_\d+\.png", e.get("src") or ""):
            e.pop("src", None)
    (dst_dir / "images").mkdir(exist_ok=True)
    _render_tables(content, dst_dir / "images")
    heads = [b for b in _blocks(content.get("blocks", [])) if b.get("type") == "heading"]
    twin["toc"] = [{"level": h.get("level", 1), "text": h.get("text", "")} for h in heads][:60]
    first = next((b.get("text", "") for b in _blocks(content.get("blocks", [])) if b.get("type") == "paragraph" and len(b.get("text", "")) > 60), "")
    twin["summary"] = first[:220]
    for k in ("replaced", "updated_at", "ai_edited_at", "translation_error"):
        twin.pop(k, None)
    twin.update(id=new_id, translated_from=meta["id"], translated_at=_now(), translated_by=by)
    (dst_dir / "content.json").write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
    (dst_dir / "meta.json").write_text(json.dumps(twin, ensure_ascii=False, indent=2), encoding="utf-8")
    return twin


def translation_map(src_dir: Path) -> tuple[str, str, list[str]]:
    """(source language, target language, strings to translate) of the report in src_dir."""
    meta = json.loads((src_dir / "meta.json").read_text(encoding="utf-8"))
    content = json.loads((src_dir / "content.json").read_text(encoding="utf-8"))
    src = meta.get("language") or "cn"
    return src, other(src), collect(content, meta, src)


if __name__ == "__main__":  # python translate.py <report id> [...]: through the running server's rules
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import server

    for rid in sys.argv[1:]:
        print(rid, "->", server.translate_report(rid, wait=True))
