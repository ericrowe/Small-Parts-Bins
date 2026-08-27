#!/usr/bin/env python3
"""Check plan naming, single-active-plan, numbering, and archive pairing."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ACTIVE_RE = re.compile(r"^(\d{3})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
ARCHIVE_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2})-(\d{3})-([a-z0-9]+(?:-[a-z0-9]+)*?)(-walkthrough)?\.md$"
)


def main() -> int:
    errors: list[str] = []
    active = []
    numbers: dict[str, str] = {}

    for path in sorted(ROOT.glob("[0-9]*.md")):
        match = ACTIVE_RE.fullmatch(path.name)
        if not match:
            errors.append(f"invalid active-plan filename: {path.name}")
            continue
        active.append(path)
        number = match.group(1)
        numbers[number] = path.name

    if len(active) > 1:
        errors.append("more than one numbered plan is active: " + ", ".join(p.name for p in active))

    archived: dict[tuple[str, str, str], set[bool]] = {}
    for path in sorted((ROOT / "Completed").glob("*.md")):
        match = ARCHIVE_RE.fullmatch(path.name)
        if not match:
            errors.append(f"invalid archived filename: {path.name}")
            continue
        date, number, slug, walkthrough = match.groups()
        archived.setdefault((date, number, slug), set()).add(bool(walkthrough))
        if number in numbers and numbers[number] != path.name:
            errors.append(f"plan number {number} exists in both active and completed locations")
        numbers[number] = path.name

    for key, variants in archived.items():
        if variants != {False, True}:
            date, number, slug = key
            errors.append(f"archive pair incomplete for {date}-{number}-{slug}")

    if errors:
        print("Plan pipeline check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    active_name = active[0].name if active else "none"
    highest = max((int(number) for number in numbers), default=0)
    print(f"Plan pipeline valid; active plan: {active_name}; next number: {highest + 1:03d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

