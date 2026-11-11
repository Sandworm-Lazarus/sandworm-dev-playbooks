# Original Privacy Guard and catalog safeguards

## Problem and implementation

The collection originally supplied six synthetic privacy-policy ideas without an executable adapter. We developed an original Python standard-library utility that masks email-shaped text and explicit sensitive JSON fields. It can run as a CLI or be imported into an application without network requests or model calls.

The policy is deliberately bounded: arbitrary names, telephone numbers, obfuscated addresses and context-dependent secrets require a configured field policy or a separately evaluated detector. This implementation does not wrap or validate upstream Presidio.

The [guide](../privacy-guard.md) documents input limits, marker behavior, policy configuration, exit codes and supported input. The [sample](../../examples/privacy-input.json) contains synthetic data only.

```bash
python3 scripts/privacy_guard.py json --sensitive-field customer_name < examples/privacy-input.json
python3 scripts/check_privacy_fixtures.py --check-report examples/privacy-guard-results.json
python3 -m unittest discover -s tests -v
```

## Reproducible evidence

The [fixture report](../../examples/privacy-guard-results.json) records each synthetic case's outcome and SHA-256 hashes for the guard, runner and fixtures. It excludes raw input and transformed payloads. `--check-report` reruns those cases and fails if the report is stale or any expectation fails. The report has no timestamps or machine-specific paths, so the same source and fixtures produce identical bytes.

Unit and CLI regressions additionally exercise malformed JSON, nested field policies, budgets, idempotency and sanitized failure behavior. Synthetic test coverage is evidence for these defined cases, not a universal privacy guarantee.

## Catalog safeguards

The validator now checks required array/object shapes and consumer field types before semantic checks. Previously, malformed fixtures such as a list-valued tool purpose, a missing source note or missing top-level evidence could pass validation and fail later in search/render. They are now rejected at validation.

The focused collection generator derives snapshot identity from the hub rather than a fixed date. Generator regressions check future snapshots, deterministic output, skill partitioning, and exact tool/source/evidence subsets. The original utility is distributed to Cyber Arsenal and Dev Playbooks from the hub source.

## Validation scope

Local catalog, generation, privacy-policy and CLI checks are separate from hosted GitHub Actions results. Follow the workflow runs for hosted execution status. The 160 linked skill entries and 66 upstream tools retain their existing review labels and untested runtime status; none was installed or executed as part of this development.

Original implementation, fixture runner, tests and documentation are covered by this repository's MIT license. Linked external projects retain their own terms.
