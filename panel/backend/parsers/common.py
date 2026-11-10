"""Helpers shared by the docx and pdf parsers."""
from __future__ import annotations

import re
from collections import Counter
from typing import Any

CAPTION_RE = re.compile(
    r"^\s*(?:(?:exhibit|figure|fig\.?|chart|table|graph)\s*\d+[A-Za-z]?|(?:图表|图|表|附图|附表)\s*\d+)\s*[:：.．\-—–]?\s*",
    re.I,
)
CAPTION_KIND_RE = re.compile(r"^\s*(exhibit|figure|fig\.?|chart|graph|table|图表|图|表|附图|附表)", re.I)
STOP = set(
    """a an and are as at be by for from has have in is it its of on or that the this to was were will with
    we our not but than more less over under into out up down about after before between during through
    per vs via each all any some such these those also been being can could may might should would
    year years quarter quarters q1 q2 q3 q4 1q 2q 3q 4q bn mn m k usd eur gbp jpy cny rmb hk
    source sources note notes exhibit figure table chart qoq yoy ttm ytd""".split()
)


def is_caption(text: str) -> bool:
    return bool(text) and len(text) <= 220 and bool(CAPTION_RE.match(text))


def strip_caption_label(text: str) -> str:
    return CAPTION_RE.sub("", text, count=1).strip()


CAPTION_LABEL_RE = re.compile(r"^\s*((?:exhibit|figure|fig\.?|chart|table|graph)\s*\d+[A-Za-z]?|(?:图表|图|表|附图|附表)\s*\d+)", re.I)


def caption_label(text: str) -> str:
    """The document's own exhibit label ("Exhibit 12", "图3"), or '' if the caption has none."""
    m = CAPTION_LABEL_RE.match(text or "")
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def caption_kind(text: str) -> str:
    m = CAPTION_KIND_RE.match(text or "")
    if not m:
        return "figure"
    w = m.group(1).lower()
    return "table" if w in ("table", "表", "附表") else "figure"


def guess_language(text: str) -> str:
    cjk = len(re.findall(r"[一-鿿]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    return "cn" if cjk > latin * 0.3 else "en"


def attach_captions(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach caption-like paragraphs to the neighbouring image/table block."""
    out: list[dict[str, Any]] = []
    i = 0
    n = len(blocks)
    while i < n:
        b = blocks[i]
        if b["type"] in ("image", "table") and not b.get("caption"):
            # caption before
            if out and out[-1]["type"] == "paragraph" and out[-1].get("style") == "caption":
                cap = out.pop()
                b["caption"] = cap["text"]
            # caption after (skip over sibling images in a row)
            elif i + 1 < n and blocks[i + 1]["type"] == "paragraph" and blocks[i + 1].get("style") == "caption":
                b["caption"] = blocks[i + 1]["text"]
                i += 1  # consume caption
            # note after
            if i + 1 < n and blocks[i + 1]["type"] == "paragraph" and blocks[i + 1].get("style") == "note":
                b["note"] = blocks[i + 1]["text"]
                i += 1
        out.append(b)
        i += 1
    return out


def build_exhibits(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Number every image/table (depth-first, document order) and return the exhibit index.

    An exhibit without its own caption borrows the nearest preceding heading so the
    index never shows a blank entry.
    """
    exhibits: list[dict[str, Any]] = []
    counter = {"n": 0, "heading": ""}

    def visit(items: list[dict[str, Any]]):
        for b in items:
            if b["type"] == "heading":
                counter["heading"] = b["text"]
                continue
            if b["type"] == "layout":
                for cell in b["cells"]:
                    visit(cell)
                continue
            if b["type"] not in ("image", "table"):
                continue
            counter["n"] += 1
            n = counter["n"]
            b["exhibit"] = n
            b["anchor"] = f"ex-{n}"
            cap = b.get("caption") or ""
            kind = "table" if b["type"] == "table" else "figure"
            if cap and CAPTION_KIND_RE.match(cap):
                kind = caption_kind(cap)
            exhibits.append(
                {
                    "n": n,
                    "kind": kind,
                    "type": b["type"],
                    "caption": strip_caption_label(cap) if cap else counter["heading"],
                    "derived": not cap,
                    "label": caption_label(cap),
                    "anchor": b["anchor"],
                    "src": b.get("src"),
                }
            )

    visit(blocks)
    return exhibits


def keywords_from_coverage(coverage: str, limit: int = 8) -> list[str]:
    parts = re.split(r"\s*[/／、,，;；|]\s*", coverage)
    out = []
    for p in parts:
        p = p.strip(" .。")
        if p and p not in out:
            out.append(p)
    return out[:limit]


CN_STOP = {"季度", "美元", "亿美", "亿美元", "万亿", "百分", "一季度", "二季度", "三季度", "四季度", "年一季", "年二季", "年三季", "年四季",
           "个基点", "基点", "我们", "本季", "上季", "同比", "环比", "其中", "以及", "由于", "但是", "对于", "可以", "进一步", "资料来源", "来源",
           "数据", "数值", "图表", "近似", "显示", "继续", "仍然", "截至", "月份", "年份", "方面", "整体", "分别", "约为", "左右", "上升", "下降"}


def auto_keywords(text: str, language: str, limit: int = 6) -> list[str]:
    """Cheap keyword extraction so a card never shows an empty keyword row."""
    if language == "cn":
        # frequent 2-4 character runs of CJK, longest-first dedupe
        grams: Counter[str] = Counter()
        for run in re.findall(r"[一-鿿]{2,}", text):
            for size in (4, 3, 2):
                for j in range(0, len(run) - size + 1):
                    grams[run[j : j + size]] += 1
        picked: list[str] = []
        for g, c in grams.most_common(400):
            if c < 3:
                break
            if g in CN_STOP or any(s in g for s in ("季度", "美元", "基点", "来源", "数据", "我们")):
                continue
            if any(g in p or p in g for p in picked):
                continue
            picked.append(g)
            if len(picked) >= limit:
                break
        return picked
    phrases: Counter[str] = Counter()
    for m in re.finditer(r"\b([A-Z][A-Za-z&-]+(?:\s+[A-Z][A-Za-z&-]+){0,3})\b", text):
        p = m.group(1).strip()
        if p.lower() in STOP or len(p) < 3:
            continue
        phrases[p] += 1
    picked = []
    for p, c in phrases.most_common(100):
        if c < 2:
            break
        if any(p.lower() in q.lower() or q.lower() in p.lower() for q in picked):
            continue
        picked.append(p)
        if len(picked) >= limit:
            break
    return picked
