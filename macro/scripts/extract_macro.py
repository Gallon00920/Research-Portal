#!/usr/bin/env python3
"""Macro / Market: turn the screenshots of a slide deck into data, slide by slide, in order.

One brief per month. An upload is a title plus any number of slide images in order; Claude reads
each image into one generic shape (a title, then blocks: charts, tables, bullet lists, call-outs,
plain text, footnotes), this script parses the numbers, and the site redraws every slide as real
charts and tables. A later upload for the same month replaces it. Output:

  macro/data/<YYYY-MM>.json           the brief: title, pages (one per slide, in upload order)
  macro/data/<YYYY-MM>/<nn>.<ext>     the uploaded images, kept for checking
  macro/data/index.json               which months exist

Usage
  python macro/scripts/extract_macro.py --apply
      process macro/incoming/: <YYYY-MM>.meta.json ({"title": ...}) plus <YYYY-MM>-<nn>.<ext> images,
      the files the site commits on upload; this is what the GitHub workflow runs
  python macro/scripts/extract_macro.py --images a.png b.png --year 2026 --month 10 --title "..."
      extract local images, in the order given
  python macro/scripts/extract_macro.py --from-raw pages.json --year 2026 --month 10 [--images ...]
      skip Claude: normalise an already transcribed list of pages (the shape Claude returns)
  python macro/scripts/extract_macro.py --translate [--force] [--year 2026 --month 10]
  python macro/scripts/extract_macro.py --reindex

Needs ANTHROPIC_API_KEY (the factors requirements: anthropic, truststore). MACRO_MODEL overrides
the model; AI_MOCK=1 writes placeholder pages instead of calling Claude.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]  # macro/
REPO = ROOT.parent
DATA = ROOT / "data"
INCOMING = ROOT / "incoming"
FAILED = ROOT / "failed"
sys.path.insert(0, str(REPO / "factors" / "scripts"))
import extract_factors as ff  # noqa: E402  (shared: the Claude call, number parsing, figure checks)

DEFAULT_MODEL = "claude-opus-5-5"
MEDIA_TYPES = ff.MEDIA_TYPES
MAX_IMAGE_BYTES = ff.MAX_IMAGE_BYTES
INCOMING_IMG_RE = re.compile(r"^(\d{4}-\d{2})-(\d{2})\.(png|jpe?g|webp|gif)$", re.I)
INCOMING_META_RE = re.compile(r"^(\d{4}-\d{2})\.meta\.json$", re.I)
TONES = ("none", "positive", "negative", "warning", "neutral")
KINDS = ("line", "bar", "hbar")

ExtractionError = ff.ExtractionError
MissingKeyError = ff.MissingKeyError
clean_text = ff.clean_text
parse_number = ff.parse_number
now_iso = ff.now_iso
month_key = ff.month_key


def log(*parts: Any) -> None:
    print("[macro]", *parts, file=sys.stderr, flush=True)


def mock() -> bool:
    return os.environ.get("AI_MOCK", "").strip().lower() in {"1", "true", "yes"}


def model_name() -> str:
    return os.environ.get("MACRO_MODEL", "").strip() or os.environ.get("FACTORS_MODEL", "").strip() or DEFAULT_MODEL


# ------------------------------------------------------------------ what Claude returns for one slide
_obj, _STR, _STRS = ff._obj, ff._STR, ff._STRS
_CELL = _obj({"text": _STR, "tone": {"type": "string", "enum": list(TONES)}})
PAGE_SCHEMA = _obj({
    "title": _STR,
    "subtitle": _STR,
    "blocks": {"type": "array", "items": _obj({
        "type": {"type": "string", "enum": ["chart", "table", "bullets", "callout", "text", "footnotes"]},
        "title": _STR,
        "kind": {"type": "string", "enum": list(KINDS) + [""]},
        "unit": _STR,
        "categories": _STRS,
        "series": {"type": "array", "items": _obj({"name": _STR, "values": _STRS})},
        "bars": {"type": "array", "items": _obj({"group": _STR, "label": _STR, "value": _STR, "text": _STR,
                                                 "parts": {"type": "array", "items": _obj({"name": _STR, "value": _STR})}})},
        "columns": _STRS,
        "rows": {"type": "array", "items": _obj({"cells": {"type": "array", "items": _CELL}})},
        "items": _STRS,
        "text": _STR,
        "notes": _STRS,
    })},
})

PAGE_PROMPT = """This image is one slide of an internal investment-committee deck (macro and market updates, portfolio impact). Transcribe it exactly into the JSON shape so the slide can be rebuilt on a web page with real charts and tables. Accuracy matters more than anything else: these are financial figures, so read every number from its printed label, never from the height or length of a bar, and never estimate or fill in a value that is not printed. Keep the original language of every text; do not translate.

