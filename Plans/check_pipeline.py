#!/usr/bin/env python3
"""Check plan naming, central queue priorities, numbering, and archive pairing."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ACTIVE_RE = re.compile(r"^(\d{3})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
PRIORITY_FIELD_RE = re.compile(r"^- Priority:", re.MULTILINE)
PRIORITY_ROW_RE = re.compile(r"^\|\s*([1-9]\d*)\s*\|\s*(\d{3})\s+[—-]\s+[^|]+\|", re.MULTILINE)
ARCHIVE_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2})-(\d{3})-([a-z0-9]+(?:-[a-z0-9]+)*?)(-walkthrough)?\.md$"
)


def main() -> int:
    errors: list[str] = []
    active = []
    queued = []
    queued_by_number: dict[str, str] = {}
    locations: dict[str, tuple[str, str]] = {}

    for path in sorted(ROOT.glob("[0-9]*.md")):
        match = ACTIVE_RE.fullmatch(path.name)
        if not match:
            errors.append(f"invalid active-plan filename: {path.name}")
            continue
        active.append(path)
        number = match.group(1)
        if number in locations:
            errors.append(f"plan number {number} is duplicated in the in-work directory")
        locations[number] = ("active", path.name)
        text = path.read_text()
        if "- Status: Queued" in text:
            errors.append(f"in-work plan still declares queued status: {path.name}")
        if PRIORITY_FIELD_RE.search(text):
            errors.append(f"priority must exist only in Plans/PRIORITIES.md: {path.name}")

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
        queued_by_number[number] = path.name
        text = path.read_text()
        if "- Status: Queued" not in text:
            errors.append(f"queued plan does not declare queued status: {path.name}")
        if PRIORITY_FIELD_RE.search(text):
            errors.append(f"priority must exist only in Plans/PRIORITIES.md: {path.name}")

    priority_doc = ROOT / "PRIORITIES.md"
    if queued and not priority_doc.is_file():
        errors.append("queued plans exist but Plans/PRIORITIES.md is missing")
    priorities: dict[int, str] = {}
    prioritized_numbers: set[str] = set()
    if priority_doc.is_file():
        for match in PRIORITY_ROW_RE.finditer(priority_doc.read_text()):
            priority, number = int(match.group(1)), match.group(2)
            if priority in priorities:
                errors.append(f"priority {priority} appears more than once in Plans/PRIORITIES.md")
            if number in prioritized_numbers:
                errors.append(f"plan {number} appears more than once in Plans/PRIORITIES.md")
            priorities[priority] = number
            prioritized_numbers.add(number)

    expected_priorities = set(range(1, len(queued) + 1))
    if set(priorities) != expected_priorities:
        errors.append(
            "priority table ranks must be contiguous from 1 through "
            f"{len(queued)}; found {sorted(priorities)}"
        )
    if prioritized_numbers != set(queued_by_number):
        errors.append(
            "priority table plan numbers must exactly match queued plans; "
            f"table={sorted(prioritized_numbers)}, queued={sorted(queued_by_number)}"
        )

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

    active_names = ", ".join(path.name for path in active) if active else "none"
    highest = max((int(number) for number in locations), default=0)
    next_number = priorities.get(1)
    next_queued = queued_by_number.get(next_number, "none") if next_number else "none"
    print(
        f"Plan pipeline valid; in-work plans: {active_names}; "
        f"queued plans: {len(queued)}; next queued: {next_queued}; "
        f"next number: {highest + 1:03d}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
