"""Unpack the compressed files dropped into AI generation: .zip, .7z, .rar, .tar (also .tar.gz /
.tgz, .tar.bz2, .tar.xz) and single compressed files (.gz, .bz2, .xz), including archives inside
archives, to any depth up to MAX_DEPTH.

expand(paths, dest, keep) returns (kept files, notes): every file found whose extension is in
`keep`, written under `dest` with its own name (a clash gets the name of the folder it came from,
then a number), and one-line notes on what was unpacked and what was left out.

Safety: nothing is written outside `dest` (entries with absolute paths or "..", links and devices
are ignored), and the total unpacked size and file count are capped, so an archive bomb stops
with an error instead of filling the disk. Password-protected archives are reported, not guessed.
.7z is read with the py7zr package, and .rar with the rarfile package (plus an unrar tool); without
them both are read with the 7-Zip program when the server has one (7z / 7zz / 7za on the PATH, or
the 7-Zip folder under Program Files on Windows). Without any of these those archives are reported
with what to do.
"""
from __future__ import annotations

import bz2
import gzip
import lzma
import os
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

MAX_DEPTH = 6                    # archives inside archives inside ...
MAX_TOTAL_BYTES = 1024 ** 3      # 1 GB unpacked in all
MAX_FILES = 2000                 # files unpacked in all
JUNK_NAMES = {".ds_store", "thumbs.db", "desktop.ini"}
JUNK_DIRS = {"__macosx"}

TAR_SUFFIXES = (".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz", ".tbz2", ".tar.xz", ".txz")
SINGLE_SUFFIXES = {".gz": gzip.open, ".bz2": bz2.open, ".xz": lzma.open}
ARCHIVE_SUFFIXES = (".zip", ".7z", ".rar") + TAR_SUFFIXES + tuple(SINGLE_SUFFIXES)


class ArchiveError(Exception):
    pass


def archive_kind(name: str) -> str:
    """'zip', '7z', 'rar', 'tar', 'single' or '' for a file name."""
    n = name.lower()
    if n.endswith(".zip"):
        return "zip"
    if n.endswith(".7z"):
        return "7z"
    if n.endswith(".rar"):
        return "rar"
    if n.endswith(TAR_SUFFIXES):
        return "tar"
    if n.endswith(tuple(SINGLE_SUFFIXES)):
        return "single"
    return ""


def is_archive(name: str) -> bool:
    return bool(archive_kind(name))


class _Budget:
    def __init__(self):
        self.bytes = 0
        self.files = 0

    def take(self, size: int, what: str):
        self.bytes += max(0, size)
        self.files += 1
        if self.bytes > MAX_TOTAL_BYTES:
            raise ArchiveError(f"the archives unpack to more than {MAX_TOTAL_BYTES // 1024 ** 2} MB ({what}); split them up")
        if self.files > MAX_FILES:
            raise ArchiveError(f"the archives hold more than {MAX_FILES} files ({what}); split them up")


def expand(paths: list[Path], dest: Path, keep: set[str]) -> tuple[list[Path], list[str]]:
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    kept: list[Path] = []
    notes: list[str] = []
    budget = _Budget()
    work = dest / ".work"
    try:
        for p in paths:
            p = Path(p)
            if is_archive(p.name):
                _unpack(p, p.name, dest, work, keep, kept, notes, budget, depth=1)
            else:
                kept.append(p)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return kept, notes


# ------------------------------------------------------------------ one archive
def _unpack(path: Path, label: str, dest: Path, work: Path, keep: set[str], kept: list[Path], notes: list[str],
            budget: _Budget, depth: int):
    if depth > MAX_DEPTH:
        raise ArchiveError(f"{label}: archives are nested more than {MAX_DEPTH} deep")
    kind = archive_kind(path.name)
    found = 0
    skipped: list[str] = []
    for name, folder, data_path in _entries(path, kind, label, work, budget):
        inner = f"{label} › {name}"
        if is_archive(name):
            _unpack(data_path, inner, dest, work, keep, kept, notes, budget, depth + 1)
            found += 1
        elif Path(name).suffix.lower() in keep:
            kept.append(_place(data_path, name, folder, dest))
            found += 1
        else:
            skipped.append(name)
    notes.append(f"unpacked {label}: {found} file(s)" + (f"; left out {len(skipped)} other file(s): " + ", ".join(skipped[:8])
                                                         + (" …" if len(skipped) > 8 else "") if skipped else ""))


def _entries(path: Path, kind: str, label: str, work: Path, budget: _Budget):
    """(file name, folder it sat in, a local path to its bytes) for every regular file of an archive."""
    work.mkdir(parents=True, exist_ok=True)
    if kind == "zip":
        yield from _zip_entries(path, label, work, budget)
    elif kind == "tar":
        yield from _tar_entries(path, label, work, budget)
    elif kind == "single":
        yield from _single_entry(path, label, work, budget)
    elif kind == "7z":
        yield from _7z_entries(path, label, work, budget)
    elif kind == "rar":
        yield from _rar_entries(path, label, work, budget)


