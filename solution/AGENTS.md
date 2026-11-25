# AGENTS.md — WattWise Billing

Instructions for AI coding agents. Humans: see README.md and CONTRIBUTING.md.

## Commands

```bash
python -m pip install -e ".[dev]"                        # setup
python -m pytest                                          # full suite (must stay green)
python tools/drift-check/drift_check.py --repo .          # wiki ↔ code drift report (exit 1 = drift)
python -m wattwise invoice C-1001 2026-11                 # one invoice
python -m wattwise run 2026-11                            # batch run, all customers
```

## Source of truth (non-negotiable)

1. **`wiki/` is the truth for business rules** (`Billing-Rules.md`, `Tariffs.md`, `Meter-Readings.md`). When code and wiki disagree, **the code is wrong**.
2. Worked examples in the wiki are **expected values**: use them in tests verbatim.
3. Green tests ≠ correct. The existing suite misses rule violations; check against the wiki, not just pytest.
4. Bug reports describe symptoms; reporters' guesses ("the calculation is fine") are hypotheses, not facts.
5. The rule ↔ code ↔ test map lives in `tools/drift-check/rules.json`. Keep it current.

## Boundaries

- **Never** edit business-rule text in `wiki/Billing-Rules.md`, `wiki/Tariffs.md` or `wiki/Meter-Readings.md`. If you think a rule is wrong, write a proposal to `wiki/_proposals/<rule-id>.md` for product-owner sign-off.
- **Never** edit `data/`: the readings are correct.
- **Never** weaken, delete or rewrite existing tests. Add new ones only.
- **Never** special-case a customer or meter id. Fix the cause in the domain modules (`models`, `meter`, `tariff`, `billing`), never in `web.py`, `views.py` or `cli.py`.
- No `float` for money, no `round()`/`quantize()`: use `Decimal` and `money.round_eur`. No new dependencies.
- **Never** merge or mark a ticket closed. The furthest you go is `Fixed (pending review)`; a human approves.
- If you are unsure which side (code or wiki) is right, **stop and ask**. Escalating is a valid outcome.

These are enforced by `.claude/settings.json` hooks (`tools/guard.py`); other tools: treat them as hard rules.

## Workflows (skills in `.agents/skills/`)

| Task                                 | Skill                                                                                                       |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| Fix a bug ticket from `issues/`      | `fix-bug`: reproduce → root cause vs wiki → failing test → **human gate** → fix → verify → review → package |
| Check wiki ↔ code consistency        | `drift-check`: run checker, triage each finding (code wrong / wiki stale / untested / undocumented)         |
| Create or update wiki docs from code | `wiki-sync`: document undocumented code, keep the rule map current, turn wiki examples into tests           |

## No orphans: everything is registered

Every file in `wiki/` and `data/` and every module in `src/wattwise/`, new or old, must be registered in `tools/drift-check/rules.json` (`inventory`, `rules`) and cross-referenced: rule pages ↔ code ↔ tests, data files ↔ reader module ↔ wiki page ↔ schema, modules ↔ `wiki/Architecture.md`, pages ↔ `wiki/Home.md`. Adding or renaming any of these means updating the registry in the same change. Check with `python tools/wikiguard_lint.py --repo .`.

## Company engineering guidelines (not in the wiki; rationale in GUIDELINES.md)

- **Customer first:** C1 what we promise is what we bill · C2 one failing customer never blocks others (isolate batch failures) · C3 in doubt, hold and escalate, never guess · C4 list _all_ affected customers for corrections · C5 every invoice line traceable to a rule ID.
- **Numbers:** N1 no float for money/energy (Decimal or integer minor units) · N2 round once, only via `round_eur` · N3 no overflow: unbounded/64-bit integers for counters, sums, IDs (BigInt/long/BIGINT elsewhere), range-check at boundaries · N4 physical counters wrap at `10^digits`; never assume monotonic · N5 price is continuous: +1 kWh never costs more than the top unit price · N6 units in names.
- **Time:** T1 periods inclusive (`end - start + 1`) · T2 no hard-coded month/year lengths · T3 no clock reads in domain logic; Europe/Berlin and DST-aware.
- **Quality:** Q1 every wiki example is an executable test · Q2 test boundaries and invariants · Q3 regression test per bug · Q4 automatic reconciliation of totals.
- **Errors:** E1 domain exceptions naming entity and values · E2 validate at boundaries, pure domain · E3 failures reported as data with reason.
- **Knowledge:** K1 wiki owns rules, code owns mechanics · K2 every rule mapped to code and tests, no orphans · K3 rule changes only via `wiki/_proposals/` + PO sign-off · K4 keep the _why_ · K5 every fixed ticket has a CHANGELOG line (Unreleased, with ticket id) and vice versa.
- **Privacy/security:** P1 meter data is personal (GDPR): minimise and pseudonymise · P2 no customer data to external AI without a DPA · P3 no new dependencies or secrets.
- **AI agents:** A1 follow this file; hooks enforce it · A2 humans approve, agents propose · A3 log every action, write an RCA · A4 escalating is a success.

## Conventions (full list: CONTRIBUTING.md)

- Python 3.10+, full type hints, Google-style docstrings (`Args:`, `Returns:`, `Raises:`).
- Raise domain exceptions from `wattwise/errors.py`; messages name the entity and the offending values.
- Bug fix ⇒ regression test that fails without the fix, `# Regression test for BUG-<id>` above it, hand calculation in a comment, name `test_<function>_<expected behaviour>`.
- `CHANGELOG.md` line under **Unreleased** with the ticket id.
- Conventional Commits ending in the ticket id: `fix(meter): handle register rollover (BUG-142)`. One ticket per PR.
