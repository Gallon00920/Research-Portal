#!/usr/bin/env python3
"""Investment performance (fund key factors): turn an uploaded image (a slide or a table screenshot) into data.

Two tabs, one month per file:
  performance   the fund performance table            -> a real HTML table on the site
  budget        the budget completion slide (charts)  -> real charts on the site

Claude reads the image and transcribes it into a fixed JSON shape (structured output, every
value kept as the text printed in the image); this script then parses the numbers, runs
arithmetic checks (totals, stacked segments) and writes the result. A known gap is explained
with an automatic note instead of a warning: the budget total of the fund performance table
includes projects the table hides, listed in factors/config.json. Output:

  factors/data/<tab>/<YYYY-MM>.json     the data the page renders
  factors/data/<tab>/<YYYY-MM>.<ext>    the uploaded image, kept for checking
  factors/data/index.json               which months exist for each tab

Usage
  python factors/scripts/extract_factors.py --apply
      process every factors/incoming/<tab>-<YYYY>-<MM>.<ext> (what the site commits on upload);
      this is what the GitHub workflow runs
  python factors/scripts/extract_factors.py --image slide.png --tab budget --year 2026 --month 9
      extract one local image
  python factors/scripts/extract_factors.py --from-raw raw.json --tab budget --year 2026 --month 9 [--image slide.png]
      skip Claude: normalise an already transcribed JSON (same shape Claude returns)
  python factors/scripts/extract_factors.py --note "…" [--explains-warnings] --tab budget --year 2026 --month 9
      write the month's note (repeat --note for several); --explains-warnings hides its warnings
  python factors/scripts/extract_factors.py --move-to 2026-09 [--replace] --tab performance --year 2026 --month 8
      file a month under another date (it was uploaded with the wrong one)
  python factors/scripts/extract_factors.py --translate [--force] [--tab budget --year 2026 --month 9]
      create the English labels for saved months that still show Chinese (all months, or one)
  python factors/scripts/extract_factors.py --recheck
      run the arithmetic checks again on every saved month (after editing config.json, or a rule change)
  python factors/scripts/extract_factors.py --reindex

Needs ANTHROPIC_API_KEY for the first two forms and for --translate. FACTORS_MODEL overrides the model.
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

ROOT = Path(__file__).resolve().parents[1]  # factors/
DATA = ROOT / "data"
INCOMING = ROOT / "incoming"
FAILED = ROOT / "failed"
CONFIG = ROOT / "config.json"

TABS = ("performance", "budget")
DEFAULT_MODEL = "claude-opus-5-5"
MEDIA_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024
INCOMING_RE = re.compile(r"^(performance|budget)-(\d{4})-(\d{2})\.(png|jpe?g|webp|gif)$", re.I)
# a request to file a month under another date: {"to": "YYYY-MM", "replace": false}
MOVE_RE = re.compile(r"^(performance|budget)-(\d{4}-\d{2})\.move\.json$", re.I)


class ExtractionError(Exception):
    """The image could not be turned into data (bad input, refusal, unusable answer)."""


class MissingKeyError(ExtractionError):
    """No Anthropic credential is configured."""


def log(*parts: Any) -> None:
    print("[factors]", *parts, file=sys.stderr, flush=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def month_key(year: int, month: int) -> str:
    if not (2000 <= int(year) <= 2100 and 1 <= int(month) <= 12):
        raise ExtractionError(f"invalid year/month: {year}-{month}")
    return f"{int(year):04d}-{int(month):02d}"


# ------------------------------------------------------------------ what Claude returns
def _obj(props: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


_STR = {"type": "string"}
_STRS = {"type": "array", "items": _STR}

RAW_SCHEMAS: dict[str, dict[str, Any]] = {
    "performance": _obj({
        "title": _STR,
        "name_header": _STR,
        "columns": {"type": "array", "items": _obj({"label": _STR, "group": _STR})},
        "rows": {"type": "array", "items": _obj({"name": _STR, "is_total": {"type": "boolean"}, "cells": _STRS})},
        "footnotes": _STRS,
    }),
    "budget": _obj({
        "title": _STR,
        "sections": {"type": "array", "items": _obj({
            "title": _STR,
            "blocks": {"type": "array", "items": _obj({
                "charts": {"type": "array", "items": _obj({
                    "title": _STR,
                    "bars": {"type": "array", "items": _obj({
                        "group": _STR,
                        "label": _STR,
                        "kind": {"type": "string", "enum": ["budget", "actual"]},
                        "value": _STR,
                        "segments": {"type": "array", "items": _obj({"label": _STR, "value": _STR})},
                    })},
                })},
                "notes": _STRS,
            })},
        })},
    }),
}

PROMPTS: dict[str, str] = {
    "performance": """This image is a fund performance table from an internal investment report. Transcribe it exactly so it can be rebuilt as a real table. Accuracy matters more than anything else here: these are financial figures, so read every digit carefully and never estimate or fill in a value you cannot see.

- title: the table's title if one is printed, otherwise an empty string.
- name_header: the header of the first column (the fund name column).
- columns: every column after the name column, left to right. `label` is the column's own header with line breaks joined by a space (for example "YTD (LTM avg)"). `group` is the header that spans above it (for example "现金收息"); use an empty string when no header spans above the column.
- rows: every row top to bottom, including the total row. `name` is the first cell. `cells` has exactly one entry per column, in column order, written exactly as printed: keep thousands separators, percent signs, minus signs and decimals ("1,481,409", "-14.2%", "5.6%"). A dash or an empty cell is "-". Set is_total to true only for the total / summary row.
- footnotes: any notes printed under the table, one string each; an empty list if none.

