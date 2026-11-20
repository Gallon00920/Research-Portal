"""Upload a Skill folder to the Claude API and print its id.

    py -3.13 panel/backend/upload_skill.py <skill folder> [--sector <sector id>] [--update] [--display-name <name>]

The folder holds a SKILL.md (with the name / description frontmatter) and whatever references,
scripts and examples the skill uses; the whole folder is sent (under 30 MB), less Python caches
and OS junk files. ANTHROPIC_API_KEY must be set in the environment.

With --sector, the skill is registered for that sector in panel/data/ai_skills.json, where the
report generation (ai_assist.py) reads it. With --update, a sector that already has a skill gets
a new version of that same skill (its id stays, and the generation picks up the latest version);
without --update, or for a sector with no skill yet, a new skill is created.

    py -3.13 panel/backend/upload_skill.py --all
uploads every quarterly skill in panel/skills/ for its research sector (SECTOR_SKILLS below),
updating the skills that are already registered and creating the others.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_FILE = ROOT / "data" / "ai_skills.json"
SKILLS_DIR = ROOT / "skills"
# research sector -> skill folder under panel/skills/
SECTOR_SKILLS = {
    "private_credit": "private-credit-quarterly-report",
    "software_otf": "otf-quarterly-report",
    "private_equity": "pe-quarterly-report",
    "aviation": "aircraft-quarterly-report",
}
SKIP_DIRS = {"__pycache__", ".git", ".ipynb_checkpoints"}
SKIP_FILES = {".DS_Store", "Thumbs.db", "desktop.ini"}


def skill_files(folder: Path) -> list[tuple[str, bytes]]:
    """(path inside the upload, bytes) for every file of the skill, the folder name first."""
    out = []
    for p in sorted(folder.rglob("*")):
        rel = p.relative_to(folder.parent)
        if not p.is_file() or any(part in SKIP_DIRS for part in rel.parts) or p.name in SKIP_FILES or p.suffix == ".pyc":
            continue
        out.append((rel.as_posix(), p.read_bytes()))
    return out


def skill_name(folder: Path) -> str:
    for line in (folder / "SKILL.md").read_text(encoding="utf-8").splitlines()[1:12]:
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip('"')
    return folder.name


def upload(client, folder: Path, sector: str = "", update: bool = False, display_name: str = "") -> int:
    folder = folder.resolve()
    if not (folder / "SKILL.md").is_file():
        print(f"no SKILL.md in {folder}", file=sys.stderr)
        return 2
    files = skill_files(folder)
    size = sum(len(b) for _, b in files)
    name = skill_name(folder)
    data = json.loads(SKILLS_FILE.read_text(encoding="utf-8")) if SKILLS_FILE.exists() else {}
    existing = (data.get(sector) or {}).get("skill_id") if sector else None
    print(f"{name}: {len(files)} files, {size / 1e6:.1f} MB")
    if update and existing:
        version = client.skills.versions.create(existing, files=files)
        print(f"  new version of {existing}: {getattr(version, 'id', '') or getattr(version, 'version', '')}")
        skill_id = existing
    else:
        kwargs = {"files": files}
        if display_name:
            kwargs["display_name"] = display_name
        skill = client.skills.create(**kwargs)
        skill_id = skill.id
        print(f"  skill id:       {skill.id}")
        print(f"  latest version: {skill.latest_version_id}")
        print(f"  display name:   {skill.display_name}")
    if sector:
        data[sector] = {"skill_id": skill_id, "name": name}
        SKILLS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  registered for sector '{sector}' in {SKILLS_FILE.relative_to(ROOT.parent)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Upload a Skill folder to the Claude API.")
    ap.add_argument("folder", type=Path, nargs="?", help="the skill folder (contains SKILL.md)")
    ap.add_argument("--sector", default="", help="register the skill for this sector in panel/data/ai_skills.json")
    ap.add_argument("--update", action="store_true", help="add a new version to the sector's existing skill instead of creating a new skill")
    ap.add_argument("--all", action="store_true", help="upload every quarterly skill in panel/skills/ for its research sector")
    ap.add_argument("--display-name", default="", help="display name in the Console (defaults to the SKILL.md name)")
    a = ap.parse_args()
    if not (a.all or a.folder):
        ap.error("give a skill folder, or --all")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set", file=sys.stderr)
        return 2
    import anthropic

    try:
        import truststore  # type: ignore  (TLS-inspecting corporate proxies)

        truststore.inject_into_ssl()
    except Exception:
        pass
    client = anthropic.Anthropic()
    if a.all:
        rc = 0
        for sector, folder in SECTOR_SKILLS.items():
            if (SKILLS_DIR / folder / "SKILL.md").is_file():
                rc |= upload(client, SKILLS_DIR / folder, sector, update=True)
        return rc
    return upload(client, a.folder, a.sector, a.update, a.display_name)


if __name__ == "__main__":
    sys.exit(main())
