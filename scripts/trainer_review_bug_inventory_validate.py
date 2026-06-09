#!/usr/bin/env python3
"""Validate trainer PR review comment bodies for Bug inventory (P0-P4 declaration)."""
from __future__ import annotations

import re
import sys

INV_HEADING = re.compile(r"^###\s+(Bug inventory|Findings)\b", re.M | re.I)
BUDS_P02_CAP = re.compile(r"P0\s*[-–]\s*P2\b", re.I)
SEV_ROW = re.compile(r"\|\s*[^|\n]+\|\s*P[0-4]\s*\|", re.I)
NONE_DECL = re.compile(
    r"(no\s+P0\s*[-–]\s*P4|no\s+P0-P4|zero\s+P0|P0\s*[-–]\s*P4\s+findings:\s*none|"
    r"no\s+P0\s*[-–]\s*P[0-4]\s+(findings|defects|blockers))",
    re.I,
)


def validate_bug_inventory(body: str, repo: str) -> list[str]:
    errors: list[str] = []
    if not INV_HEADING.search(body):
        errors.append(
            "missing '### Bug inventory' (preferred) or '### Findings' section"
        )
    if repo == "buds" and BUDS_P02_CAP.search(body):
        errors.append(
            "buds remediate scope is P0-P4; do not cap reviews at P0-P2 "
            "(list or waive every P0-P4 item)"
        )
    if not (NONE_DECL.search(body) or SEV_ROW.search(body)):
        errors.append(
            "Bug inventory must table every P0-P4 item (ID | Sev | Finding | Status) "
            "or include an explicit 'No P0-P4 findings' line with evidence"
        )
    return errors


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "usage: trainer_review_bug_inventory_validate.py <repo_slug> <body_file>",
            file=sys.stderr,
        )
        return 2
    repo = sys.argv[1].strip().lower()
    body_path = sys.argv[2]
    try:
        body = open(body_path, encoding="utf-8").read()
    except OSError as exc:
        print(f"FAIL  cannot read body: {exc}", file=sys.stderr)
        return 2
    errors = validate_bug_inventory(body, repo)
    if errors:
        for err in errors:
            print(f"FAIL  {err}", file=sys.stderr)
        return 1
    print("PASS  bug inventory declaration")
    return 0


if __name__ == "__main__":
    sys.exit(main())
