#!/usr/bin/env python3
"""Offline, bounded preprocessing of conventional email addresses and JSON fields.

This is an explicit application policy, not general PII detection. Nothing here
uses a network service, a model, third-party packages, or original-input logging.
"""

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from typing import Any, Optional, Tuple


EMAIL_MASK = "[EMAIL_REDACTED]"
FIELD_MASK = "[FIELD_REDACTED]"
DEFAULT_SENSITIVE_FIELDS = (
    "customer_name", "password", "api_key", "access_token", "refresh_token",
    "secret", "authorization",
)
DEFAULT_MAX_BYTES = 1024 * 1024
DEFAULT_MAX_DEPTH = 32
MAX_NODES = 50000
HARD_MAX_BYTES = 16 * 1024 * 1024
HARD_MAX_DEPTH = 128
MAX_INTEGER_DIGITS = 4096
_INTEGER_LIMIT = 10 ** MAX_INTEGER_DIGITS

# A deliberately bounded ASCII pattern, not an RFC mailbox parser. Each local
# part has at most 64 characters; a hostname must contain at least one dot.
_LOCAL = r"A-Za-z0-9.!#$%&'*+/=?^_`{|}~\-"
_LABEL = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
EMAIL_RE = re.compile(
    r"(?<![" + _LOCAL + r"@])[" + _LOCAL + r"]{1,64}@"
    + _LABEL + r"(?:\." + _LABEL + r")+(?![A-Za-z0-9_\-])"
)


class PrivacyError(ValueError):
    """A rejected input or policy; messages never include original input."""


@dataclass(frozen=True)
class Policy:
    """Exact case-insensitive JSON field policy and bounded input limits.

    Passing sensitive_fields replaces the defaults in the Python API. The CLI's
    repeatable --sensitive-field adds names to the defaults instead.
    """

    sensitive_fields: Tuple[str, ...] = DEFAULT_SENSITIVE_FIELDS
    max_bytes: int = DEFAULT_MAX_BYTES
    max_depth: int = DEFAULT_MAX_DEPTH

    def __post_init__(self) -> None:
        if type(self.max_bytes) is not int or not 1 <= self.max_bytes <= HARD_MAX_BYTES:
            raise PrivacyError("invalid byte budget")
        if type(self.max_depth) is not int or not 0 <= self.max_depth <= HARD_MAX_DEPTH:
            raise PrivacyError("invalid depth budget")
        if not isinstance(self.sensitive_fields, (list, tuple, set, frozenset)):
            raise PrivacyError("invalid sensitive-field policy")
        if len(self.sensitive_fields) > 128:
            raise PrivacyError("too many sensitive fields")
        names = []
        for name in self.sensitive_fields:
            if type(name) is not str or not name or len(name) > 128:
                raise PrivacyError("invalid sensitive-field name")
            _utf8(name)
            names.append(name.casefold())
        object.__setattr__(self, "sensitive_fields", tuple(sorted(set(names))))


def _policy(policy: Optional[Policy]) -> Policy:
    if policy is None:
        return Policy()
    if not isinstance(policy, Policy):
        raise PrivacyError("invalid policy")
    return policy


def _utf8(text: str) -> bytes:
    try:
        return text.encode("utf-8")
    except UnicodeEncodeError:
        raise PrivacyError("input is not valid UTF-8 text") from None


def _text_budget(text: str, policy: Policy) -> None:
    if type(text) is not str:
        raise PrivacyError("text input must be a string")
    if len(text) > policy.max_bytes or len(_utf8(text)) > policy.max_bytes:
        raise PrivacyError("input exceeds byte budget")


def mask_text(text: str, policy: Optional[Policy] = None) -> str:
    """Mask matched ASCII email addresses, preserving all other text exactly."""
    active_policy = _policy(policy)
    _text_budget(text, active_policy)
    result = EMAIL_RE.sub(EMAIL_MASK, text)
    _text_budget(result, active_policy)
    return result


def _validate_json(value: Any, policy: Policy) -> None:
    """Validate the complete original tree before masking even sensitive fields.

    The byte budget is measured using compact, UTF-8 JSON with ensure_ascii=False.
    An iterative walk also rejects cycles, unsupported Python types, non-finite
    numbers, excessive depth, and excessive node count before serialization.
    """
    stack = [(False, value, 0)]
    ancestors = set()
    used_bytes = 0
    nodes = 0
    pending = 1
    while stack:
        leaving, current, depth = stack.pop()
        if leaving:
            ancestors.remove(current)
            continue
        nodes += 1
        pending -= 1
        if nodes > MAX_NODES:
            raise PrivacyError("input exceeds node budget")
        if depth > policy.max_depth:
            raise PrivacyError("input exceeds depth budget")
        kind = type(current)
        if kind is str:
            _text_budget(current, policy)
            used_bytes += len(_utf8(json.dumps(current, ensure_ascii=False)))
        elif current is None or kind is bool:
            used_bytes += len(json.dumps(current))
        elif kind is int:
            if current <= -_INTEGER_LIMIT or current >= _INTEGER_LIMIT:
                raise PrivacyError("integer exceeds supported representation")
            try:
                used_bytes += len(str(current))
            except ValueError:
                raise PrivacyError("integer exceeds supported representation") from None
        elif kind is float:
            if not math.isfinite(current):
                raise PrivacyError("non-finite JSON number is unsupported")
            used_bytes += len(json.dumps(current, allow_nan=False))
        elif kind in (list, dict):
            identity = id(current)
            if identity in ancestors:
                raise PrivacyError("cyclic JSON input is unsupported")
            # Avoid allocating an unbounded traversal stack for broad objects.
            pending += len(current)
            if pending + nodes > MAX_NODES:
                raise PrivacyError("input exceeds node budget")
            ancestors.add(identity)
            stack.append((True, identity, depth))
            used_bytes += 2 + max(0, len(current) - 1)
            if kind is dict:
                for key, child in current.items():
                    if type(key) is not str:
                        raise PrivacyError("JSON object keys must be strings")
                    _text_budget(key, policy)
                    used_bytes += len(_utf8(json.dumps(key, ensure_ascii=False))) + 1
                    if used_bytes > policy.max_bytes:
                        raise PrivacyError("input exceeds byte budget")
                    stack.append((False, child, depth + 1))
            else:
                stack.extend((False, child, depth + 1) for child in current)
        else:
            raise PrivacyError("unsupported JSON value type")
        if used_bytes > policy.max_bytes:
            raise PrivacyError("input exceeds byte budget")


