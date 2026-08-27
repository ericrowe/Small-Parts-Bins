#!/usr/bin/env python3
"""Check active/queued plan naming, numbering, and archive pairing."""

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
    queued = []
    locations: dict[str, tuple[str, str]] = {}

    for path in sorted(ROOT.glob("[0-9]*.md")):
        match = ACTIVE_RE.fullmatch(path.name)
        if not match:
            errors.append(f"invalid active-plan filename: {path.name}")
            continue
        active.append(path)
        number = match.group(1)
        locations[number] = ("active", path.name)

    if len(active) > 1:
        errors.append("more than one numbered plan is active: " + ", ".join(p.name for p in active))

    for path in sorted((ROOT / "Queued").glob("*.md")):
        match = ACTIVE_RE.fullmatch(path.name)
        if not match:
            errors.append(f"invalid queued-plan filename: {path.name}")
            continue
        queued.append(path)
        number = match.group(1)
        if number in locations:
            errors.append(
                f"plan number {number} exists in both {locations[number][0]} and queued locations"
            )
        locations[number] = ("queued", path.name)
        if "- Status: Queued" not in path.read_text():
            errors.append(f"queued plan does not declare queued status: {path.name}")

    archived: dict[tuple[str, str, str], set[bool]] = {}
    for path in sorted((ROOT / "Completed").glob("*.md")):
        match = ARCHIVE_RE.fullmatch(path.name)
        if not match:
            errors.append(f"invalid archived filename: {path.name}")
            continue
        date, number, slug, walkthrough = match.groups()
        archived.setdefault((date, number, slug), set()).add(bool(walkthrough))
        if number in locations and locations[number][0] != "completed":
            errors.append(
                f"plan number {number} exists in both {locations[number][0]} and completed locations"
            )
        locations[number] = ("completed", path.name)

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
    highest = max((int(number) for number in locations), default=0)
    print(
        f"Plan pipeline valid; active plan: {active_name}; "
        f"queued plans: {len(queued)}; next number: {highest + 1:03d}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