- title: the slide title (the large heading at the top). subtitle: the sentence or paragraph printed directly under the title, if any, else "".
- blocks: everything else on the slide, in reading order (left column top to bottom, then right column; a panel with a header box is one block whose title is the header text). Every block has every field; leave the ones that do not apply empty ("" or []).

Block types:
- "chart": kind is "line" for lines over categories, "bar" for vertical bars, "hbar" for horizontal bars. unit is the unit printed in the header or axis ("%", "$m", "万美元") or "". For line and bar charts: categories are the x-axis labels left to right; series has one entry per line or bar colour, with its legend name (or the label printed beside the line, for example "9月", "6月") and values: one printed value per category as text ("4.1%", "3.625%"), or "" where no value is printed for that category. For hbar charts: bars lists every bar top to bottom; group is the heading above a run of bars ("浮动为主 · 48%") repeated for each bar under it, or ""; label is the bar's own label; value is the bar's total as printed ("31.6"); text is the full annotation printed beside the bar ("31.6 · 浮动100%"); parts lists the coloured segments of the bar as the legend names them with each part's figure if printed ("100%", "52%", or an amount), else "". notes: any legend entries or small notes under the chart, one each.
- "table": columns are the header cells left to right (the first may be ""); rows are every body row top to bottom, cells one per column with the cell text exactly as printed (line breaks joined by a space) and tone: the colour the cell is shaded or written in: "positive" for green, "negative" for red or pink, "warning" for yellow or amber, "neutral" for grey, "none" otherwise. notes: lines printed under the table.
- "bullets": a bullet list; title is its heading if it has one; items one per bullet, exactly as written (join wrapped lines).
- "callout": a highlighted box of text (shaded background or a thick left border); text is its full text.
- "text": a plain paragraph; text is its content.
- "footnotes": the small numbered source notes at the bottom of the slide; items one per note. Page numbers and the logo are not content."""


def call_claude_page(image: bytes, media_type: str) -> tuple[dict[str, Any], str]:
    request: dict[str, Any] = {
        "model": model_name(),
        "max_tokens": 16000,
        "output_config": {"effort": "high", "format": {"type": "json_schema", "schema": PAGE_SCHEMA}},
        "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": base64.standard_b64encode(image).decode("ascii")}},
            {"type": "text", "text": PAGE_PROMPT},
        ]}],
    }
    return ff._ask_claude(request, declined="Claude declined to read this slide",
                          too_long="the slide holds more than fits in one answer; crop it and upload again")


# ------------------------------------------------------------------ normalise one slide
def _num(text: Any) -> float | None:
    p = parse_number(text)
    return p["value"] if p["kind"] in ("number", "percent") else None


def normalize_page(raw: dict[str, Any], n: int) -> dict[str, Any]:
    warnings: list[str] = []
    blocks: list[dict[str, Any]] = []
    for b in raw.get("blocks") or []:
        kind = str(b.get("type") or "")
        title = clean_text(b.get("title"))
        notes = [clean_text(x) for x in (b.get("notes") or []) if clean_text(x)]
        if kind == "chart":
            ck = b.get("kind") if b.get("kind") in KINDS else ("hbar" if b.get("bars") else "line")
            out: dict[str, Any] = {"type": "chart", "kind": ck, "title": title, "unit": clean_text(b.get("unit")), "notes": notes}
            if ck == "hbar":
                bars = []
                for bar in b.get("bars") or []:
                    label = clean_text(bar.get("label"))
                    value = _num(bar.get("value"))
                    if value is None:
                        warnings.append(f"Slide {n}: the bar “{label}” has no readable value (“{clean_text(bar.get('value'))}”).")
                        continue
                    parts = []
                    for part in bar.get("parts") or []:
                        pt = clean_text(part.get("value"))
                        parsed = parse_number(pt)
                        share = None
                        if parsed["kind"] == "percent" and parsed["value"] is not None:
                            share = max(0.0, min(1.0, parsed["value"] / 100))
                        elif parsed["kind"] == "number" and parsed["value"] is not None and value:
                            share = max(0.0, min(1.0, parsed["value"] / value))
                        parts.append({"name": clean_text(part.get("name")), "text": pt, "share": share})
                    bars.append({"group": clean_text(bar.get("group")), "label": label, "value": value,
                                 "text": clean_text(bar.get("text")) or clean_text(bar.get("value")), "parts": parts})
                if not bars:
                    continue
                out["bars"] = bars
            else:
                cats = [clean_text(c) for c in (b.get("categories") or [])]
                series = []
                for sr in b.get("series") or []:
                    vals = [clean_text(v) for v in (sr.get("values") or [])]
                    if len(vals) != len(cats):
                        warnings.append(f"Slide {n}: series “{clean_text(sr.get('name'))}” has {len(vals)} values for {len(cats)} categories.")
                        vals = (vals + [""] * len(cats))[:len(cats)]
                    points = [{"text": v, "value": _num(v)} for v in vals]
                    if any(p["value"] is not None for p in points):
                        series.append({"name": clean_text(sr.get("name")), "points": points})
                if not cats or not series:
                    continue
                out["categories"], out["series"] = cats, series
            blocks.append(out)
        elif kind == "table":
            cols = [clean_text(c) for c in (b.get("columns") or [])]
            rows = []
            for r in b.get("rows") or []:
                cells = [{"text": clean_text(c.get("text")), "tone": c.get("tone") if c.get("tone") in TONES else "none"} for c in (r.get("cells") or [])]
                if cols and len(cells) != len(cols):
                    warnings.append(f"Slide {n}: a table row has {len(cells)} cells for {len(cols)} columns ({cells[0]['text'] if cells else '?'}).")
                    cells = (cells + [{"text": "", "tone": "none"}] * len(cols))[:len(cols)]
                rows.append(cells)
            if rows:
                blocks.append({"type": "table", "title": title, "columns": cols, "rows": rows, "notes": notes})
        elif kind == "bullets":
            items = [clean_text(x) for x in (b.get("items") or []) if clean_text(x)]
            if items:
                blocks.append({"type": "bullets", "title": title, "items": items})
        elif kind in ("callout", "text"):
            text = clean_text(b.get("text"))
            if text:
                blocks.append({"type": kind, "title": title, "text": text})
        elif kind == "footnotes":
            items = [clean_text(x) for x in (b.get("items") or []) if clean_text(x)]
            if items:
                blocks.append({"type": "footnotes", "items": items})
    if not blocks and not clean_text(raw.get("title")):
        raise ExtractionError(f"slide {n}: nothing readable was found in the image")
    return {"n": n, "title": clean_text(raw.get("title")), "subtitle": clean_text(raw.get("subtitle")), "blocks": blocks, "warnings": warnings}


# ------------------------------------------------------------------ English labels (same mechanism as factors)
TRANSLATE_PROMPT = """You are translating the text of an internal investment-committee slide deck from Chinese into English, so the same slides can be shown to English readers. The deck covers macro and market updates (central-bank rate paths, inflation, market pricing) and their effect on a portfolio of private credit, CLO, real-estate and other alternative funds.

