---
name: wiki-sync
description: Create and maintain wiki documentation from the actual code so wiki, code and tests share one source of truth - document undocumented code, keep the rule-to-code-to-test map current, turn wiki worked examples into executable tests, and propose (never apply) business-rule changes. Use after code changes, when drift-check reports UNTESTED/UNDOCUMENTED, or when asked to update docs.
---

# wiki-sync

Principle: **the wiki owns the *rules*, the code owns the *mechanics*.** You may freely document mechanics. You may only *propose* rule changes.

## Triggers
- After a code change: `git diff` (or the PR diff) touches `src/wattwise/`.
- `drift-check` reports `UNTESTED`, `UNDOCUMENTED`, or wiki sections missing from the registry.

## 1. Map
- For each changed or flagged symbol, find its rule in `tools/drift-check/rules.json`.
- Missing mapping: add it (`code`, `tests`, `examples`, `depends_on`). Rule ids are `<Page>#<heading-slug>`.

## 2. Document mechanics (allowed edits)
- `wiki/Architecture.md` and `wiki/Glossary.md`: update module tables, data flow and terms to match the code.
- New code with business meaning and no rule: draft `wiki/_proposals/<Page>#<slug>.md` describing what the code *does*, with a worked example computed by actually running the code. Mark it `Status: draft, needs PO sign-off`. Never present the code's behaviour as the intended rule without sign-off.

## 3. Make the wiki executable
- For every wiki worked example without a test, add one to `tests/test_wiki_examples.py`, parametrised and tagged with the rule id in a comment.
- These tests must use the wiki's numbers verbatim. If one fails, **do not change the expectation**: that is drift, so hand it to `drift-check`/`fix-bug`.

## 4. Rule changes (propose only)
- If code intentionally changed a rule (approved per CHANGELOG/ticket), write `wiki/_proposals/<rule-id>.md` with: current wiki text, proposed text, evidence (ticket, commit), affected examples with recomputed numbers.

## 5. Verify and report
- `python -m pytest`, the drift check and `python tools/wikiguard_lint.py --repo .` all pass: every new or changed wiki page, data file and module is registered in `rules.json` `inventory`.
- Summarise in `reports/wiki-sync.md`: docs updated, tests added, proposals awaiting sign-off.

## Never
- Paraphrase a rule in a way that changes its meaning, or "document the bug" (describe buggy code as the rule).
- Remove the *why* from a rule. Keep the reasons the wiki gives.
