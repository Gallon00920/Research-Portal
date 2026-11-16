"""Upload a Skill folder to the Claude API and print its id.

    py -3.13 panel/backend/upload_skill.py <skill folder> [--sector <sector id>] [--display-name <name>]

The folder holds a SKILL.md (with the name / description frontmatter) and whatever references,
scripts and examples the skill uses; the whole folder is sent (under 30 MB). ANTHROPIC_API_KEY
must be set in the environment. With --sector, the new skill id is written into
panel/data/ai_skills.json for that sector, where the report generation (ai_assist.py) reads it.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_FILE = ROOT / "data" / "ai_skills.json"


def main() -> int:
    ap = argparse.ArgumentParser(description="Upload a Skill folder to the Claude API.")
    ap.add_argument("folder", type=Path, help="the skill folder (contains SKILL.md)")
    ap.add_argument("--sector", default="", help="register the skill for this sector in panel/data/ai_skills.json")
    ap.add_argument("--display-name", default="", help="display name in the Console (defaults to the SKILL.md name)")
    a = ap.parse_args()
    folder = a.folder.resolve()
    if not (folder / "SKILL.md").is_file():
        print(f"no SKILL.md in {folder}", file=sys.stderr)
        return 2
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set", file=sys.stderr)
        return 2
    import anthropic
    from anthropic.lib import files_from_dir

    client = anthropic.Anthropic()
    kwargs = {"files": files_from_dir(str(folder))}
    if a.display_name:
        kwargs["display_name"] = a.display_name
    skill = client.skills.create(**kwargs)
    name = ""
    for line in (folder / "SKILL.md").read_text(encoding="utf-8").splitlines()[1:12]:
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip()
            break
    print(f"skill id:       {skill.id}")
    print(f"latest version: {skill.latest_version_id}")
    print(f"display name:   {skill.display_name}")
    if a.sector:
        data = json.loads(SKILLS_FILE.read_text(encoding="utf-8")) if SKILLS_FILE.exists() else {}
        data[a.sector] = {"skill_id": skill.id, "name": name or skill.display_name}
        SKILLS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"registered for sector '{a.sector}' in {SKILLS_FILE.relative_to(ROOT.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