Keep the original language of every label; do not translate.""",
    "budget": """This image is a budget completion slide from an internal investment report: bar charts comparing budget with actual figures, with bullet-point commentary under them. Transcribe it exactly so the charts can be redrawn from data. Accuracy matters more than anything else here: read every number from its printed label, never from the bar's height, and never estimate a value that is not printed.

- title: the slide title.
- sections: the titled panels, left to right (for example one for cash inflow and one for capital calls). `title` is the text in the panel's header box, including the unit if it is printed there.
- blocks: within a section, each group of charts that shares one commentary box, left to right. A section with a single commentary box has a single block.
- charts: the charts in the block, left to right. `title` is the small heading above the chart, or an empty string if it has none. Charts separated by a dashed divider or with their own heading are separate charts.
- bars: every bar left to right. `kind` is "budget" for a budget bar (usually grey) and "actual" for an actual bar. `label` is the text under that bar with line breaks joined by a space (for example "预算", "实际", "3Q26 预算"); when the only text under a pair of bars is a shared label, put that text in `group` and use "预算" / "实际" as each bar's label. `group` is otherwise the shared label under a pair of bars, or an empty string.
- value: the number printed on top of the bar, exactly as printed, with its unit ("731万", "1,983万", "5.8万").
- segments: when a bar is stacked from several parts (for example one part per month, listed beside or above the bar), list every part from the bottom of the stack to the top, each with its label ("7月") and printed value ("159万"). A part that is drawn and labelled but has no number of its own still gets an entry: give its label and an empty value (for example a part marked "同4月收息", meaning the same amount as April, with nothing printed beside it). Do not work out or copy a number that is not printed next to that part. When a bar is a single block drawn in the style of one part (for example dashed like the latest month), give it one segment with that part's label. Otherwise an empty list.
- notes: the bullet points of the block's commentary box, one string per bullet, exactly as written.

Keep the original language of every label and note; do not translate.""",
}


# ------------------------------------------------------------------ Claude call
def _trust_os_certificates() -> None:
    """Behind a TLS-inspecting corporate proxy, validate with the operating system's store."""
    try:
        import truststore
    except ImportError:
        return
    truststore.inject_into_ssl()


def call_claude(image: bytes, media_type: str, tab: str) -> tuple[dict[str, Any], str]:
    """Send the image to Claude and return (transcription, model that answered)."""
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        raise MissingKeyError("ANTHROPIC_API_KEY is not set, so the image cannot be read by Claude")
    try:
        import anthropic
    except ImportError as exc:
        raise ExtractionError("the anthropic package is not installed (pip install -r factors/requirements.txt)") from exc
    _trust_os_certificates()

    model = os.environ.get("FACTORS_MODEL", "").strip() or DEFAULT_MODEL
    request: dict[str, Any] = {
        "model": model,
        "max_tokens": 16000,
        # effort high: a dense table of figures is exactly where careful reading pays
        "output_config": {"effort": "high", "format": {"type": "json_schema", "schema": RAW_SCHEMAS[tab]}},
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": base64.standard_b64encode(image).decode("ascii")}},
                {"type": "text", "text": PROMPTS[tab]},
            ],
        }],
    }
    return _ask_claude(request, declined="Claude declined to read this image",
                       too_long="the image holds more data than fits in one answer; crop it and upload again")


def _ask_claude(request: dict[str, Any], *, declined: str, too_long: str) -> tuple[dict[str, Any], str]:
    """Send one structured-output request and return (parsed JSON answer, model that answered)."""
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        raise MissingKeyError("ANTHROPIC_API_KEY is not set, so Claude cannot be called")
    try:
        import anthropic
    except ImportError as exc:
        raise ExtractionError("the anthropic package is not installed (pip install -r factors/requirements.txt)") from exc
    _trust_os_certificates()
    model = request["model"]
    betas: list[str] = []
    # if a safety classifier declines the request, let the API re-run it on a fallback model
    if os.environ.get("FACTORS_FALLBACKS", "1").strip().lower() not in {"0", "false", "no"}:
        betas.append("server-side-fallback-2026-07-01")
        request = dict(request, fallbacks="default")

    client = anthropic.Anthropic()
    try:
        if betas:
            response = client.beta.messages.create(betas=betas, **request)
        else:
            response = client.messages.create(**request)
    except anthropic.AuthenticationError as exc:
        raise ExtractionError("the Anthropic API key was rejected (401)") from exc
    except anthropic.PermissionDeniedError as exc:
        raise ExtractionError(f"the Anthropic API key may not use this model or feature (403): {exc.message}") from exc
    except anthropic.RateLimitError as exc:
        raise ExtractionError("the Anthropic API rate limit was hit; try again in a minute") from exc
    except anthropic.BadRequestError as exc:
        raise ExtractionError(f"the Anthropic API rejected the request (400): {exc.message}") from exc
    except anthropic.APIStatusError as exc:
        raise ExtractionError(f"Anthropic API error {exc.status_code}: {exc.message}") from exc
    except anthropic.APIConnectionError as exc:
        raise ExtractionError(f"could not reach the Anthropic API: {exc}") from exc

    if response.stop_reason == "refusal":
        raise ExtractionError(declined)
    if response.stop_reason == "max_tokens":
        raise ExtractionError(too_long)
    text = next((block.text for block in response.content if block.type == "text"), "")
    try:
        raw = json.loads(text)
    except ValueError as exc:
        raise ExtractionError("Claude's answer was not valid JSON") from exc
    return raw, getattr(response, "model", model) or model