The message holds two lists of numbered items. "labels" are short chart and table labels: slide titles, panel headers, axis categories, legend names, column headers, table cells. "notes" are sentences: bullet points, call-outs, subtitles and footnotes. Return one entry for every item in both lists, giving its `id` and `english`, its translation. Leave none out.

Labels have to fit in a table cell or beside a bar, so keep them as short as the original and use the standard market term (点阵图 is Dot plot, 加息 is Rate hike, 降息 is Rate cut, 按兵不动 is On hold, 浮动利率 is Floating rate, 估值 is Valuation, 信用风险 is Credit risk, 正面 is Positive, 负面 is Negative, 中性 is Neutral, 受益 is Benefits).

Anything already in English, and any code, stays exactly as it is: fund names, CLO, OIS, CPI, FOMC, SEP, bp, 3Q26, 2026Q4. A month label such as 9月 becomes Sep. Percentages and every other number stay exactly as written; an amount written in 万 inside a sentence is converted to millions, dividing by 100.

Notes should read as plain, natural English, with nothing added and nothing left out."""


def text_strings(doc: dict[str, Any]) -> dict[str, list[str]]:
    labels: list[str] = []
    notes: list[str] = []

    def add(bucket: list[str], value: Any) -> None:
        if isinstance(value, str) and value and value not in labels and value not in notes:
            bucket.append(value)

    add(labels, doc.get("title"))
    for page in doc.get("pages") or []:
        add(labels, page.get("title"))
        add(notes, page.get("subtitle"))
        for b in page.get("blocks") or []:
            add(labels, b.get("title"))
            if b.get("type") == "chart":
                for c in b.get("categories") or []:
                    add(labels, c)
                for sr in b.get("series") or []:
                    add(labels, sr.get("name"))
                for bar in b.get("bars") or []:
                    add(labels, bar.get("group"))
                    add(labels, bar.get("label"))
                    add(labels, bar.get("text"))
                    for part in bar.get("parts") or []:
                        add(labels, part.get("name"))
                for x in b.get("notes") or []:
                    add(notes, x)
            elif b.get("type") == "table":
                for c in b.get("columns") or []:
                    add(labels, c)
                for row in b.get("rows") or []:
                    for cell in row:
                        add(labels, cell.get("text"))
                for x in b.get("notes") or []:
                    add(notes, x)
            elif b.get("type") in ("bullets", "footnotes"):
                for x in b.get("items") or []:
                    add(notes, x)
            elif b.get("type") in ("callout", "text"):
                add(notes, b.get("text"))
    return {"labels": labels, "notes": notes}


def untranslated(doc: dict[str, Any]) -> dict[str, list[str]]:
    have = doc.get("en") or {}
    return {role: [s for s in strings if ff.CJK_RE.search(s) and s not in have] for role, strings in text_strings(doc).items()}


def translate_strings(strings: dict[str, list[str]]) -> dict[str, str]:
    labels, notes = strings.get("labels", []), strings.get("notes", [])
    numbered = dict(enumerate(labels + notes, start=1))
    if not numbered:
        return {}
    payload = {
        "labels": [{"id": i, "text": s} for i, s in numbered.items() if i <= len(labels)],
        "notes": [{"id": i, "text": s} for i, s in numbered.items() if i > len(labels)],
    }
    request = {
        "model": model_name(), "max_tokens": 16000, "system": TRANSLATE_PROMPT,
        "output_config": {"effort": "medium", "format": {"type": "json_schema", "schema": ff.TRANSLATION_SCHEMA}},
        "messages": [{"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=1)}],
    }
    raw, _ = ff._ask_claude(request, declined="Claude declined to translate the slides", too_long="there is too much text to translate in one answer")
    out: dict[str, str] = {}
    for item in raw.get("translations") or []:
        try:
            source = numbered.get(int(item.get("id")))
        except (TypeError, ValueError):
            continue
        english = clean_text(item.get("english"))
        if not (source and english and english != source):
            continue
        if not ff.figures_match(source, english):
            log("translation rejected, its figures differ from the original:", source, "->", english)
            continue
        out[source] = english
    return out


def add_english(doc: dict[str, Any]) -> int:
    doc.setdefault("en", {})
    added = 0
    for _attempt in range(2):
        todo = untranslated(doc)
        if not (todo["labels"] or todo["notes"]):
            break
        found = translate_strings(todo)
        doc["en"].update(found)
        added += len(found)
        if not found:
            break
    doc.pop("en_error", None)
    return added


def translate_month(key: str, force: bool = False) -> dict[str, Any]:
    path = DATA / (key + ".json")
    if not re.fullmatch(r"\d{4}-\d{2}", str(key)) or not path.is_file():
        raise ExtractionError(f"there is no brief for {key}")
    doc = json.loads(path.read_text(encoding="utf-8"))
    if force:
        doc["en"] = {}
    add_english(doc)
    _write_doc(path, doc)
    return doc


def translate_missing() -> int:
    done = 0
    for path in sorted(DATA.glob("*.json")) if DATA.is_dir() else []:
        if not re.fullmatch(r"\d{4}-\d{2}", path.stem):
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        todo = untranslated(doc)
        if not (todo["labels"] or todo["notes"]):
            continue
        try:
            added = add_english(doc)
        except MissingKeyError:
            return done
        except ExtractionError as exc:
            log(f"{path.stem}: English labels not created ({exc})")
            continue
        _write_doc(path, doc)
        done += 1
        log(f"{path.stem}: {added} English label(s) added")
    return done


# ------------------------------------------------------------------ storage
def rebuild_index() -> dict[str, Any]:
    months = sorted(p.stem for p in DATA.glob("*.json") if re.fullmatch(r"\d{4}-\d{2}", p.stem)) if DATA.is_dir() else []
    index = {"months": months}
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return index


def _write_doc(path: Path, doc: dict[str, Any]) -> None:
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save(year: int, month: int, title: str, pages: list[dict[str, Any]], images: list[tuple[bytes, str]], *, model: str) -> dict[str, Any]:
    """Write the month's brief and its images (replacing what the month had). images are (bytes, ext) in page order."""
    key = month_key(year, month)
    DATA.mkdir(parents=True, exist_ok=True)
    folder = DATA / key
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True, exist_ok=True)
    for page, (data, ext) in zip(pages, images):
        name = f"{page['n']:02d}{ext.lower()}"
        (folder / name).write_bytes(data)
        page["source_image"] = name
    doc = {"year": int(year), "month": int(month), "title": clean_text(title), "extracted_at": now_iso(), "model": model,
           "pages": pages, "warnings": [w for p in pages for w in p.get("warnings") or []]}
    _write_doc(DATA / (key + ".json"), doc)
    rebuild_index()
    return doc


