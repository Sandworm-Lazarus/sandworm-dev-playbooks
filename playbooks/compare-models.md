# Compare models fairly

**Purpose:** evaluate models for a specific workload without confusing price, speed, and answer quality. This is an original Sandworm Arsenal workflow.

**โจทย์:** เลือกโมเดลให้ตรงงาน ด้วยชุดทดสอบเดียวกันและต้นทุนที่ตรวจสอบได้

## Inputs

- Representative tasks and acceptance criteria.
- Exact model identifiers, provider or local runtime, and revisions where available.
- Budget, latency requirements, and tool/context constraints.
- Current price evidence or measured local resource cost.

## Procedure

1. Freeze a task set representative of the intended work. Keep tuning examples separate from evaluation examples and use no private data unless its handling is authorized.
2. Define quality checks before generating answers. Prefer observable outcomes: tests passing, valid structured output, grounded citations, or a human rubric with explicit criteria.
3. Record prompts, system instructions, tool access, sampling settings, reasoning settings, context limits, concurrency, and hardware. Use comparable settings; document any differences that cannot be aligned.
4. Run the same tasks on each model. Retain failures, timeouts, refusals, and retries. Repeat enough trials for the intended decision and report sample size rather than implying certainty from one run.
5. Measure quality, end-to-end latency, token usage, and billed cost separately. Distinguish provider-side speed from tool and network time when the measurements permit it.
6. Price input, output, cache writes, and cache reads according to the provider's current billing rules. Include tools or hosted jobs when relevant. A subscription quota is not automatically a per-token price.
7. Compare quality-qualified options against the actual budget and latency constraints. If using weighted scores, show normalization, weights, and missing-data handling. Unknown values remain unknown.

## Output contract

| Model / revision | Passed / attempted | Latency p50 / p95 | Total cost | Cost per passed task | Conditions / missing data |
| --- | --- | --- | --- | --- | --- |
| Populate from measurements | Include failures | State sample size | Measured or clearly estimated | Total cost ÷ passed tasks | Include provider, settings, retries |

When there are zero passed tasks, cost per passed task is undefined; do not divide by zero or report zero cost. With very small samples, list individual latency values and avoid presenting tail percentiles as stable estimates.

## Worked example — synthetic

Model A passes 8 of 10 tasks at a total cost of $0.40. Model B passes 9 of 10 at $0.90. The observed cost per passed task is $0.05 for A and $0.10 for B. If the acceptance threshold is 9 of 10, only B qualifies in this illustrative run. If both meet the workload's requirement, cost and latency can inform the choice. Ten tasks alone do not establish broad model superiority.

## Task prompt

> Compare these models for the supplied tasks and constraints using this playbook. Prepare a reproducible evaluation plan first. Keep measured results, external benchmark claims, and estimates separate; leave missing prices or capabilities unknown.