def _safe_parts(name: str) -> list[str] | None:
    """The path's parts inside the archive, or None for a path that would leave the folder or is junk."""
    parts = [x for x in PurePosixPath(name.replace("\\", "/")).parts if x not in ("", ".")]
    if not parts or any(x == ".." for x in parts) or name.startswith(("/", "\\")) or ":" in parts[0]:
        return None
    if any(x.lower() in JUNK_DIRS for x in parts[:-1]):
        return None
    base = parts[-1]
    if base.lower() in JUNK_NAMES or base.startswith(("._", "~$")):
        return None
    return parts


def _scratch(work: Path, name: str) -> Path:
    i = 0
    while True:
        out = work / f"{i:05d}-{Path(name).name[-80:]}"
        if not out.exists():
            return out
        i += 1


def _copy_limited(src, out: Path, budget: _Budget, what: str, declared: int | None = None):
    """Copy one entry out, stopping as soon as the running total passes the cap (an entry's
    declared size is checked first, but the bytes actually read are what count)."""
    if declared is not None and budget.bytes + declared > MAX_TOTAL_BYTES:
        raise ArchiveError(f"the archives unpack to more than {MAX_TOTAL_BYTES // 1024 ** 2} MB ({what}); split them up")
    size = 0
    with out.open("wb") as fh:
        while True:
            chunk = src.read(1 << 20)
            if not chunk:
                break
            size += len(chunk)
            if budget.bytes + size > MAX_TOTAL_BYTES:
                raise ArchiveError(f"the archives unpack to more than {MAX_TOTAL_BYTES // 1024 ** 2} MB ({what}); split them up")
            fh.write(chunk)
    budget.take(size, what)