def _check_image(image: bytes, ext: str) -> str:
    ext = ext.lower() if ext.startswith(".") else "." + ext.lower()
    if ext not in MEDIA_TYPES:
        raise ExtractionError("every slide must be a PNG, JPEG, WebP or GIF image")
    if not image:
        raise ExtractionError("an image file is empty")
    if len(image) > MAX_IMAGE_BYTES:
        raise ExtractionError("an image is larger than 5 MB; save it smaller and upload again")
    return ext


def extract(year: int, month: int, title: str, images: list[tuple[bytes, str]], progress=None) -> dict[str, Any]:
    """Images (bytes, ext) in order -> Claude, one call per slide -> the saved brief."""
    month_key(year, month)
    if not images:
        raise ExtractionError("drop at least one slide image")
    checked = [(data, _check_image(data, ext)) for data, ext in images]
    pages, model = [], "mock" if mock() else model_name()
    for i, (data, ext) in enumerate(checked, start=1):
        if progress:
            progress(i, len(checked))
        if mock():
            raw = _mock_page(i, title)
        else:
            raw, model = call_claude_page(data, MEDIA_TYPES[ext])
        pages.append(normalize_page(raw, i))
    doc_title = clean_text(title) or next((p["title"] for p in pages if p["title"]), "") or month_key(year, month)
    body_en: dict[str, str] = {}
    en_error = None
    if not mock():
        probe = {"title": doc_title, "pages": pages, "en": body_en}
        try:
            add_english(probe)
            body_en = probe["en"]
        except ExtractionError as exc:
            en_error = str(exc)
            log(f"{month_key(year, month)}: English labels not created ({exc})")
    doc = save(year, month, doc_title, pages, checked, model=model)
    doc["en"] = body_en
    if en_error:
        doc["en_error"] = en_error
    _write_doc(DATA / (month_key(year, month) + ".json"), doc)
    return doc


