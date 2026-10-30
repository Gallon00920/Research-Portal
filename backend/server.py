"""AID Research Panel — API + static file server.

Run:  python backend/server.py   (or run.bat)
Then open http://127.0.0.1:8765

No database: every report lives in data/reports/<id>/ as
  meta.json      card metadata (title, sector, quarter, keywords, ...)
  content.json   parsed blocks + exhibit index
  images/        extracted figures
  source.<ext>   the uploaded file, kept so the report can be re-parsed
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import shutil
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from parsers import parse_report  # noqa: E402

DATA = ROOT / "data"
REPORTS = DATA / "reports"
SECTORS_FILE = DATA / "sectors.json"
WEB = ROOT / "web"
REPORTS.mkdir(parents=True, exist_ok=True)

DEFAULT_SECTORS = [
    {"id": "private_credit", "code": "PC", "name_en": "Private Credit", "name_cn": "私募信贷", "region": "North America",
     "coverage_en": ["Private credit", "Direct lending", "BDC", "MM CLO"], "coverage_cn": ["私募信贷", "直接贷款", "商业发展公司 BDC", "中型市场贷款抵押债券 MM CLO"], "status": "active"},
    {"id": "software_otf", "code": "SW", "name_en": "Software & OTF", "name_cn": "软件与科技融资", "region": "Global",
     "coverage_en": ["Software", "Technology lending", "OTF / BDC"], "coverage_cn": ["软件", "科技贷款", "OTF / BDC"], "status": "active"},
    {"id": "infrastructure", "code": "INF", "name_en": "Infrastructure", "name_cn": "基础设施", "region": "Global",
     "coverage_en": ["Infrastructure debt", "Energy transition", "Digital infra"], "coverage_cn": ["基础设施债务", "能源转型", "数字基础设施"], "status": "active"},
    {"id": "aviation", "code": "AVI", "name_en": "Aviation", "name_cn": "航空", "region": "Global",
     "coverage_en": ["Aircraft leasing", "Aviation finance", "Aerospace"], "coverage_cn": ["飞机租赁", "航空金融", "航空航天"], "status": "active"},
]

app = FastAPI(title="AID Research Panel")

# ------------------------------------------------------------------- login
# Set PANEL_PASSWORD to require a shared password (recommended for any public URL).
# Without it the site is open, which is fine on a laptop at http://127.0.0.1.
PANEL_PASSWORD = os.environ.get("PANEL_PASSWORD", "").strip()
SECRET_KEY = os.environ.get("SECRET_KEY", "").strip() or hashlib.sha256(("aid-panel:" + PANEL_PASSWORD).encode()).hexdigest()
SESSION_COOKIE = "aid_session"
SESSION_DAYS = 30
PUBLIC_PATHS = {"/login.html", "/api/login", "/api/health"}


def auth_enabled() -> bool:
    return bool(PANEL_PASSWORD)


def make_token() -> str:
    exp = str(int(time.time()) + SESSION_DAYS * 86400)
    sig = hmac.new(SECRET_KEY.encode(), ("ok:" + exp).encode(), hashlib.sha256).hexdigest()
    return exp + "." + sig


def token_ok(token: str | None) -> bool:
    if not token or "." not in token:
        return False
    exp, sig = token.split(".", 1)
    if not exp.isdigit() or int(exp) < time.time():
        return False
    good = hmac.new(SECRET_KEY.encode(), ("ok:" + exp).encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(good, sig)


def is_https(request: Request) -> bool:
    return request.url.scheme == "https" or request.headers.get("x-forwarded-proto", "").lower() == "https"


@app.middleware("http")
async def require_login(request: Request, call_next):
    if not auth_enabled():
        return await call_next(request)
    path = request.url.path
    if path in PUBLIC_PATHS or token_ok(request.cookies.get(SESSION_COOKIE)):
        return await call_next(request)
    if path.startswith("/api/"):
        return JSONResponse({"error": "login required"}, status_code=401)
    if path.endswith((".css", ".js", ".png", ".ico", ".svg")):
        return await call_next(request)
    return RedirectResponse("/login.html", status_code=302)


@app.post("/api/login")
async def api_login(request: Request, payload: dict[str, Any]):
    if not auth_enabled():
        return {"ok": True}
    given = str(payload.get("password", ""))
    if not hmac.compare_digest(given.encode(), PANEL_PASSWORD.encode()):
        time.sleep(0.8)  # slow down guessing
        raise HTTPException(401, "wrong password")
    resp = JSONResponse({"ok": True})
    resp.set_cookie(SESSION_COOKIE, make_token(), max_age=SESSION_DAYS * 86400, httponly=True, samesite="lax", secure=is_https(request))
    return resp


@app.post("/api/logout")
def api_logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(SESSION_COOKIE)
    return resp


@app.get("/api/health")
def api_health():
    return {"ok": True, "auth": auth_enabled()}


# ----------------------------------------------------------------- utilities
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def current_quarter() -> tuple[int, int]:
    d = datetime.now()
    return d.year, (d.month - 1) // 3 + 1


def period_label(year: int, quarter: int) -> str:
    return f"{quarter}Q{year}"


def period_key(year: int, quarter: int) -> int:
    return year * 10 + quarter


def load_sectors() -> list[dict[str, Any]]:
    if not SECTORS_FILE.exists():
        SECTORS_FILE.write_text(json.dumps(DEFAULT_SECTORS, ensure_ascii=False, indent=2), encoding="utf-8")
    return json.loads(SECTORS_FILE.read_text(encoding="utf-8"))


def save_sectors(sectors: list[dict[str, Any]]):
    SECTORS_FILE.write_text(json.dumps(sectors, ensure_ascii=False, indent=2), encoding="utf-8")


def read_meta(d: Path) -> dict[str, Any] | None:
    f = d / "meta.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return None


def all_meta() -> list[dict[str, Any]]:
    out = []
    for d in REPORTS.iterdir():
        if d.is_dir():
            m = read_meta(d)
            if m:
                out.append(m)
    out.sort(key=lambda m: (m.get("period_key", 0), m.get("uploaded_at", "")), reverse=True)
    return out


def report_dir(rid: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9_\-]+", rid):
        raise HTTPException(400, "bad id")
    d = REPORTS / rid
    if not d.is_dir():
        raise HTTPException(404, "report not found")
    return d


def parse_period(s: str | None) -> int | None:
    """Accept '2Q2026', '2026Q2', '2026-2' -> 20262."""
    if not s:
        return None
    m = re.fullmatch(r"\s*(\d)Q(\d{4})\s*", s, re.I) or re.fullmatch(r"\s*(\d{4})Q(\d)\s*", s, re.I)
    if m:
        a, b = m.groups()
        year, q = (int(b), int(a)) if len(a) == 1 else (int(a), int(b))
        return period_key(year, q)
    m = re.fullmatch(r"\s*(\d{4})[-/](\d)\s*", s)
    if m:
        return period_key(int(m.group(1)), int(m.group(2)))
    raise HTTPException(400, f"bad period: {s}")


# ------------------------------------------------------------------- sectors
@app.get("/api/sectors")
def api_sectors():
    sectors = load_sectors()
    metas = all_meta()
    for s in sectors:
        mine = [m for m in metas if m.get("sector") == s["id"]]
        s["report_count"] = len(mine)
        s["latest_period"] = mine[0]["period"] if mine else None
        s["latest_period_key"] = mine[0]["period_key"] if mine else None
        s["periods"] = sorted({m["period"] for m in mine}, key=lambda p: parse_period(p), reverse=True)
        s["languages"] = sorted({m["language"] for m in mine})
        s["natures"] = sorted({m["nature"] for m in mine})
    return sectors


@app.post("/api/sectors")
def api_add_sector(payload: dict[str, Any]):
    sectors = load_sectors()
    name_en = (payload.get("name_en") or "").strip()
    if not name_en:
        raise HTTPException(400, "name_en required")
    sid = re.sub(r"[^a-z0-9]+", "_", name_en.lower()).strip("_") or f"sector_{uuid.uuid4().hex[:6]}"
    if any(s["id"] == sid for s in sectors):
        raise HTTPException(409, "sector exists")
    code = (payload.get("code") or "".join(w[0] for w in name_en.split()[:3])).upper()[:4]
    sectors.append({
        "id": sid, "code": code, "name_en": name_en, "name_cn": (payload.get("name_cn") or name_en).strip(),
        "region": payload.get("region") or "Global",
        "coverage_en": payload.get("coverage_en") or [], "coverage_cn": payload.get("coverage_cn") or [],
        "status": payload.get("status") or "active",
    })
    save_sectors(sectors)
    return sectors[-1]


@app.put("/api/sectors-order")
def api_order_sectors(payload: dict[str, Any]):
    """Reorder sectors: payload {"order": [sector ids in the desired order]}."""
    sectors = load_sectors()
    order = [x for x in payload.get("order", []) if isinstance(x, str)]
    by_id = {s["id"]: s for s in sectors}
    if set(order) != set(by_id):
        raise HTTPException(400, "order must list every sector id exactly once")
    new = [by_id[i] for i in order]
    save_sectors(new)
    return new


@app.put("/api/sectors/{sid}")
def api_update_sector(sid: str, payload: dict[str, Any]):
    sectors = load_sectors()
    for s in sectors:
        if s["id"] == sid:
            if "name_en" in payload and not (payload["name_en"] or "").strip():
                raise HTTPException(400, "name_en required")
            for k in ("code", "name_en", "name_cn", "region", "coverage_en", "coverage_cn", "status"):
                if k in payload and payload[k] is not None:
                    s[k] = payload[k]
            save_sectors(sectors)
            return s
    raise HTTPException(404, "sector not found")


@app.delete("/api/sectors/{sid}")
def api_delete_sector(sid: str):
    sectors = load_sectors()
    if any(m.get("sector") == sid for m in all_meta()):
        raise HTTPException(409, "sector still has reports")
    new = [s for s in sectors if s["id"] != sid]
    if len(new) == len(sectors):
        raise HTTPException(404, "sector not found")
    save_sectors(new)
    return {"ok": True}


# ------------------------------------------------------------------- reports
@app.get("/api/reports")
def api_reports(sector: str | None = None, year: int | None = None, quarter: int | None = None,
                nature: str | None = None, language: str | None = None,
                period_from: str | None = None, period_to: str | None = None, q: str | None = None,
                limit: int | None = None):
    metas = all_meta()
    pf, pt = parse_period(period_from), parse_period(period_to)
    out = []
    for m in metas:
        if sector and m.get("sector") != sector:
            continue
        if year and m.get("year") != year:
            continue
        if quarter and m.get("quarter") != quarter:
            continue
        if nature and m.get("nature") != nature:
            continue
        if language and m.get("language") != language:
            continue
        if pf and m.get("period_key", 0) < pf:
            continue
        if pt and m.get("period_key", 0) > pt:
            continue
        if q:
            hay = " ".join([m.get("title", ""), " ".join(m.get("keywords", [])), m.get("source_name", "")]).lower()
            if q.lower() not in hay:
                continue
        out.append(m)
    if limit:
        out = out[:limit]
    return out


@app.get("/api/reports/recent")
def api_recent(limit: int = 6, language: str | None = None, nature: str | None = None):
    metas = all_meta()
    if language:
        metas = [m for m in metas if m.get("language") == language]
    if nature:
        metas = [m for m in metas if m.get("nature") == nature]
    metas.sort(key=lambda m: m.get("uploaded_at", ""), reverse=True)
    return metas[:limit]


@app.get("/api/reports/{rid}")
def api_report(rid: str):
    d = report_dir(rid)
    meta = read_meta(d)
    content = json.loads((d / "content.json").read_text(encoding="utf-8"))
    return {"meta": meta, "content": content}


@app.put("/api/reports/{rid}")
def api_update_report(rid: str, payload: dict[str, Any]):
    d = report_dir(rid)
    meta = read_meta(d) or {}
    for k in ("title", "nature", "language", "sector"):
        if k in payload and payload[k]:
            meta[k] = payload[k]
    if "keywords" in payload:
        kws = payload["keywords"]
        if isinstance(kws, str):
            kws = [k.strip() for k in re.split(r"[,，;；]", kws) if k.strip()]
        meta["keywords"] = kws
    if "year" in payload and "quarter" in payload:
        y, qq = int(payload["year"]), int(payload["quarter"])
        if not (1 <= qq <= 4):
            raise HTTPException(400, "quarter must be 1-4")
        meta.update(year=y, quarter=qq, period=period_label(y, qq), period_key=period_key(y, qq))
    meta["updated_at"] = now_iso()
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


@app.delete("/api/reports/{rid}")
def api_delete_report(rid: str):
    d = report_dir(rid)
    shutil.rmtree(d)
    return {"ok": True}


@app.post("/api/reports/{rid}/reparse")
def api_reparse(rid: str):
    d = report_dir(rid)
    meta = read_meta(d) or {}
    src = next((p for p in d.iterdir() if p.name.startswith("source.")), None)
    if not src:
        raise HTTPException(404, "source file missing")
    img_dir = d / "images"
    shutil.rmtree(img_dir, ignore_errors=True)
    parsed = parse_report(src, img_dir)
    _write_content(d, meta, parsed, keep_title=True)
    return read_meta(d)


@app.get("/api/reports/{rid}/images/{name}")
def api_image(rid: str, name: str):
    d = report_dir(rid)
    if not re.fullmatch(r"[A-Za-z0-9_.\-]+", name):
        raise HTTPException(400, "bad name")
    f = d / "images" / name
    if not f.exists():
        raise HTTPException(404, "image not found")
    return FileResponse(f)


@app.get("/api/reports/{rid}/source")
def api_source(rid: str):
    d = report_dir(rid)
    meta = read_meta(d) or {}
    src = next((p for p in d.iterdir() if p.name.startswith("source.")), None)
    if not src:
        raise HTTPException(404, "source file missing")
    return FileResponse(src, filename=meta.get("source_name") or src.name)


def _write_content(d: Path, meta: dict[str, Any], parsed: dict[str, Any], keep_title: bool = False):
    content = {"blocks": parsed["blocks"], "exhibits": parsed["exhibits"], "stats": parsed["stats"]}
    (d / "content.json").write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
    if not keep_title or not meta.get("title"):
        meta["title"] = parsed["title"]
    if not meta.get("keywords"):
        meta["keywords"] = parsed["keywords"]
    if not meta.get("language"):
        meta["language"] = parsed["language"]
    meta["stats"] = parsed["stats"]
    meta["exhibit_count"] = len(parsed["exhibits"])
    for k in ("subtitle", "masthead", "coverage", "publish_date"):
        if parsed.get(k):
            meta[k] = parsed[k]
    meta["toc"] = [{"level": b["level"], "text": b["text"]} for b in parsed["blocks"] if b["type"] == "heading"][:60]
    first = next((b["text"] for b in parsed["blocks"] if b["type"] == "paragraph" and len(b.get("text", "")) > 60), "")
    meta["summary"] = first[:220]
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...), sector: str = Form(...), year: int | None = Form(None),
                     quarter: int | None = Form(None), nature: str = Form("full"), language: str = Form(""),
                     title: str = Form(""), keywords: str = Form("")):
    sectors = load_sectors()
    if not any(s["id"] == sector for s in sectors):
        raise HTTPException(400, "unknown sector")
    cy, cq = current_quarter()
    year = year or cy
    quarter = quarter or cq
    if not (1 <= quarter <= 4):
        raise HTTPException(400, "quarter must be 1-4")
    if nature not in ("full", "summary"):
        raise HTTPException(400, "nature must be full or summary")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in (".docx", ".pdf"):
        raise HTTPException(400, "Only .docx and .pdf reports are supported")

    rid = f"{sector}-{year}Q{quarter}-{nature}-{uuid.uuid4().hex[:8]}"
    d = REPORTS / rid
    d.mkdir(parents=True)
    src = d / f"source{ext}"
    with src.open("wb") as fh:
        shutil.copyfileobj(file.file, fh)
    try:
        parsed = parse_report(src, d / "images")
    except Exception as e:  # keep the data folder clean on failure
        shutil.rmtree(d, ignore_errors=True)
        raise HTTPException(422, f"Could not parse report: {e}")

    kws = [k.strip() for k in re.split(r"[,，;；]", keywords) if k.strip()]
    meta = {
        "id": rid,
        "title": title.strip(),
        "sector": sector,
        "year": year,
        "quarter": quarter,
        "period": period_label(year, quarter),
        "period_key": period_key(year, quarter),
        "nature": nature,
        "language": language if language in ("en", "cn") else "",
        "keywords": kws,
        "source_name": file.filename,
        "source_ext": ext,
        "uploaded_at": now_iso(),
    }
    _write_content(d, meta, parsed, keep_title=bool(meta["title"]))
    return read_meta(d)


@app.get("/api/meta")
def api_meta():
    y, q = current_quarter()
    metas = all_meta()
    years = sorted({m["year"] for m in metas} | {y}, reverse=True)
    return {"current_year": y, "current_quarter": q, "years": years, "report_count": len(metas), "auth": auth_enabled()}


# -------------------------------------------------------------------- static
@app.exception_handler(HTTPException)
async def http_exc(_, exc: HTTPException):
    return JSONResponse({"error": exc.detail}, status_code=exc.status_code)


@app.middleware("http")
async def no_cache_static(request, call_next):
    """Frontend files change between versions; make browsers revalidate them."""
    response = await call_next(request)
    if not request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


app.mount("/", StaticFiles(directory=str(WEB), html=True), name="web")


if __name__ == "__main__":
    import uvicorn

    if not auth_enabled():
        print("PANEL_PASSWORD is not set: the panel is open to anyone who can reach it (fine for local use).")
    uvicorn.run("server:app", host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "8765")), reload=False, app_dir=str(ROOT / "backend"))