def _zip_name(info: zipfile.ZipInfo) -> str:
    """Zips made on Windows store non-ASCII names in the local code page without saying so:
    Chinese names come out as cp437 mojibake. Recover them as UTF-8, else GBK."""
    if info.flag_bits & 0x800:
        return info.filename
    try:
        raw = info.filename.encode("cp437")
    except UnicodeEncodeError:
        return info.filename
    for enc in ("utf-8", "gbk"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return info.filename


def _zip_entries(path: Path, label: str, work: Path, budget: _Budget):
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        raise ArchiveError(f"{label} is not a readable zip file") from exc
    with zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = _zip_name(info)
            parts = _safe_parts(name)
            if not parts:
                continue
            if info.flag_bits & 0x1:
                raise ArchiveError(f"{label} is password-protected; unpack it and drop the files, or re-pack without a password")
            out = _scratch(work, parts[-1])
            with zf.open(info) as src:
                _copy_limited(src, out, budget, f"{label} › {name}", declared=info.file_size)
            yield parts[-1], (parts[-2] if len(parts) > 1 else ""), out


def _tar_entries(path: Path, label: str, work: Path, budget: _Budget):
    try:
        tf = tarfile.open(path)
    except tarfile.TarError as exc:
        raise ArchiveError(f"{label} is not a readable tar archive") from exc
    with tf:
        for m in tf:
            if not m.isfile():  # directories, links and devices are never written
                continue
            parts = _safe_parts(m.name)
            if not parts:
                continue
            src = tf.extractfile(m)
            if src is None:
                continue
            out = _scratch(work, parts[-1])
            with src:
                _copy_limited(src, out, budget, f"{label} › {m.name}", declared=m.size)
            yield parts[-1], (parts[-2] if len(parts) > 1 else ""), out


def _single_entry(path: Path, label: str, work: Path, budget: _Budget):
    """report.pdf.gz -> report.pdf"""
    opener = SINGLE_SUFFIXES[Path(path.name.lower()).suffix]
    name = path.name[: -len(Path(path.name).suffix)] or "file"
    out = _scratch(work, name)
    try:
        with opener(path, "rb") as src:
            _copy_limited(src, out, budget, label)
    except (OSError, EOFError, lzma.LZMAError) as exc:
        raise ArchiveError(f"{label} is not a readable compressed file") from exc
    yield name, "", out


def _extracted_files(root: Path, label: str, budget: _Budget):
    """Walk a folder an extractor wrote into, keeping only regular files inside it."""
    root = root.resolve()
    for f in sorted(root.rglob("*")):
        if f.is_symlink() or not f.is_file():
            continue
        try:
            rel = f.resolve().relative_to(root)
        except ValueError:
            continue  # outside the folder: never used
        parts = _safe_parts(rel.as_posix())
        if not parts:
            continue
        budget.take(f.stat().st_size, f"{label} › {rel.as_posix()}")
        yield parts[-1], (parts[-2] if len(parts) > 1 else ""), f


def seven_zip_program() -> str | None:
    """The 7-Zip command-line program, if the server has one."""
    for name in ("7z", "7zz", "7za"):
        found = shutil.which(name)
        if found:
            return found
    for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"), r"C:\Program Files"):
        if base and Path(base, "7-Zip", "7z.exe").is_file():
            return str(Path(base, "7-Zip", "7z.exe"))
    return None


def _cli_entries(path: Path, label: str, work: Path, budget: _Budget, program: str):
    """Read a .7z or .rar with the 7-Zip program: list it (sizes, passwords), then extract it into
    a fresh folder of its own and take only the regular files that stay inside that folder."""
    run = dict(stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    # a dummy password: a protected archive fails at once instead of waiting at a prompt
    listing = subprocess.run([program, "l", "-slt", "-pX-no-password", "--", str(path)], **run)
    if listing.returncode != 0:
        detail = (listing.stderr or listing.stdout).strip().splitlines()[-1:] or [""]
        if "password" in (listing.stderr + listing.stdout).lower():
            raise ArchiveError(f"{label} is password-protected; unpack it and drop the files, or re-pack without a password")
        raise ArchiveError(f"{label} could not be read ({detail[0]})")
    entries = listing.stdout.split("\n\n")
    if any("Encrypted = +" in e for e in entries):
        raise ArchiveError(f"{label} is password-protected; unpack it and drop the files, or re-pack without a password")
    declared = 0
    for e in entries:
        for line in e.splitlines():
            if line.startswith("Size = ") and line[7:].strip().isdigit():
                declared += int(line[7:].strip())
    if budget.bytes + declared > MAX_TOTAL_BYTES:
        raise ArchiveError(f"{label} unpacks to more than {MAX_TOTAL_BYTES // 1024 ** 2} MB; split it up")
    root = _scratch(work, "x")
    root.mkdir()
    # -snl- / no -spf: links are not created and absolute paths are not honoured
    done = subprocess.run([program, "x", "-y", "-pX-no-password", "-bso0", "-bsp0", f"-o{root}", "--", str(path)], **run)
    if done.returncode not in (0, 1):  # 1 = warnings
        text = (done.stderr or done.stdout).lower()
        if "password" in text:
            raise ArchiveError(f"{label} is password-protected; unpack it and drop the files, or re-pack without a password")
        raise ArchiveError(f"{label} could not be unpacked ({(done.stderr or done.stdout).strip().splitlines()[-1:] or ['']})")
    yield from _extracted_files(root, label, budget)


def _7z_entries(path: Path, label: str, work: Path, budget: _Budget):
    try:
        import py7zr  # type: ignore
    except ImportError:
        program = seven_zip_program()
        if program:
            yield from _cli_entries(path, label, work, budget, program)
            return
        raise ArchiveError(f"{label}: .7z archives need 7-Zip or the py7zr package on the server, or re-pack as .zip")
    root = _scratch(work, "7z")
    root.mkdir()
    try:
        with py7zr.SevenZipFile(path, "r") as zf:
            if zf.needs_password():
                raise ArchiveError(f"{label} is password-protected; unpack it and drop the files, or re-pack without a password")
            declared = sum(getattr(i, "uncompressed", 0) or 0 for i in zf.list())
            if budget.bytes + declared > MAX_TOTAL_BYTES:
                raise ArchiveError(f"{label} unpacks to more than {MAX_TOTAL_BYTES // 1024 ** 2} MB; split it up")
            zf.extractall(path=root)
    except ArchiveError:
        raise
    except Exception as exc:  # noqa: BLE001  (py7zr raises several of its own types)
        raise ArchiveError(f"{label} is not a readable 7z archive ({exc})") from exc
    yield from _extracted_files(root, label, budget)


def _rar_entries(path: Path, label: str, work: Path, budget: _Budget):
    try:
        import rarfile  # type: ignore
    except ImportError:
        rarfile = None
    if rarfile is None:
        program = seven_zip_program()  # 7-Zip reads RAR as well
        if program:
            yield from _cli_entries(path, label, work, budget, program)
            return
        raise ArchiveError(f"{label}: .rar archives need 7-Zip on the server; re-pack as .zip or .7z")
    try:
        with rarfile.RarFile(path) as rf:
            if rf.needs_password():
                raise ArchiveError(f"{label} is password-protected; unpack it and drop the files, or re-pack without a password")
            for info in rf.infolist():
                if info.is_dir() or info.is_symlink():
                    continue
                parts = _safe_parts(info.filename)
                if not parts:
                    continue
                out = _scratch(work, parts[-1])
                with rf.open(info) as src:
                    _copy_limited(src, out, budget, f"{label} › {info.filename}", declared=info.file_size)
                yield parts[-1], (parts[-2] if len(parts) > 1 else ""), out
    except ArchiveError:
        raise
    except Exception as exc:  # noqa: BLE001  (no unrar tool, a broken archive)
        raise ArchiveError(f"{label} could not be unpacked ({exc}); re-pack as .zip or .7z") from exc


def _place(data_path: Path, name: str, folder: str, dest: Path) -> Path:
    """Move an unpacked file into dest under its own name; a clash takes its folder's name, then a number."""
    base = Path(name).name
    candidates = [base]
    if folder:
        candidates.append(f"{folder} - {base}")
    stem, suffix = Path(base).stem, Path(base).suffix
    for cand in candidates + [f"{stem} ({i}){suffix}" for i in range(2, 1000)]:
        out = dest / cand
        if not out.exists():
            shutil.move(str(data_path), out)
            return out
    raise ArchiveError(f"too many files named {base}")