def _mock_page(n: int, title: str) -> dict[str, Any]:
    """AI_MOCK=1: a placeholder slide with one of each block type."""
    return {
        "title": f"{title or 'Mock brief'} · slide {n}", "subtitle": "AI_MOCK is set: this slide is a placeholder, not a reading of the image.",
        "blocks": [
            {"type": "chart", "title": "Mock line chart", "kind": "line", "unit": "%", "categories": ["2026", "2027", "2028", "长期"],
             "series": [{"name": "9月", "values": ["4.1%", "4.1%", "3.9%", "3.2%"]}, {"name": "6月", "values": ["3.8%", "3.6%", "3.4%", "3.1%"]}],
             "bars": [], "columns": [], "rows": [], "items": [], "text": "", "notes": []},
            {"type": "chart", "title": "Mock horizontal bars ($m)", "kind": "hbar", "unit": "$m", "categories": [], "series": [],
             "bars": [{"group": "浮动为主 · 48%", "label": "PAG BRS", "value": "31.6", "text": "31.6 · 浮动100%", "parts": [{"name": "浮动利率部分", "value": "100%"}]},
                      {"group": "浮动为主 · 48%", "label": "Apollo ABL", "value": "25.4", "text": "25.4 · 浮动52%", "parts": [{"name": "浮动利率部分", "value": "52%"}]},
                      {"group": "固定 / 部分浮动 · 46%", "label": "Oak Street", "value": "41.0", "text": "41.0 · 浮动0%", "parts": [{"name": "浮动利率部分", "value": "0%"}]}],
             "columns": [], "rows": [], "items": [], "text": "", "notes": ["浮动利率部分", "固定/部分浮动"]},
            {"type": "table", "title": "Mock table", "kind": "", "unit": "", "categories": [], "series": [], "bars": [], "columns": ["基金", "收入端", "综合"],
             "rows": [{"cells": [{"text": "OTF", "tone": "none"}, {"text": "正面", "tone": "positive"}, {"text": "短正中负", "tone": "warning"}]},
                      {"cells": [{"text": "Oak Street", "tone": "none"}, {"text": "中性", "tone": "neutral"}, {"text": "中性偏负", "tone": "negative"}]}],
             "items": [], "text": "", "notes": []},
            {"type": "bullets", "title": "", "kind": "", "unit": "", "categories": [], "series": [], "bars": [], "columns": [], "rows": [],
             "items": ["第一点：占位内容。", "第二点：占位内容。"], "text": "", "notes": []},
            {"type": "callout", "title": "", "kind": "", "unit": "", "categories": [], "series": [], "bars": [], "columns": [], "rows": [], "items": [],
             "text": "占位的结论框。", "notes": []},
            {"type": "footnotes", "title": "", "kind": "", "unit": "", "categories": [], "series": [], "bars": [], "columns": [], "rows": [],
             "items": ["1. 来源：占位。"], "text": "", "notes": []},
        ],
    }