# ------------------------------------------------------------------ English labels
# The uploads are usually Chinese slides. After an image is read, Claude also translates its
# labels and commentary, and the page shows the English when its interface is in English.
# Translations live in the month's file as "en": {original text: English text}; the original
# is always kept and is what the Chinese interface shows.
CJK_RE = re.compile(r"[㐀-䶿一-鿿]")

TRANSLATION_SCHEMA = _obj({"translations": {"type": "array", "items": _obj({"id": {"type": "integer"}, "english": _STR})}})

TRANSLATE_PROMPT = """You are translating the labels and commentary of an internal fund report from Chinese into English, so the same charts and tables can be shown to English readers. The report covers private credit and alternative funds: cash interest received, budgets against actuals, capital calls, yields and IRR.

The message holds two lists of numbered items. "labels" are short chart and table labels: titles, column headers, labels under bars, legend entries. "notes" are commentary sentences and footnotes. Return one entry for every item in both lists, giving its `id` and `english`, its translation. Leave none out.

Labels have to fit in a table header or under a bar, so keep them as short as the original and use the standard reporting term (for example 预算 is Budget, 实际 is Actual, 现金收息 is Cash interest received, 归还本金 is Principal repaid, call款 is Capital calls, 完成度 is Completion).

Anything already in English, and any code, stays exactly as it is: fund names, AWIS, AID, YTD, LTM, IRR, 3Q26, 9M26, 1H26, 2026Q1. So "3Q26 预算" becomes "3Q26 Budget". A month label such as 7月 becomes Jul, and 26年7月 becomes July 2026.

Amounts: the English page shows amounts in millions. A unit such as 万美元 therefore becomes "US$ million", and an amount written in 万 inside a sentence is converted to millions, dividing by 100 (159万 becomes 1.59 million, 2,102万 becomes 21.02 million). Percentages and every other number stay exactly as written.

Notes should read as plain, natural English, with nothing added and nothing left out."""


def text_strings(doc: dict[str, Any]) -> dict[str, list[str]]:
    """Every label and sentence a reader sees in a month, by role. Figures are not text."""
    labels: list[str] = []
    notes: list[str] = []

    def add(bucket: list[str], value: Any) -> None:
        if isinstance(value, str) and value and value not in labels and value not in notes:
            bucket.append(value)

    add(labels, doc.get("title"))
    if "columns" in doc:  # fund performance table
        add(labels, doc.get("name_header"))
        for col in doc.get("columns") or []:
            add(labels, col.get("group"))
            add(labels, col.get("label"))
        for row in doc.get("rows") or []:
            add(labels, row.get("name"))
        for note in doc.get("footnotes") or []:
            add(notes, note)
    for section in doc.get("sections") or []:  # budget completion slide
        add(labels, section.get("title"))
        for block in section.get("blocks") or []:
            for chart in block.get("charts") or []:
                add(labels, chart.get("title"))
                for bar in chart.get("bars") or []:
                    add(labels, bar.get("group"))
                    add(labels, bar.get("label"))
                    for seg in bar.get("segments") or []:
                        add(labels, seg.get("label"))
            for note in block.get("notes") or []:
                add(notes, note)
    return {"labels": labels, "notes": notes}


def untranslated(doc: dict[str, Any]) -> dict[str, list[str]]:
    """The strings that still need English: they contain Chinese and have no translation yet."""
    have = doc.get("en") or {}
    return {role: [s for s in strings if CJK_RE.search(s) and s not in have] for role, strings in text_strings(doc).items()}


