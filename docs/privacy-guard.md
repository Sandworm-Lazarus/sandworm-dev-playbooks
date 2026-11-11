# Offline privacy preprocessing

`scripts/privacy_guard.py` is original Python code for one explicit application
policy: mask conventional ASCII email addresses in text, and mask configured
field values in JSON. It runs locally with the Python standard library and makes
no network, model, or API calls. It targets Python 3.9 or newer.

Use it to prepare a bounded support-ticket fixture or application event before
another system consumes the result. Review the field policy for that application.
The utility does not discover every kind of personal information, certify a
document as anonymous, or wrap Presidio.

## Policy

| Input | Transformation |
| --- | --- |
| Text | Replace matched ASCII email addresses with `[EMAIL_REDACTED]`; preserve other characters and whitespace. |
| JSON string values | Apply the same email masking recursively through lists and objects. |
| Configured JSON fields | Replace the entire value, including a nested object, number or null, with `[FIELD_REDACTED]`. |
| Other supported JSON values | Preserve booleans, finite numbers, null and structure. |
| JSON object keys | Preserve key names exactly; do not mask their contents or rename them. |

Default sensitive fields are `customer_name`, `password`, `api_key`,
`access_token`, `refresh_token`, `secret`, and `authorization`. Matching compares
the complete field name after Unicode case folding. It does not trim whitespace,
normalize Unicode, match substrings, or infer that a differently named field is
sensitive. For example, `PASSWORD` matches; `password_hint` does not.

The complete original JSON tree is validated before any field is discarded. A
malformed or over-budget value inside `password` still causes rejection.

## CLI

Run from the repository root. Supply input through stdin or `--input`; there is
no command-line argument for original text.

```bash
printf '%s' 'ส่งเอกสารไปที่ nina@example.invalid' | python3 scripts/privacy_guard.py text
```

Output:

```text
ส่งเอกสารไปที่ [EMAIL_REDACTED]
```

Add an application field with a repeatable option. CLI additions extend the
default field set.

```bash
printf '%s' '{"citizen_id":"SYNTHETIC-ID","note":"alex@example.invalid","version":"3.12"}' | python3 scripts/privacy_guard.py json --sensitive-field citizen_id
```

Output:

```json
{"citizen_id":"[FIELD_REDACTED]","note":"[EMAIL_REDACTED]","version":"3.12"}
```

File input and resource limits:

```bash
python3 scripts/privacy_guard.py json --input examples/privacy-input.json --max-bytes 65536 --max-depth 16
python3 scripts/privacy_guard.py --help
```

Successful stdout contains only the transformed document. JSON uses sorted keys,
compact separators and UTF-8 characters; neither mode adds a trailing newline.
Passing successful output through the same mode and policy produces identical
output. Validation finishes before output is written. Diagnostics never include
the original document, rejected argument, or file path.

| Exit status | Meaning |
| --- | --- |
| `0` | Transformation succeeded; an empty text result is valid. |
| `2` | Invalid arguments, invalid policy, malformed or unsupported input, or exceeded budget. No transformed output is emitted. |
| `3` | File or stream I/O failed. The output destination may have received bytes before a write failure. |

Do not overwrite an input file by redirecting stdout to that same file: the shell
can truncate it before Python reads it. Choose a separate output file and check
the exit status before using the result.

## Python API

No installation is required when the repository root is on `sys.path`.

```python
from scripts.privacy_guard import (
    DEFAULT_SENSITIVE_FIELDS, Policy, PrivacyError,
    mask_json, mask_text, redact_json_text,
)

policy = Policy(
    sensitive_fields=DEFAULT_SENSITIVE_FIELDS + ("citizen_id",),
    max_bytes=65536,
    max_depth=16,
)

try:
    text = mask_text("ติดต่อ nina@example.invalid", policy)
    event = mask_json({"citizen_id": "SYNTHETIC-ID", "attempts": 2}, policy)
    serialized = redact_json_text('{"note":"alex@example.invalid"}', policy)
except PrivacyError:
    # Stop this processing path. Do not forward the rejected original input.
    raise
```

`mask_text` returns a string, `mask_json` returns a new JSON-compatible value
without mutating the original, and `redact_json_text` strictly parses and returns
deterministic JSON text. `Policy(sensitive_fields=("private_note",))` replaces the
default field set in the Python API; explicitly append defaults when desired.
No policy-file loader or extra dependency is needed.

## Budgets and rejected inputs

- Default input and output byte budget: **1,048,576 UTF-8 bytes**, configurable
  with `max_bytes` / `--max-bytes` up to a hard maximum of **16,777,216**.
- Default JSON depth: **32**; the root value has depth zero. It can be configured
  from **0** to **128**. For example, `[[0]]` has maximum value depth two.
- JSON has a fixed **50,000 value-node** budget, including the root. Object keys
  contribute bytes but are not value nodes. Empty objects and lists are nodes.
- Integers are limited to **4,096 decimal digits**, independent of whether the
  Python interpreter has its own integer conversion limit.
- Sensitive-field policy: at most **128 names**, each **1–128 characters**.

For text, measure the original UTF-8 input. For an already parsed Python JSON
value, measure its compact UTF-8 JSON representation, including keys, punctuation
and escapes. JSON text/CLI input must also fit the original serialized byte
budget, including input whitespace. Output must fit the same budget so it can be
processed again. Replacing a very short email with a longer mask can therefore
cause rejection near the configured byte limit.

Rejected JSON includes duplicate keys, trailing documents, NaN/Infinity,
overflowing non-finite floats, unsupported Python types, non-string object keys,
cycles and invalid Unicode surrogates. CLI input must decode as strict UTF-8;
UTF-8 BOM JSON is rejected. A nesting scan runs before the JSON parser so deeply
nested input is rejected before recursive parsing. Valid root scalars are
supported; empty text is supported, while an empty JSON document is invalid.

## Limitations and evidence

The email pattern is bounded ASCII pattern matching, not full RFC mailbox
validation. Quoted mailbox syntax, single-label hosts, internationalized mailbox
forms, obfuscated addresses and encoded data are outside the supported policy.
It can over-mask strings that resemble conventional addresses. Arbitrary Thai
names, phone numbers, identification numbers, locations and secrets in free text
remain unchanged unless a relevant JSON field is explicitly configured. In text
mode, JSON-looking text receives only email masking; field policy requires JSON
mode. Keys and other metadata can contain sensitive information and are preserved.

The utility does not extract PDFs, scan binary files, load URL input, encrypt
data, prevent other application logging, or detect model prompt injection. Choose
another component when those capabilities are required. Synthetic fixture results
do not measure recall on real user data or establish compliance.

Run the local, synthetic-data-only suite:

```bash
python3 -m unittest discover -s tests -p 'test_privacy_guard.py' -v
python3 scripts/check_privacy_fixtures.py
```

The suite exercises expected outputs, repeated passes, recursive structure,
case matching, UTF-8 byte/depth/node boundaries, parser rejection, malformed
Unicode, distinct CLI errors and non-disclosure of synthetic input markers in
diagnostics. All example addresses use reserved `.invalid` domains; names,
identifiers and tokens are fabricated.

[The fixture file](../examples/privacy-fixtures.json) keeps upstream
`runtime_tested` false. Its expected outputs define this utility's policy and
remain proposed criteria for any Presidio or other adapter. The fixture runner's
report records local utility evidence separately; it is not evidence that an
upstream recognizer or third-party tool was executed. This repository does not
claim runtime validation across every Python version it supports or a successful
GitHub-hosted CI run based solely on these local commands.