# ------------------------------------------------------------------ incoming (GitHub Pages)
def process_incoming() -> int:
    """macro/incoming/<YYYY-MM>.meta.json + <YYYY-MM>-<nn>.<ext> -> one brief per month. Returns months written."""
    if not INCOMING.is_dir():
        return 0
    groups: dict[str, list[Path]] = {}
    metas: dict[str, Path] = {}
    for path in sorted(INCOMING.iterdir()):
        if not path.is_file() or path.name.startswith("."):
            continue
        m = INCOMING_IMG_RE.match(path.name)
        if m:
            groups.setdefault(m.group(1), []).append(path)
            continue
        m = INCOMING_META_RE.match(path.name)
        if m:
            metas[m.group(1)] = path
            continue
        log("ignored (name is not <YYYY-MM>-<nn>.<ext> or <YYYY-MM>.meta.json):", path.name)
    done = 0
    for key, files in sorted(groups.items()):
        year, month = int(key[:4]), int(key[5:])
        title = ""
        if key in metas:
            try:
                title = str(json.loads(metas[key].read_text(encoding="utf-8")).get("title") or "")
            except (OSError, ValueError):
                title = ""
        images = [(p.read_bytes(), p.suffix) for p in sorted(files)]
        try:
            doc = extract(year, month, title, images)
        except MissingKeyError as exc:
            print(f"::warning::Macro / Market: {exc}. {key} stays in macro/incoming until the secret is added.")
            return done
        except ExtractionError as exc:
            FAILED.mkdir(parents=True, exist_ok=True)
            for p in files + ([metas[key]] if key in metas else []):
                shutil.move(str(p), str(FAILED / p.name))
            (FAILED / (key + ".error.txt")).write_text(f"{now_iso()}  {exc}\n", encoding="utf-8")
            print(f"::warning::Macro / Market: {key} could not be read ({exc}); moved to macro/failed.")
            continue
        for p in files + ([metas[key]] if key in metas else []):
            p.unlink()
        done += 1
        log(f"{key}: {len(doc['pages'])} slide(s) saved ({len(doc.get('warnings') or [])} warning(s))")
    return done


