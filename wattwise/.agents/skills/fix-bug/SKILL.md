---
name: fix-bug
description: Resolve a bug ticket from issues/ by grounding it in the wiki business rules - reproduce, find the root cause, write a failing regression test, get human approval, fix, verify and package a reviewable change. Use when asked to fix or investigate a BUG-<id> ticket.
---

# fix-bug

Input: a ticket id (e.g. `BUG-142`). Work in this exact order. Write your findings to `reports/<ticket>-rca.md` as you go; that file is the audit trail a human reviews.

## 1. Triage
- Read `issues/<ticket>-*.md`. Separate **facts** (observed output, data) from **claims** (reporter's guesses).
- Run `python tools/drift-check/drift_check.py --repo .` and note any DRIFT finding related to this ticket.

## 2. Reproduce
- Run the ticket's CLI steps and capture the actual output.

## 3. Root cause (read-only)
- Find the governing rule in `wiki/` (use `tools/drift-check/rules.json` to map rule → code → tests).
- Trace the symptom to the **cause**: the code that contradicts the rule. It is often not where the symptom shows.
- Record in the RCA: `Wiki says` (quote + file#section) · `Code does` (file:line) · `Why tests missed it`.
- Blast radius: which other customers or months the same cause affects. Re-bill all customers for all months in `data/` and list the ones affected, with EUR amounts.

## 4. Failing regression test
- Add a test using the wiki's worked example as the expected value. Follow CONTRIBUTING (ticket comment, hand calculation, naming).
- Run it and **confirm it fails** for the right reason. Paste the failure into the RCA.

## 5. Human gate
- Stop and present: root cause, wiki quote, proposed fix, blast radius. Wait for approval.
- In headless mode with no human, write `STATUS: awaiting approval` in the RCA and stop.
- If code and wiki seem *both* plausible, do **not** pick one. Escalate with a proposal in `wiki/_proposals/`.

## 6. Minimal fix
- Change only the domain module(s) at fault. No special cases, no float, `round_eur` only, domain exceptions.

## 7. Verify
- New test is green, `python -m pytest` is fully green, the drift check shows this rule `IN SYNC`, and `python tools/wikiguard_lint.py --repo .` has no new errors.
- Re-run the ticket's reproduction steps; the expected result from the ticket holds.
- Before/after billing diff for all customers, so there are no unintended changes.

## 8. Independent review
- Use a fresh context (the `reviewer` subagent if available) to check the diff against CONTRIBUTING's Definition of Done and the wiki rule. Fix or escalate on findings.

## 9. Package (never merge)
- `CHANGELOG.md` line under Unreleased, set the ticket status to `Fixed (pending review)`, update `rules.json` tests for the rule.
- Draft a Conventional Commit message and a PR body (ticket, root cause, fix, tests, blast radius, customers needing corrected invoices) in the RCA.
