"""Static build for GitHub Pages.

  python backend/build_static.py --apply
      * incoming/<id>.<ext>[.enc] + incoming/<id>.meta.json[.enc]  -> data/reports/<id>/ (parsed)
      * ops/*.json[.enc] (update_meta / delete / sectors)          -> applied, then removed
      * every report that has plaintext files gets an up-to-date encrypted copy
      * data/index.json(.enc) rebuilt (all report metadata)

  python backend/build_static.py --site site
      copies web/ + the encrypted data into site/ and writes site/config.js so the
      frontend runs in static mode (reads data/, writes through the GitHub API).

Files per report (data/reports/<id>/):
  meta.json, content.json, images/, source.*   plain files (default: committed and served as-is)
  meta.json.enc, bundle.enc                     only when PANEL_PASSWORD is set (encrypted site)

Default is an open site: no password, everything committed in plain form. Setting the
PANEL_PASSWORD secret switches the whole pipeline to encrypted files (see crypto_util.py).
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

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from crypto_util import decrypt_bytes, derive_key, encrypt_bytes, load_or_create_salt, password_from_env  # noqa: E402
from parsers import parse_report  # noqa: E402

DATA = ROOT / "data"
REPORTS = DATA / "reports"
INCOMING = ROOT / "incoming"
OPS = ROOT / "ops"
WEB = ROOT / "web"
SALT_FILE = DATA / "salt.txt"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(*a):
    print("[build]", *a, flush=True)


class Crypto:
    def __init__(self):
        self.password = password_from_env()
        self.salt = load_or_create_salt(SALT_FILE) if self.password else None
        self.key = derive_key(self.password, self.salt) if self.password else None

    @property
    def on(self) -> bool:
        return self.key is not None

    def read(self, path: Path) -> bytes:
        raw = path.read_bytes()
        if path.suffix == ".enc":
            if not self.on:
                raise RuntimeError(f"{path.name} is encrypted but PANEL_PASSWORD is not set")
            return decrypt_bytes(self.key, raw)
        return raw

    def write_enc(self, path: Path, data: bytes):
        path.write_bytes(encrypt_bytes(self.key, data))


def dump(obj: Any, pretty: bool = False) -> bytes:
    return json.dumps(obj, ensure_ascii=False, indent=2 if pretty else None).encode("utf-8")


# ------------------------------------------------------------------ reports
def read_meta(d: Path, c: Crypto) -> dict[str, Any] | None:
    for name in ("meta.json", "meta.json.enc"):
        f = d / name
        if f.exists():
            try:
                return json.loads(c.read(f))
            except Exception as e:
                log("cannot read", f, e)
    return None


def all_meta(c: Crypto) -> list[dict[str, Any]]:
    out = []
    if REPORTS.exists():
        for d in sorted(REPORTS.iterdir()):
            if d.is_dir():
                m = read_meta(d, c)
                if m:
                    out.append(m)
    out.sort(key=lambda m: (m.get("period_key", 0), m.get("uploaded_at", "")), reverse=True)
    for m in out:  # tell the site whether the original file is available for download
        d = REPORTS / m["id"]
        src = next((p.name for p in d.iterdir() if p.name.startswith("source.")), None) if d.exists() else None
        m["source_file"] = src
    return out


def fill_meta_from_parsed(meta: dict[str, Any], parsed: dict[str, Any]):
    if not meta.get("title"):
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


def write_plain(d: Path, meta: dict[str, Any], content: dict[str, Any] | None):
    d.mkdir(parents=True, exist_ok=True)
    (d / "meta.json").write_bytes(dump(meta, pretty=True))
    if content is not None:
        (d / "content.json").write_bytes(dump(content))


def write_encrypted(d: Path, meta: dict[str, Any], c: Crypto):
    """Build meta.json.enc and bundle.enc from the plaintext files in d."""
    content_f = d / "content.json"
    bundle_f = d / "bundle.enc"
    if content_f.exists():
        content = json.loads(content_f.read_bytes())
        images = {}
        img_dir = d / "images"
        if img_dir.exists():
            for f in sorted(img_dir.iterdir()):
                images[f.name] = base64.b64encode(f.read_bytes()).decode("ascii")
        bundle = {"meta": meta, "content": content, "images": images}
    elif bundle_f.exists():
        bundle = json.loads(c.read(bundle_f))
        bundle["meta"] = meta
    else:
        log("no content for", d.name)
        return
    c.write_enc(bundle_f, dump(bundle))
    c.write_enc(d / "meta.json.enc", dump(meta))


def save_report(d: Path, meta: dict[str, Any], content: dict[str, Any] | None, c: Crypto):
    """content=None means metadata-only update."""
    has_plain = (d / "content.json").exists() or content is not None
    if has_plain:
        write_plain(d, meta, content)
    elif not c.on:
        raise RuntimeError(f"{d.name}: only encrypted files exist and PANEL_PASSWORD is not set")
    if c.on:
        write_encrypted(d, meta, c)


def sync_encrypted(c: Crypto) -> int:
    """Refresh the encrypted copy of every report that has plaintext (local edits, first publish)."""
    if not c.on or not REPORTS.exists():
        return 0
    n = 0
    for d in sorted(REPORTS.iterdir()):
        if d.is_dir() and (d / "meta.json").exists():
            meta = json.loads((d / "meta.json").read_bytes())
            write_encrypted(d, meta, c)
            n += 1
    return n


def period_label(y: int, q: int) -> str:
    return f"{q}Q{y}"


# ------------------------------------------------------------------ incoming
def process_incoming(c: Crypto) -> int:
    if not INCOMING.exists():
        return 0
    done = 0
    files = sorted(p for p in INCOMING.iterdir() if p.is_file() and not p.name.startswith("."))
    sidecars = {p.name.split(".")[0]: p for p in files if ".meta.json" in p.name}
    for p in files:
        if ".meta.json" in p.name:
            continue
        uid = p.name.split(".")[0]
        mp = sidecars.get(uid)
        if not mp:
            log("skip (no sidecar yet):", p.name)
            continue
        try:
            meta_in = json.loads(c.read(mp))
            raw = c.read(p)
        except Exception as e:
            log("cannot read incoming", p.name, e)
            continue
        parts = [x for x in p.name.split(".")[1:] if x != "enc"]
        ext = "." + (parts[-1].lower() if parts else "docx")
        sector = meta_in.get("sector") or "unsorted"
        year = int(meta_in.get("year") or datetime.now().year)
        quarter = int(meta_in.get("quarter") or (datetime.now().month - 1) // 3 + 1)
        nature = meta_in.get("nature") if meta_in.get("nature") in ("full", "summary") else "full"
        rid = f"{sector}-{year}Q{quarter}-{nature}-{uid[:8]}"
        d = REPORTS / rid
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
        src = d / f"source{ext}"
        src.write_bytes(raw)
        try:
            parsed = parse_report(src, d / "images")
        except Exception as e:
            log("PARSE FAILED", p.name, e)
            shutil.rmtree(d, ignore_errors=True)
            continue
        meta = {
            "id": rid, "title": (meta_in.get("title") or "").strip(), "sector": sector, "year": year, "quarter": quarter,
            "period": period_label(year, quarter), "period_key": year * 10 + quarter, "nature": nature,
            "language": meta_in.get("language") if meta_in.get("language") in ("en", "cn") else "",
            "keywords": [k.strip() for k in re.split(r"[,，;；]", meta_in.get("keywords") or "") if k.strip()],
            "source_name": meta_in.get("source_name") or p.name.replace(".enc", ""), "source_ext": ext,
            "uploaded_at": meta_in.get("uploaded_at") or now_iso(),
        }
        fill_meta_from_parsed(meta, parsed)
        content = {"blocks": parsed["blocks"], "exhibits": parsed["exhibits"], "stats": parsed["stats"]}
        save_report(d, meta, content, c)
        p.unlink()
        mp.unlink()
        done += 1
        log("parsed", p.name, "->", rid, parsed["stats"])
    return done


# ------------------------------------------------------------------ ops
def load_sectors() -> list[dict[str, Any]]:
    f = DATA / "sectors.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []


def apply_ops(c: Crypto) -> int:
    if not OPS.exists():
        return 0
    n = 0
    for p in sorted(x for x in OPS.iterdir() if x.is_file() and not x.name.startswith(".")):
        try:
            op = json.loads(c.read(p))
        except Exception as e:
            log("cannot read op", p.name, e)
            continue
        kind = op.get("op")
        try:
            if kind == "update_meta":
                d = REPORTS / op["id"]
                meta = read_meta(d, c)
                if meta:
                    for k in ("title", "nature", "language", "sector"):
                        if op.get(k):
                            meta[k] = op[k]
                    if "keywords" in op:
                        kws = op["keywords"]
                        meta["keywords"] = [k.strip() for k in re.split(r"[,，;；]", kws) if k.strip()] if isinstance(kws, str) else kws
                    if op.get("year") and op.get("quarter"):
                        y, q = int(op["year"]), int(op["quarter"])
                        meta.update(year=y, quarter=q, period=period_label(y, q), period_key=y * 10 + q)
                    meta["updated_at"] = now_iso()
                    save_report(d, meta, None, c)
            elif kind == "delete":
                shutil.rmtree(REPORTS / op["id"], ignore_errors=True)
            elif kind == "sectors":
                (DATA / "sectors.json").write_bytes(dump(op["sectors"], pretty=True))
            else:
                log("unknown op", kind)
        except Exception as e:
            log("op failed", p.name, e)
            continue
        p.unlink()
        n += 1
        log("applied", kind, op.get("id", ""))
    return n


# ------------------------------------------------------------------ index + site
def build_index(c: Crypto):
    metas = all_meta(c)
    y = datetime.now().year
    index = {
        "generated": now_iso(),
        "sectors": load_sectors(),
        "reports": metas,
        "meta": {"current_year": y, "current_quarter": (datetime.now().month - 1) // 3 + 1,
                 "years": sorted({m["year"] for m in metas} | {y}, reverse=True), "report_count": len(metas), "auth": c.on},
    }
    for old in (DATA / "index.json", DATA / "index.json.enc"):
        if old.exists():
            old.unlink()
    if c.on:
        c.write_enc(DATA / "index.json.enc", dump(index))
    else:
        (DATA / "index.json").write_bytes(dump(index))
    log("index:", len(metas), "reports", "(encrypted)" if c.on else "(plain)")


def strip_plaintext():
    """Encrypted mode in CI: keep only the encrypted copies in the repository."""
    if not REPORTS.exists():
        return
    for d in REPORTS.iterdir():
        if not d.is_dir():
            continue
        for f in list(d.iterdir()):
            if f.is_dir():
                shutil.rmtree(f, ignore_errors=True)
            elif not f.name.endswith(".enc"):
                f.unlink()
    for f in (DATA / "index.json",):
        if f.exists():
            f.unlink()


def build_site(out: Path, c: Crypto, repo: str, branch: str):
    shutil.rmtree(out, ignore_errors=True)
    shutil.copytree(WEB, out, ignore=shutil.ignore_patterns("config.js", "login.html"))
    (out / "data").mkdir()
    for name in ("sectors.json", "salt.txt", "index.json", "index.json.enc"):
        f = DATA / name
        if f.exists():
            shutil.copy(f, out / "data" / name)
    if REPORTS.exists():
        for d in REPORTS.iterdir():
            if not d.is_dir():
                continue
            dst = out / "data" / "reports" / d.name
            if c.on:
                if (d / "bundle.enc").exists():
                    dst.mkdir(parents=True)
                    shutil.copy(d / "bundle.enc", dst / "bundle.enc")
            else:
                dst.mkdir(parents=True)
                for f in d.iterdir():
                    if f.name in ("meta.json", "content.json") or f.name.startswith("source."):
                        shutil.copy(f, dst / f.name)
                if (d / "images").exists():
                    shutil.copytree(d / "images", dst / "images")
    cfg = {"static": True, "encrypted": c.on, "repo": repo, "branch": branch, "built": now_iso()}
    (out / "config.js").write_text("window.AID_CONFIG = " + json.dumps(cfg) + ";\n", encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    log("site written to", out, cfg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="process incoming/ and ops/, refresh encrypted copies, rebuild the index")
    ap.add_argument("--site", metavar="DIR", help="write the static site into DIR")
    ap.add_argument("--strip-plain", action="store_true", help="encrypted mode: remove plaintext copies after building (used in CI)")
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    ap.add_argument("--branch", default=os.environ.get("GITHUB_REF_NAME", "main"))
    a = ap.parse_args()
    c = Crypto()
    log("encryption:", "on" if c.on else "off (open site, PANEL_PASSWORD not set)")
    if a.apply:
        n1 = process_incoming(c)
        n2 = apply_ops(c)
        n3 = sync_encrypted(c)
        build_index(c)
        if c.on and a.strip_plain:
            strip_plaintext()
        log(f"applied {n1} uploads, {n2} ops; refreshed {n3} encrypted reports")
    if a.site:
        if not (DATA / "index.json").exists() and not (DATA / "index.json.enc").exists():
            build_index(c)
        build_site(Path(a.site), c, a.repo, a.branch)


if __name__ == "__main__":
    main()
