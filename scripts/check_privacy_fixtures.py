#!/usr/bin/env python3
"""Reproduce bounded privacy-policy fixture results without recording payloads."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from privacy_guard import DEFAULT_SENSITIVE_FIELDS, Policy, PrivacyError, mask_json, mask_text

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples" / "privacy-fixtures.json"
MAX_FIXTURE_BYTES = 2 * 1024 * 1024
IDENTIFIER = re.compile(r"[a-z][a-z0-9-]{0,79}\Z")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate_fixtures(path=FIXTURES):
    """Return deterministic case outcomes and content hashes, never payloads."""
    with Path(path).open("rb") as handle:
        raw = handle.read(MAX_FIXTURE_BYTES + 1)
    if len(raw) > MAX_FIXTURE_BYTES:
        raise ValueError("Fixture file exceeds the size budget")
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("cases"), list) or not data["cases"]:
        raise ValueError("Invalid fixture schema")
    seen = set()
    outcomes = []
    for case in data["cases"]:
        if not isinstance(case, dict):
            raise ValueError("Invalid fixture case")
        ident = case.get("id")
        fields = case.get("sensitive_fields", [])
        if (not isinstance(ident, str) or not IDENTIFIER.fullmatch(ident) or ident in seen
                or case.get("mode") not in ("text", "json")
                or "input" not in case or "expected_output" not in case
                or not isinstance(fields, list) or any(not isinstance(x, str) for x in fields)):
            raise ValueError("Invalid fixture case contract")
        seen.add(ident)
        try:
            policy = Policy(sensitive_fields=DEFAULT_SENSITIVE_FIELDS + tuple(fields))
            operation = mask_text if case["mode"] == "text" else mask_json
            observed = operation(case["input"], policy)
            canonical = lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True,
                                                 allow_nan=False, separators=(",", ":"))
            passed = canonical(observed) == canonical(case["expected_output"])
        except (PrivacyError, TypeError, ValueError):
            passed = False
        outcomes.append({"id": ident, "passed": passed})
    return {
        "schema_version": 1,
        "tool": "Sandworm Privacy Guard",
        "scope": "Synthetic email and explicit JSON-field masking cases only. No upstream runtime or general PII coverage claim.",
        "source_sha256": {
            "guard": digest(ROOT / "scripts" / "privacy_guard.py"),
            "fixtures": hashlib.sha256(raw).hexdigest(),
            "runner": digest(Path(__file__).resolve()),
        },
        "cases_total": len(outcomes),
        "cases_passed": sum(case["passed"] for case in outcomes),
        "all_passed": all(case["passed"] for case in outcomes),
        "cases": outcomes,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=FIXTURES)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write-report", type=Path)
    mode.add_argument("--check-report", type=Path)
    args = parser.parse_args(argv)
    try:
        result = evaluate_fixtures(args.fixtures)
        output = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.check_report:
            if args.check_report.read_text(encoding="utf-8") != output:
                print("Fixture report differs; regenerate and review the source/fixture changes.", file=sys.stderr)
                return 1
        elif args.write_report:
            args.write_report.write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)
        if not result["all_passed"]:
            print("One or more synthetic privacy cases failed.", file=sys.stderr)
            return 1
        return 0
    except (ValueError, TypeError, UnicodeError, RecursionError):
        print("Cannot evaluate fixtures: invalid fixture data.", file=sys.stderr)
        return 2
    except OSError:
        print("Cannot read or write fixture evidence.", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