def translate_strings(strings: dict[str, list[str]]) -> dict[str, str]:
    """Ask Claude for the English of the given labels and notes. Returns {original: English}.
    Items are numbered and answered by number, so nothing depends on the text being echoed back."""
    labels, notes = strings.get("labels", []), strings.get("notes", [])
    numbered = dict(enumerate(labels + notes, start=1))
    if not numbered:
        return {}
    payload = {
        "labels": [{"id": i, "text": text} for i, text in numbered.items() if i <= len(labels)],
        "notes": [{"id": i, "text": text} for i, text in numbered.items() if i > len(labels)],
    }
    request = {
        "model": os.environ.get("FACTORS_MODEL", "").strip() or DEFAULT_MODEL,
        "max_tokens": 16000,
        "system": TRANSLATE_PROMPT,
        "output_config": {"effort": "medium", "format": {"type": "json_schema", "schema": TRANSLATION_SCHEMA}},
        "messages": [{"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=1)}],
    }
    raw, _model = _ask_claude(request, declined="Claude declined to translate the labels",
                              too_long="there is too much text to translate in one answer")
    out: dict[str, str] = {}
    for item in raw.get("translations") or []:
        try:
            source = numbered.get(int(item.get("id")))
        except (TypeError, ValueError):
            continue
        english = clean_text(item.get("english"))
        if not (source and english and english != source):
            continue
        if not figures_match(source, english):
            # better the original sentence than an English one with a wrong number
            log("translation rejected, its figures differ from the original:", source, "->", english)
            continue
        out[source] = english
    return out


def _numbers(text: str) -> list[float]:
    return [float(x.replace(",", "")) for x in re.findall(r"(?<![\w.])\d[\d,]*(?:\.\d+)?", text)]


def figures_match(source: str, english: str) -> bool:
    """A translation may change words, not figures: every percentage must reappear, and every
    amount written in 万 (or 亿) must reappear converted to millions."""
    percent = r"\d[\d,]*(?:\.\d+)?\s*[%％]"
    as_numbers = lambda found: sorted(float(re.sub(r"[^\d.]", "", x)) for x in found)
    if as_numbers(re.findall(percent, source)) != as_numbers(re.findall(percent, english)):
        return False
    available = _numbers(english)
    for amount, unit in re.findall(r"(\d[\d,]*(?:\.\d+)?)\s*(万|亿)", source):
        value = float(amount.replace(",", ""))
        millions = value / 100 if unit == "万" else value * 100
        if not any(abs(n - millions) < 1e-6 for n in available):
            return False
    return True


def add_english(doc: dict[str, Any]) -> int:
    """Translate whatever in this month still lacks English. Returns how many strings were added.
    One answer can leave items out (it has happened with a whole list of notes), so anything
    still missing is asked for once more; what is missing after that is left for a later run."""
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


def translate_month(tab: str, key: str, force: bool = False) -> dict[str, Any]:
    """(Re)create the English labels of a saved month. force starts again from nothing."""
    if tab not in TABS or not re.fullmatch(r"\d{4}-\d{2}", str(key)):
        raise ExtractionError("unknown sub-tab or month")
    path = DATA / tab / (key + ".json")
    if not path.is_file():
        raise ExtractionError(f"there is no data for {tab} {key}")
    doc = json.loads(path.read_text(encoding="utf-8"))
    if force:
        doc["en"] = {}
    add_english(doc)
    _write_doc(path, doc)
    return doc


def translate_missing() -> int:
    """Give every saved month that still shows Chinese its English labels. Returns months updated."""
    done = 0
    for tab in TABS:
        for path in sorted((DATA / tab).glob("*.json")) if (DATA / tab).is_dir() else []:
            doc = json.loads(path.read_text(encoding="utf-8"))
            todo = untranslated(doc)
            if not (todo["labels"] or todo["notes"]):
                continue
            try:
                added = add_english(doc)
            except MissingKeyError:
                return done  # nothing can be translated without the key; the next run tries again
            except ExtractionError as exc:
                log(f"{tab} {path.stem}: English labels not created ({exc})")
                continue
            _write_doc(path, doc)
            done += 1
            log(f"{tab} {path.stem}: {added} English label(s) added")
    return done


# ------------------------------------------------------------------ number parsing
_DASHES = {"", "-", "–", "—", "−", "n/a", "na", "nm", "n.a."}


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value if value is not None else "")).strip()


def parse_number(text: Any) -> dict[str, Any]:
    """'1,481,409' / '-14.2%' / '5.8万' / '(1.2%)' / '-'  ->  {value, kind, decimals, unit}.
    kind is 'number', 'percent', 'empty' (a dash) or 'text' (not a number)."""
    s = clean_text(text)
    if s.lower() in _DASHES:
        return {"value": None, "kind": "empty", "decimals": 0, "unit": ""}
    body = s.replace(",", "").replace("，", "").replace(" ", "").replace("−", "-").replace("–", "-")
    negative = False
    if body.startswith("(") and body.endswith(")"):
        negative, body = True, body[1:-1]
    m = re.fullmatch(r"([+-]?)(\d+(?:\.\d+)?|\.\d+)(%|万|亿|[kKmM]|bn)?", body)
    if not m:
        return {"value": None, "kind": "text", "decimals": 0, "unit": ""}
    sign, digits, unit = m.group(1), m.group(2), m.group(3) or ""
    value = float(digits)
    if sign == "-" or negative:
        value = -value
    decimals = len(digits.split(".")[1]) if "." in digits else 0
    if decimals == 0:
        value = int(value)
    return {"value": value, "kind": "percent" if unit == "%" else "number", "decimals": decimals, "unit": "" if unit == "%" else unit}


def _close(a: float, b: float, rel: float, absolute: float) -> bool:
    return abs(a - b) <= max(absolute, rel * max(abs(a), abs(b)))


# ------------------------------------------------------------------ normalise: performance table
def _column_style(label: str, group: str) -> str:
    low, glow = label.lower(), group.lower()
    if "completion" in low or "完成" in label:
        return "completion"
    if low.startswith("irr") or glow.startswith("irr"):
        return "irr"
    if "ltm" in low:
        return "heat"
    return ""


def normalize_performance(raw: dict[str, Any]) -> dict[str, Any]:
    columns_in = raw.get("columns") or []
    rows_in = raw.get("rows") or []
    if not columns_in or not rows_in:
        raise ExtractionError("no table was found in the image")
    n = len(columns_in)
    warnings: list[str] = []

    rows = []
    for row in rows_in:
        name = clean_text(row.get("name"))
        cells = [clean_text(c) for c in (row.get("cells") or [])]
        if len(cells) != n:
            warnings.append(f"Row “{name}” has {len(cells)} values for {n} columns; check it against the image.")
            cells = (cells + ["-"] * n)[:n]
        parsed = [parse_number(c) for c in cells]
        is_total = bool(row.get("is_total")) or bool(re.search(r"\btotal\b|合计|总计", name, re.I))
        rows.append({
            "name": name,
            "total": is_total,
            "text": ["-" if p["kind"] == "empty" else c for c, p in zip(cells, parsed)],
            "cells": [p["value"] for p in parsed],
            "_parsed": parsed,
        })

    columns = []
    for j, col in enumerate(columns_in):
        label, group = clean_text(col.get("label")), clean_text(col.get("group"))
        kinds = [r["_parsed"][j]["kind"] for r in rows]
        if "percent" in kinds:
            ctype = "percent"
        elif "number" in kinds:
            ctype = "number"
        else:
            ctype = "text"
        decimals = max([r["_parsed"][j]["decimals"] for r in rows] or [0])
        columns.append({"label": label, "group": group, "type": ctype, "decimals": decimals, "style": _column_style(label, group)})

    column_warnings, auto_notes = check_performance_totals(columns, rows)
    warnings += column_warnings

    for r in rows:
        del r["_parsed"]
    return {
        "title": clean_text(raw.get("title")),
        "name_header": clean_text(raw.get("name_header")),
        "columns": columns,
        "rows": rows,
        "footnotes": [clean_text(f) for f in (raw.get("footnotes") or []) if clean_text(f)],
        "warnings": warnings,
        "auto_notes": auto_notes,
    }


