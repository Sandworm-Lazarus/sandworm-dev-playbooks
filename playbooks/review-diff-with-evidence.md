# Review a diff with evidence

**Purpose:** review a code change and produce findings that another developer can verify. This is an original Sandworm Arsenal workflow.

**โจทย์:** ตรวจบั๊กและความเสี่ยงที่เกิดจากการแก้โค้ด โดยแยกสิ่งที่พิสูจน์ได้ออกจากข้อสงสัย

## Inputs

- Base and head revisions, the diff, and the behavior the change intends to introduce.
- Relevant callers, schemas, configuration, and existing tests.
- The allowed verification environment and any unavailable dependencies.

## Procedure

1. Resolve both revisions and summarize the changed behavior. Read project instructions before choosing verification commands.
2. Trace modified inputs through validation, authorization, state changes, and outputs. Read relevant unchanged callers and error paths when they affect the conclusion.
3. Write the invariants the change must preserve. For a game or transactional API, examples include ownership, atomic transfers, non-negative balances, idempotency, and consistent serialization.
4. For each suspected defect, construct a concrete trigger and expected versus actual behavior. Check whether it is introduced by the diff or already present at the base revision.
5. Inspect counterevidence: upstream validation, transaction boundaries, database constraints, retry behavior, and tests that might invalidate the suspicion.
6. Run targeted checks when the environment permits. Record the command, revision, observed output, and what that check actually establishes. If execution is unavailable, supply a reproducible test proposal and label it unrun.
7. Prioritize confirmed findings by practical impact and reachability. Keep unresolved questions separate. Suggest the smallest correction and a regression check.

## Finding format

| Field | Required content |
| --- | --- |
| Title | Concrete failure under a concrete condition |
| Location | Changed path and line, plus relevant callers |
| Trigger | Inputs, state, and preconditions |
| Evidence | Code path or observed reproduction |
| Impact | Who or what is affected; reachability assumptions |
| Correction | Minimal change and proposed verification |
| Status | Observed / supported by static inspection / unresolved |

“No findings” means no supported findings within the reviewed scope; it does not certify the whole application. Never report a test as passed without its actual result.

## Worked example — synthetic

A transfer handler checks that a balance covers an amount, then later updates the balance. The visible code does not show whether a transaction or conditional update protects the operation.

Expected response: trace the persistence helper and database constraints first. If those files are missing, report a concurrency question and propose a two-request regression test. A separate balance check alone is insufficient evidence to claim that a real double spend occurred.

## Task prompt

> Review the supplied base-to-head change using this playbook. Focus on defects introduced by the change. Give evidence-backed findings, separate unresolved questions, and state exactly which checks ran and which remain unrun.
