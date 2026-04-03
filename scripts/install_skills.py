#!/usr/bin/env python3
"""Install repository skills into the local Codex skills directory."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = ROOT / "skills.config.json"
TARGET_ROOT = Path.home() / ".codex" / "skills"


def main() -> int:
    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    skills = config.get("skills", [])
    TARGET_ROOT.mkdir(parents=True, exist_ok=True)

    for skill in skills:
        name = skill["name"]
        source = ROOT / skill["path"]
        destination = TARGET_ROOT / name

        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
        print(f"Skill installé: {name} -> {destination}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