COLUMN_WARNING_PREFIX = "Column “"
_COUNT_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}


def load_config() -> dict[str, Any]:
    try:
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return cfg if isinstance(cfg, dict) else {}


def hidden_budget_items() -> tuple[re.Pattern[str], list[tuple[str, float]]]:
    """(which column the rule applies to, [(project name, budget amount), ...]) from factors/config.json."""
    rule = (load_config().get("performance") or {}).get("hidden_budget_items") or {}
    items = []
    for item in rule.get("items") or []:
        try:
            name, amount = clean_text(item.get("name")), float(item.get("amount"))
        except (AttributeError, TypeError, ValueError):
            continue
        if name and amount:
            items.append((name, int(amount) if amount == int(amount) else amount))
    try:
        pattern = re.compile(str(rule.get("column") or "预算|budget"), re.I)
    except re.error:
        pattern = re.compile("预算|budget", re.I)
    return pattern, items


def check_performance_totals(columns: list[dict[str, Any]], rows: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    """Each amount column should add up to the total row. Returns (warnings, automatic notes).

    One gap is expected and explained rather than flagged: the budget column's total includes
    projects the table hides (factors/config.json). When the total exceeds the rows by exactly
    the sum of their budgets, a note naming them is written instead of a warning.
    """
    warnings: list[str] = []
    notes: list[str] = []
    totals = [r for r in rows if r.get("total")]
    body = [r for r in rows if not r.get("total")]
    if len(totals) != 1 or not body:
        return warnings, notes
    pattern, hidden = hidden_budget_items()
    expected_gap = sum(amount for _, amount in hidden)
    for j, col in enumerate(columns):
        if col.get("type") != "number":
            continue
        printed = totals[0]["cells"][j]
        if printed is None:
            continue
        summed = sum(r["cells"][j] or 0 for r in body)
        # each printed figure is rounded, so allow one unit of the last digit per row and no more:
        # a single misread digit is far larger than that
        slack = len(body) * 10 ** -int(col.get("decimals") or 0)
        if _close(summed, printed, rel=0, absolute=slack):
            continue
        label = col.get("label") or ""
        if hidden and pattern.search(label) and _close(printed - summed, expected_gap, rel=0, absolute=slack):
            count = _COUNT_WORDS.get(len(hidden), str(len(hidden)))
            listed = " and ".join(f"{name}: {amount:,}" for name, amount in hidden)
            notes.append(
                f"The {label} total of {printed:,} includes {count} new project{'s' if len(hidden) != 1 else ''} "
                f"that {'are' if len(hidden) != 1 else 'is'} hidden in this table: {listed}. "
                f"The fund rows shown add up to {summed:,}."
            )
            continue
        warnings.append(f"{COLUMN_WARNING_PREFIX}{label}”: the rows add up to {summed:,.0f} but the total row says {printed:,.0f}.")
    return warnings, notes


def recheck(path: Path) -> dict[str, Any] | None:
    """Run the arithmetic checks again on a saved month (after config.json or the rules changed).
    Hand-written notes and the figures themselves are left as they are."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("tab") == "performance":
        column_warnings, auto_notes = check_performance_totals(doc.get("columns") or [], doc.get("rows") or [])
        doc["warnings"] = [w for w in (doc.get("warnings") or []) if not w.startswith(COLUMN_WARNING_PREFIX)] + column_warnings
        doc["auto_notes"] = auto_notes
    elif doc.get("tab") == "budget":
        recheck_budget(doc)
    else:
        return None
    _tidy_annotations(doc)
    _write_doc(path, doc)
    return doc


def _tidy_annotations(doc: dict[str, Any]) -> None:
    """A hand-written note that repeats an automatic one is dropped; a warning marked as
    explained stays marked only while that warning exists."""
    auto = doc.get("auto_notes") or []
    doc["notes"] = [n for n in (doc.get("notes") or []) if n not in auto]
    doc["dismissed"] = [w for w in (doc.get("dismissed") or []) if w in (doc.get("warnings") or [])]


# ------------------------------------------------------------------ normalise: budget slide
def normalize_budget(raw: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    sections = []
    for section in raw.get("sections") or []:
        blocks = []
        for block in section.get("blocks") or []:
            charts = []
            for chart in block.get("charts") or []:
                bars = []
                for bar in chart.get("bars") or []:
                    label, group = clean_text(bar.get("label")), clean_text(bar.get("group"))
                    parsed = parse_number(bar.get("value"))
                    if parsed["value"] is None:
                        warnings.append(f"A bar labelled “{label or group}” has no readable value (“{clean_text(bar.get('value'))}”).")
                        continue
                    segments = []
                    for seg in bar.get("segments") or []:
                        sp = parse_number(seg.get("value"))
                        seg_label = clean_text(seg.get("label"))
                        if sp["value"] is None:
                            if seg_label:  # drawn and labelled on the slide, with no number of its own
                                segments.append({"label": seg_label, "value": None, "text": ""})
                            continue
                        segments.append({"label": seg_label, "value": sp["value"], "text": clean_text(seg.get("value"))})
                    warnings += resolve_segments(group or label, parsed["value"], segments)
                    bars.append({
                        "group": group,
                        "label": label,
                        "kind": "budget" if bar.get("kind") == "budget" else "actual",
                        "value": parsed["value"],
                        "text": clean_text(bar.get("value")),
                        "unit": parsed["unit"],
                        "segments": segments,
                    })
                if bars:
                    charts.append({"title": clean_text(chart.get("title")), "bars": bars})
            notes = [clean_text(note) for note in (block.get("notes") or []) if clean_text(note)]
            if charts or notes:
                blocks.append({"charts": charts, "notes": notes})
        if blocks:
            sections.append({"title": clean_text(section.get("title")), "blocks": blocks})
    if not any(chart["bars"] for s in sections for b in s["blocks"] for chart in b["charts"]):
        raise ExtractionError("no charts were found in the image")
    return {"title": clean_text(raw.get("title")), "sections": sections, "warnings": warnings}


PART_WARNING_PREFIX = "“"   # every warning about the parts of a bar starts with the bar's name in quotes


def resolve_segments(name: str, total: float, segments: list[dict[str, Any]]) -> list[str]:
    """Size the parts of a stacked bar that the slide labels without a number, then check the stack.

    A slide can mark a part by month and source and print no figure for it ("同4月收息": the same
    as April). Such a part is kept and its size is worked out as what is left of the bar once
    the numbered parts are taken off; it is marked "derived", and the page shows its label as
    the slide does. With one such part the stack adds up by construction. Returns warnings.
    """
    for seg in segments:  # start again from what was printed, so this can be re-run on saved data
        if seg.pop("derived", False):
            seg["value"] = None
    unknown = [seg for seg in segments if seg["value"] is None]
    known = sum(seg["value"] for seg in segments if seg["value"] is not None)
    slack = max(len(segments), 0.01 * abs(total))  # printed figures are rounded
    if unknown:
        rest = total - known
        if rest < -slack:
            for seg in unknown:
                seg["value"], seg["derived"] = 0, True
            return [f"“{name}”: a part has no printed number, and the other parts already add up to {known:g} against a bar of {total:g}."]
        share = max(rest, 0) / len(unknown)
        share = int(share) if share == int(share) else round(share, 2)
        for seg in unknown:
            seg["value"], seg["derived"] = share, True
        if len(unknown) > 1:
            return [f"“{name}”: {len(unknown)} parts have no printed number; the {rest:g} left of the bar is split equally between them."]
        return []
    if len(segments) > 1 and abs(known - total) > slack:
        return [f"“{name}”: the parts add up to {known:g} but the bar says {total:g}."]
    return []


def recheck_budget(doc: dict[str, Any]) -> None:
    """Size unnumbered parts and check every stack again on a saved budget month."""
    warnings = [w for w in (doc.get("warnings") or []) if not w.startswith(PART_WARNING_PREFIX)]
    for section in doc.get("sections") or []:
        for block in section.get("blocks") or []:
            for chart in block.get("charts") or []:
                for bar in chart.get("bars") or []:
                    warnings += resolve_segments(bar.get("group") or bar.get("label") or "", bar.get("value") or 0, bar.get("segments") or [])
    doc["warnings"] = warnings


NORMALIZERS = {"performance": normalize_performance, "budget": normalize_budget}


# ------------------------------------------------------------------ storage
def rebuild_index() -> dict[str, Any]:
    tabs = {}
    for tab in TABS:
        folder = DATA / tab
        months = sorted(p.stem for p in folder.glob("*.json") if re.fullmatch(r"\d{4}-\d{2}", p.stem)) if folder.is_dir() else []
        tabs[tab] = months
    index = {"tabs": tabs}
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return index


def save(tab: str, year: int, month: int, body: dict[str, Any], *, model: str, image: bytes | None, ext: str) -> dict[str, Any]:
    key = month_key(year, month)
    folder = DATA / tab
    folder.mkdir(parents=True, exist_ok=True)
    kept = _annotations(folder / (key + ".json"))
    for old in folder.glob(key + ".*"):  # an upload for a month that already has data replaces it
        old.unlink()
    source = ""
    if image is not None:
        source = key + ext.lower()
        (folder / source).write_bytes(image)
    doc = {"tab": tab, "year": int(year), "month": int(month), "extracted_at": now_iso(), "model": model, "source_image": source}
    doc.update(body)
    # what a person wrote about this month survives a new upload. A warning they marked as
    # explained stays hidden only if the new reading raises the very same warning again.
    doc["notes"], doc["dismissed"] = kept["notes"], kept["dismissed"]
    _tidy_annotations(doc)
    _write_doc(folder / (key + ".json"), doc)
    rebuild_index()
    return doc


def _write_doc(path: Path, doc: dict[str, Any]) -> None:
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _annotations(path: Path) -> dict[str, list[str]]:
    """The notes and the explained warnings already saved for a month (empty if there are none)."""
    try:
        old = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"notes": [], "dismissed": []}
    as_list = lambda v: [str(x) for x in v] if isinstance(v, list) else []
    return {"notes": as_list(old.get("notes")), "dismissed": as_list(old.get("dismissed"))}


def move_month(tab: str, key: str, year: int, month: int, replace: bool = False) -> dict[str, Any]:
    """File a month's data under another year / month (it was uploaded with the wrong date).

    The data, its notes and the uploaded image all move. If the target month already has data
    the move is refused unless replace is true, in which case that data is overwritten.
    """
    if tab not in TABS or not re.fullmatch(r"\d{4}-\d{2}", str(key)):
        raise ExtractionError("unknown sub-tab or month")
    new_key = month_key(year, month)
    if new_key == key:
        raise ExtractionError("the data is already filed under that month")
    folder = DATA / tab
    src = folder / (key + ".json")
    if not src.is_file():
        raise ExtractionError(f"there is no data for {tab} {key}")
    if (folder / (new_key + ".json")).exists() and not replace:
        raise ExtractionError(f"{new_key} already has data; choose to replace it, or pick another month")
    doc = json.loads(src.read_text(encoding="utf-8"))
    for old in folder.glob(new_key + ".*"):
        old.unlink()
    image, new_image = str(doc.get("source_image") or ""), ""
    if image and (folder / image).is_file():
        new_image = new_key + Path(image).suffix.lower()
        (folder / image).rename(folder / new_image)
    doc["year"], doc["month"], doc["source_image"] = int(year), int(month), new_image
    _write_doc(folder / (new_key + ".json"), doc)
    src.unlink()
    rebuild_index()
    return doc


MAX_NOTES, MAX_NOTE_CHARS = 20, 2000


def set_notes(tab: str, key: str, notes: list[Any], dismissed: list[Any]) -> dict[str, Any]:
    """Save the notes for one month and which of its warnings those notes explain.

    notes      sentences shown in the "Note" box above the chart or table
    dismissed  warning texts (exactly as stored) that the notes explain; the page hides them.
               The warnings themselves stay in the file, so the record of what the checks
               found is kept.
    """
    if tab not in TABS or not re.fullmatch(r"\d{4}-\d{2}", str(key)):
        raise ExtractionError("unknown sub-tab or month")
    path = DATA / tab / (key + ".json")
    if not path.is_file():
        raise ExtractionError(f"there is no data for {tab} {key}")
    doc = json.loads(path.read_text(encoding="utf-8"))
    clean = [clean_text(n)[:MAX_NOTE_CHARS] for n in (notes or []) if clean_text(n)][:MAX_NOTES]
    wanted = {str(w) for w in (dismissed or [])}
    hidden = [w for w in (doc.get("warnings") or []) if w in wanted]
    if hidden and not clean:
        raise ExtractionError("write the note that explains the warning before hiding it")
    doc["notes"], doc["dismissed"] = clean, hidden
    _write_doc(path, doc)
    return doc


def extract(tab: str, year: int, month: int, image: bytes, ext: str) -> dict[str, Any]:
    """Image -> Claude -> checked data on disk. Returns the saved document."""
    if tab not in TABS:
        raise ExtractionError(f"unknown tab: {tab}")
    ext = ext.lower() if ext.startswith(".") else "." + ext.lower()
    if ext not in MEDIA_TYPES:
        raise ExtractionError("the image must be a PNG, JPEG, WebP or GIF file")
    if not image:
        raise ExtractionError("the image file is empty")
    if len(image) > MAX_IMAGE_BYTES:
        raise ExtractionError("the image is larger than 5 MB; save it smaller and upload again")
    month_key(year, month)
    raw, model = call_claude(image, MEDIA_TYPES[ext], tab)
    body = NORMALIZERS[tab](raw)
    body["en"] = {}
    try:
        add_english(body)
    except ExtractionError as exc:  # the month is still saved, in its original language only
        body["en_error"] = str(exc)
        log(f"{tab} {month_key(year, month)}: English labels not created ({exc})")
    return save(tab, year, month, body, model=model, image=image, ext=ext)


def process_incoming() -> int:
    """Handle factors/incoming/<tab>-<YYYY>-<MM>.<ext>. Returns how many months were written."""
    if not INCOMING.is_dir():
        return 0
    done = _process_moves()
    for path in sorted(INCOMING.iterdir()):
        if not path.is_file() or path.name.startswith("."):
            continue
        m = INCOMING_RE.match(path.name)
        if not m:
            log("ignored (name is not <tab>-<YYYY>-<MM>.<ext>):", path.name)
            continue
        tab, year, month, ext = m.group(1).lower(), int(m.group(2)), int(m.group(3)), "." + m.group(4).lower()
        try:
            doc = extract(tab, year, month, path.read_bytes(), ext)
        except MissingKeyError as exc:
            # keep the upload: it is processed on the next run once the secret exists
            print(f"::warning::Fund key factors: {exc}. {path.name} stays in factors/incoming until the secret is added.")
            return done
        except ExtractionError as exc:
            FAILED.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(FAILED / path.name))
            (FAILED / (path.name + ".error.txt")).write_text(f"{now_iso()}  {exc}\n", encoding="utf-8")
            print(f"::warning::Fund key factors: {path.name} could not be read ({exc}); moved to factors/failed.")
            continue
        path.unlink()
        done += 1
        log(f"{tab} {doc['year']}-{doc['month']:02d}: saved", f"({len(doc.get('warnings') or [])} warning(s))")
    return done


def _process_moves() -> int:
    """Apply factors/incoming/<tab>-<YYYY>-<MM>.move.json (the site's "Change date").

    These run before any new image is read: a date change refers to the data that was on the
    site when it was requested, so an upload committed afterwards for the vacated month must
    land after the move, not be moved by it.
    """
    done = 0
    for path in sorted(INCOMING.iterdir()):
        m = MOVE_RE.match(path.name) if path.is_file() else None
        if not m:
            continue
        tab, key = m.group(1).lower(), m.group(2)
        try:
            request = json.loads(path.read_text(encoding="utf-8"))
            to = re.fullmatch(r"(\d{4})-(\d{2})", str(request.get("to") or ""))
            if not to:
                raise ExtractionError("the request has no target month")
            move_month(tab, key, int(to.group(1)), int(to.group(2)), bool(request.get("replace")))
        except (ValueError, AttributeError, ExtractionError) as exc:
            FAILED.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(FAILED / path.name))
            (FAILED / (path.name + ".error.txt")).write_text(f"{now_iso()}  {exc}\n", encoding="utf-8")
            print(f"::warning::Fund key factors: date change {path.name} was not applied ({exc}); moved to factors/failed.")
            continue
        path.unlink()
        done += 1
        log(f"{tab} {key} -> {to.group(0)}: date changed")
    return done


# ------------------------------------------------------------------ cli
def main() -> int:
    ap = argparse.ArgumentParser(description="Fund key factors: image -> data.")
    ap.add_argument("--apply", action="store_true", help="process factors/incoming/")
    ap.add_argument("--reindex", action="store_true", help="rebuild factors/data/index.json")
    ap.add_argument("--recheck", action="store_true", help="re-run the arithmetic checks on every saved month")
    ap.add_argument("--image", type=Path, help="image to extract (or to keep beside --from-raw data)")
    ap.add_argument("--from-raw", type=Path, help="JSON transcription to normalise instead of calling Claude")
    ap.add_argument("--note", action="append", help="note text for the month (repeatable); replaces its notes")
    ap.add_argument("--explains-warnings", action="store_true", help="with --note: hide the month's warnings")
    ap.add_argument("--translate", action="store_true", help="create English labels for saved months (all, or the one given)")
    ap.add_argument("--force", action="store_true", help="with --translate and a month: translate it again from nothing")
    ap.add_argument("--move-to", metavar="YYYY-MM", help="file the month given by --tab/--year/--month under this date")
    ap.add_argument("--replace", action="store_true", help="with --move-to: overwrite data already at the target month")
    ap.add_argument("--tab", choices=TABS)
    ap.add_argument("--year", type=int)
    ap.add_argument("--month", type=int)
    a = ap.parse_args()

    try:
        if a.apply:
            log("processed", process_incoming(), "upload(s)")
            translate_missing()  # months saved before this feature, or whose translation failed
            rebuild_index()
            return 0
        if a.translate:
            if a.tab and a.year and a.month:
                doc = translate_month(a.tab, month_key(a.year, a.month), a.force)
                log(f"{a.tab} {month_key(a.year, a.month)}: {len(doc.get('en') or {})} English label(s)")
            else:
                log("months updated:", translate_missing())
            return 0
        if a.reindex:
            log("index:", rebuild_index()["tabs"])
            return 0
        if a.recheck:
            for tab in TABS:
                for path in sorted((DATA / tab).glob("*.json")) if (DATA / tab).is_dir() else []:
                    doc = recheck(path)
                    if doc:
                        log(f"{tab} {path.stem}: {len(doc['warnings'])} warning(s), {len(doc.get('auto_notes') or [])} automatic note(s)")
            return 0
        if a.move_to and a.tab and a.year and a.month:
            to = re.fullmatch(r"(\d{4})-(\d{1,2})", a.move_to)
            if not to:
                ap.error("--move-to takes YYYY-MM")
            doc = move_month(a.tab, month_key(a.year, a.month), int(to.group(1)), int(to.group(2)), a.replace)
            log(f"{a.tab} {month_key(a.year, a.month)} -> {doc['year']}-{doc['month']:02d}: date changed")
            return 0
        if a.note is not None and a.tab and a.year and a.month:
            key = month_key(a.year, a.month)
            current = json.loads((DATA / a.tab / (key + ".json")).read_text(encoding="utf-8")) if (DATA / a.tab / (key + ".json")).is_file() else {}
            doc = set_notes(a.tab, key, a.note, (current.get("warnings") or []) if a.explains_warnings else (current.get("dismissed") or []))
            log(f"{a.tab} {key}: {len(doc['notes'])} note(s), {len(doc['dismissed'])} warning(s) explained")
            return 0
        if not (a.tab and a.year and a.month and (a.image or a.from_raw)):
            ap.error("give --apply, --reindex, or --tab/--year/--month with --image, --from-raw or --note")
        if a.from_raw:
            body = NORMALIZERS[a.tab](json.loads(a.from_raw.read_text(encoding="utf-8")))
            image = a.image.read_bytes() if a.image else None
            doc = save(a.tab, a.year, a.month, body, model="manual transcription", image=image, ext=a.image.suffix if a.image else "")
        else:
            doc = extract(a.tab, a.year, a.month, a.image.read_bytes(), a.image.suffix)
    except ExtractionError as exc:
        log("error:", exc)
        return 1
    log(f"{doc['tab']} {doc['year']}-{doc['month']:02d} saved;", len(doc.get("warnings") or []), "warning(s)")
    for w in doc.get("warnings") or []:
        log("  warning:", w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
