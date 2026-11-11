# [Detection intent]

## Goal and data

- Behavior to detect: [observable behavior]
- Required telemetry: [event sources, schema, fields, collection assumptions]
- Scope and exclusions: [systems, versions, known gaps]
- Framework mapping: [verified identifier, framework version, source]

## Logic

[Pseudocode or rule, including time window, grouping keys, thresholds, and field normalization.]

## Evaluation fixtures

| Fixture | Expected outcome | Reason | Observed result |
| --- | --- | --- | --- |
| Positive case | Alert | [Behavior] | Not run |
| Legitimate look-alike | No alert | [Distinguishing fact] | Not run |
| Missing field / partial data | [Defined handling] | [Assumption] | Not run |

## Tuning and rollout

[False-positive sources, analyst triage context, performance checks, shadow mode, ownership, rollback.]

## Evidence and limits

[Rule engine version, test command, fixture revision, coverage gaps. Passing fixtures do not establish complete detection coverage.]