# ------------------------------------------------------------------ cli
def main() -> int:
    ap = argparse.ArgumentParser(description="Macro / Market: slide images -> data.")
    ap.add_argument("--apply", action="store_true", help="process macro/incoming/")
    ap.add_argument("--reindex", action="store_true")
    ap.add_argument("--translate", action="store_true", help="create English labels for saved months (all, or the one given)")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--images", type=Path, nargs="*", help="slide images, in order")
    ap.add_argument("--from-raw", type=Path, help="JSON list of pages (the shape Claude returns) instead of calling Claude")
    ap.add_argument("--title", default="")
    ap.add_argument("--year", type=int)
    ap.add_argument("--month", type=int)
    a = ap.parse_args()
    try:
        if a.apply:
            log("processed", process_incoming(), "month(s)")
            translate_missing()
            rebuild_index()
            return 0
        if a.translate:
            if a.year and a.month:
                doc = translate_month(month_key(a.year, a.month), a.force)
                log(f"{month_key(a.year, a.month)}: {len(doc.get('en') or {})} English label(s)")
            else:
                log("months updated:", translate_missing())
            return 0
        if a.reindex:
            log("index:", rebuild_index()["months"])
            return 0
        if not (a.year and a.month and (a.images or a.from_raw)):
            ap.error("give --apply, --reindex, --translate, or --year/--month with --images or --from-raw")
        if a.from_raw:
            raws = json.loads(a.from_raw.read_text(encoding="utf-8"))
            pages = [normalize_page(r, i) for i, r in enumerate(raws, start=1)]
            images = [(p.read_bytes(), p.suffix) for p in (a.images or [])]
            images = (images + [(b"", ".png")] * len(pages))[:len(pages)]
            title = clean_text(a.title) or next((p["title"] for p in pages if p["title"]), "")
            doc = save(a.year, a.month, title, pages, [(d, e) for d, e in images], model="manual transcription")
            for page in doc["pages"]:  # pages without an image keep no source link
                if not (DATA / month_key(a.year, a.month) / page.get("source_image", "")).stat().st_size:
                    (DATA / month_key(a.year, a.month) / page["source_image"]).unlink()
                    page["source_image"] = ""
            _write_doc(DATA / (month_key(a.year, a.month) + ".json"), doc)
        else:
            doc = extract(a.year, a.month, a.title, [(p.read_bytes(), p.suffix) for p in a.images])
    except ExtractionError as exc:
        log("error:", exc)
        return 1
    log(f"{doc['year']}-{doc['month']:02d}: {len(doc['pages'])} slide(s) saved;", len(doc.get("warnings") or []), "warning(s)")
    for w in doc.get("warnings") or []:
        log("  warning:", w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