def mask_json(value: Any, policy: Optional[Policy] = None) -> Any:
    """Return a new JSON value with policy fields and string values masked.

    Object keys are preserved. Field matching uses exact Unicode casefolded names,
    without substring matching or Unicode normalization. Root depth is zero.
    """
    active_policy = _policy(policy)
    _validate_json(value, active_policy)
    fields = frozenset(active_policy.sensitive_fields)

    def walk(current: Any) -> Any:
        if type(current) is str:
            return EMAIL_RE.sub(EMAIL_MASK, current)
        if type(current) is list:
            return [walk(child) for child in current]
        if type(current) is dict:
            return {
                key: FIELD_MASK if key.casefold() in fields else walk(current[key])
                for key in sorted(current)
            }
        return current

    result = walk(value)
    _validate_json(result, active_policy)
    return result


def _reject_constant(_constant: str) -> None:
    raise PrivacyError("non-finite JSON number is unsupported")


def _parse_integer(text: str) -> int:
    # Bound decimal conversion explicitly even on Python 3.9 runtimes without
    # the newer interpreter-level integer string conversion limit.
    if len(text.lstrip("-")) > MAX_INTEGER_DIGITS:
        raise PrivacyError("integer exceeds supported representation")
    return int(text)


def _unique_object(pairs: Any) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise PrivacyError("duplicate JSON object key")
        result[key] = value
    return result


def _check_nesting(text: str, policy: Policy) -> None:
    """Bound parser nesting before json.loads, ignoring quoted brackets."""
    level = 0
    quoted = False
    escaped = False
    for character in text:
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
        elif character == '"':
            quoted = True
        elif character in "[{":
            level += 1
            if level > policy.max_depth + 1:
                raise PrivacyError("input exceeds depth budget")
        elif character in "]}":
            level -= 1


def redact_json_text(text: str, policy: Optional[Policy] = None) -> str:
    """Strictly parse, mask, and deterministically serialize one JSON document."""
    active_policy = _policy(policy)
    _text_budget(text, active_policy)
    _check_nesting(text, active_policy)
    try:
        original = json.loads(
            text, object_pairs_hook=_unique_object, parse_constant=_reject_constant,
            parse_int=_parse_integer,
        )
    except PrivacyError:
        raise
    except (ValueError, RecursionError, OverflowError):
        raise PrivacyError("malformed or unsupported JSON input") from None
    redacted = mask_json(original, active_policy)
    return json.dumps(redacted, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, _message: str) -> None:
        # argparse's default can echo an input argument, including a secret.
        self.exit(2, "privacy_guard: invalid command arguments; use --help\n")


def main(argv: Optional[list] = None) -> int:
    parser = _ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("text", "json"))
    parser.add_argument("--input", metavar="PATH", help="read UTF-8 input file; otherwise stdin")
    parser.add_argument("--sensitive-field", action="append", default=[], metavar="NAME",
                        help="add an exact case-insensitive JSON field name (repeatable)")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH)
    args = parser.parse_args(argv)
    try:
        policy = Policy(sensitive_fields=DEFAULT_SENSITIVE_FIELDS + tuple(args.sensitive_field),
                        max_bytes=args.max_bytes, max_depth=args.max_depth)
        if args.input:
            with open(args.input, "rb") as source:
                raw = source.read(policy.max_bytes + 1)
        else:
            raw = sys.stdin.buffer.read(policy.max_bytes + 1)
        if len(raw) > policy.max_bytes:
            raise PrivacyError("input exceeds byte budget")
        try:
            incoming = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise PrivacyError("input is not valid UTF-8 text") from None
        outgoing = (mask_text(incoming, policy) if args.mode == "text"
                    else redact_json_text(incoming, policy))
        sys.stdout.buffer.write(_utf8(outgoing))
        sys.stdout.buffer.flush()
        return 0
    except PrivacyError as error:
        sys.stderr.write("privacy_guard: " + str(error) + "\n")
        return 2
    except OSError:
        sys.stderr.write("privacy_guard: input/output operation failed\n")
        try:
            sys.stdout.close()
        except OSError:
            pass
        return 3


if __name__ == "__main__":
    sys.exit(main())
