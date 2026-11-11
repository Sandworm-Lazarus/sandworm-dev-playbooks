# Original tool: evidence checker

Verify that local review artifacts still match their declared SHA256 hashes, and that captured command-result metadata matches the expected command, exit code and result label. This offline Python 3.9+ utility is original Sandworm material under the repository MIT license. It reads bounded local files and emits a JSON report; it never executes the declared commands or prints artifact contents.

```bash
python3 scripts/evidence_check.py --manifest examples/evidence-manifest.json --root .
python3 -m unittest discover -s tests -p 'test_evidence_check.py' -v
```

The shipped example is **fabricated**: its command was never executed. The first command reports `ok: true` because two artifact digests and the declared metadata agree. This demonstrates the checker, not a successful run of the fabricated command.

## Practical workflow

1. Run an authorized validation command yourself in its intended environment.
2. Save the resulting report and a small JSON result record containing `command`, `exit_code` and `result`. Keep secrets out of both files.
3. Review the result and commit a manifest of expected hashes and metadata.
4. Use this checker before handing over the evidence or when reproducing a review. A changed/missing artifact or disagreement between expected and recorded results fails verification.

The manifest is the trust input. A person who can replace the manifest and every referenced artifact can manufacture a matching set. This utility does not prove a command ran, attest the machine or execution time, authenticate an author, establish SLSA provenance or evaluate whether a command's own success criteria are correct. Retain independently reviewed or signed source revisions when those properties matter.

## Manifest contract

The root contains `schema_version: 1`, a nonempty `artifacts` array, and an optional `commands` array. Each array has at most 1000 records. Additional fields are ignored.

| Record | Required fields | Meaning |
| --- | --- | --- |
| Artifact | `path`, `sha256` | Canonical relative POSIX file path and 64 lowercase hexadecimal SHA256 characters |
| Command | `id`, `command`, `result_path`, `expected_exit`, `expected_result` | Unique ID; argument array treated as data; declared result artifact; integer expected exit code; expected result label |
| Result file | `command`, `exit_code`, `result` | Recorded argument array, integer exit code and result label |

A `result_path` must also be a declared artifact. Its metadata is checked only after its hash matches. The hash and parsed metadata use the same bytes from one read. Command arguments are never passed to a shell, subprocess or interpreter. The report contains IDs, relative paths, statuses and match booleans; it omits recorded arguments, result labels, source contents and calculated digests.

IDs and result labels are nonempty strings up to 128 characters. Commands contain 1–64 nonempty string arguments, each up to 1024 characters. Expected exit codes range from -255 to 255. Duplicate artifact paths, command IDs and JSON object keys are rejected. Paths are limited to 512 characters.

## Path and resource boundaries

`--root` selects an existing directory. Artifact paths must stay inside its resolved location. Absolute paths, `..`, backslashes, drive/scheme colons, NUL bytes and noncanonical forms such as `a/./b` are rejected. Symlinks resolving outside the root are rejected before any artifacts are read; internal symlinks are allowed. Missing or dangling internal files fail verification. Avoid concurrent modification of the evidence directory during verification; this tool does not lock the filesystem or sandbox a hostile local process.

Input is capped at 1 MiB per manifest, 16 MiB per artifact and 256 KiB for a command-result artifact. Larger inputs fail without being printed. Paths identifying directories are treated as missing artifacts.

| Exit | Meaning |
| --- | --- |
| **0** | All declared hashes and command-result metadata match |
| **1** | Missing/unreadable/oversized artifact, hash mismatch, invalid captured result or metadata mismatch |
| **2** | Malformed manifest, unsafe path, invalid root, input budget error or unreadable manifest |

Use the machine-readable `artifacts[].status` and `commands[].status` to locate a failure. An unsafe manifest rejects the whole batch before artifact reads. Tests cover tampering, mismatched command/exit/result, missing artifacts, traversal, absolute paths, file/directory symlink escapes, output confidentiality and the no-execution contract.
