# BUG-142 RCA: November billing run fails for C-1004 (register rollover)

## 1. Triage

**Facts**
- `python -m wattwise run 2026-11` raises `InvalidReadingError: Meter M-20004: reading decreased from 99870 to 95` from `meter.consumption_kwh` and aborts (exit 1); only 3 of 5 invoices printed, C-1005 never billed.
- `data/readings.csv`: M-20004 (5 digits) 2026-10-01 = 99640, 2026-11-01 = 99870, 2026-12-01 = 95.
- Customer photo shows `00095` → reading is valid.

**Claims (hypotheses, not facts)**
- "Nobody touched the code" — irrelevant; the defect is latent and only triggers on the first rollover in the data.
- Implied "reading must be wrong" — refuted: wiki says a lower closing reading means rollover.

**Drift check (before)**: `Meter-Readings#register-rollover` = **DRIFT** (0/3 examples), `tests: NONE`:
- `consumption(5, 99870, 95)` wiki 225, code raises InvalidReadingError
- `consumption(6, 999900, 100)` wiki 200, code raises
- `consumption(5, 50000, 100)` wiki ImplausibleConsumptionError, code raises InvalidReadingError

Other DRIFT findings (`Billing-Rules#billing-period`, `Tariffs#how-tiered-prices-work`) belong to BUG-158 / BUG-151 — out of scope, left alone.

## 2. Reproduce

```
$ .venv/bin/python -m wattwise run 2026-11 ; echo $?
... (C-1001, C-1002, C-1003 invoices)
wattwise.errors.InvalidReadingError: Meter M-20004: reading decreased from 99870 to 95
1
```

## 3. Root cause

**Wiki says** (`wiki/Meter-Readings.md#register-rollover`):
> **A closing reading that is lower than the opening reading means the register rolled over.**
> `consumption = (max value − opening reading) + closing reading + 1 = 10^digits − opening reading + closing reading`
> Example, 5-digit meter: opening 99870, closing 00095 → `(99999 − 99870) + 95 + 1 = 225 kWh`.
> A rolled-over reading must go through the plausibility check below like any other.

**Code does** (`src/wattwise/meter.py:49-54`): `delta = current.value - previous.value`; if `delta < 0` → `raise InvalidReadingError("reading decreased ...")`. Treats every decrease as invalid; never applies the wrap formula (violates guideline N4). Rollover cases also skip the plausibility check.

**Why tests missed it**: no test covered a decreasing reading; `rules.json` listed `tests: []` for `Meter-Readings#register-rollover`. Every existing test used monotonic readings. (`test_wikiguard.py::test_consumption_kwh_handles_register_rollover` was added with the WikiGuard install and already fails.)

**Secondary finding (not fixed here)**: `cli.py` batch `run` calls `bill_customer` without per-customer error isolation, so one failure aborts the whole run (guideline C2). The web dashboard already isolates via `service.billing_result`. Fixing it touches `cli.py`, which is outside the domain modules; recommend a separate ticket.

**Blast radius** (re-billed all customers × all months in `data/`: 2026-10, 2026-11):
- Only meter that rolls over in data: M-20004 in 2026-11. 
- Affected: **C-1004 (Paul Hoffmann), 2026-11** — no invoice issued (billing failed). Batch side effect: **C-1005, 2026-11** not invoiced via CLI run (its own amount unaffected, 100.53 EUR at current code).
- No previously issued invoice was wrong → no corrections needed, only the missing C-1004 invoice (and C-1005 if the CLI run was the issuing path).
- C-1004 2026-11 after fix: 225 kWh, Base fee 9.44, Energy 77.63, total **103.61 EUR** (base fee still uses the 29-day count from BUG-158; once BUG-158 is fixed it becomes 30 days / 9.76 EUR).

## 4. Failing regression tests

Added to `tests/test_meter.py` (wiki examples verbatim):
- `test_consumption_kwh_handles_register_rollover` (5 digits, 99870 → 95 = 225)
- `test_consumption_kwh_handles_register_rollover_six_digits` (999900 → 100 = 200)
- `test_consumption_kwh_flags_implausible_rollover` (50000 → 100 = 50100 kWh > 6000 → ImplausibleConsumptionError)

Before fix:
```
E           wattwise.errors.InvalidReadingError: Meter M-1: reading decreased from 50000 to 100
src/wattwise/meter.py:51: InvalidReadingError
FAILED tests/test_meter.py::test_consumption_kwh_handles_register_rollover - ...
FAILED tests/test_meter.py::test_consumption_kwh_handles_register_rollover_six_digits
FAILED tests/test_meter.py::test_consumption_kwh_flags_implausible_rollover
3 failed, 6 passed
```
All three fail with `InvalidReadingError` from the `delta < 0` branch — the right reason.

## 5. Human gate

- Root cause: `meter.consumption_kwh` rejects lower closing readings instead of applying the rollover rule.
- Wiki: `Meter-Readings#register-rollover` (quoted above). Code and wiki are not both plausible: wiki is explicit, data confirmed by customer photo.
- Proposed fix: in `meter.py`, when `delta < 0`, `delta += 10**meter.digits` (= `max_value + 1`); plausibility check then applies unchanged. No other modules.
- Blast radius: C-1004 2026-11 (missing invoice, 103.61 EUR), C-1005 2026-11 blocked in CLI batch.

STATUS: approved by PO (pre-approved run)

## 6. Fix

`src/wattwise/meter.py` `consumption_kwh`: the `delta < 0` branch no longer raises; it adds `meter.max_value + 1` (= `10^digits`) to the delta, per the wiki formula. The result then flows through the existing plausibility check unchanged. Integer arithmetic only; no other module touched.

## 7. Verify

- New tests: 3/3 green. `test_wikiguard.py::test_consumption_kwh_handles_register_rollover[*]` (pre-existing, failing before): 2/2 green now.
- Full suite: **not fully green** — 45 passed, 11 failed (was 40 passed, 13 failed). All 11 remaining failures belong to other tickets and were failing before this change: `billing_period_days_*` / `base_fee_over_calendar_year_*` (BUG-158, billing-period off-by-one), `energy_charge_is_continuous_*` (BUG-151, tiered pricing), and the aggregate `wikiguard_lint_has_no_errors` / `wiki_and_code_are_in_sync` (fail on those same rules + tariff.py E1 errors). Left alone per run notes.
- Drift check: `Meter-Readings#register-rollover` **IN SYNC (3/3 examples)**. Summary 6→7 IN SYNC, 5→4 DRIFT.
- `wikiguard_lint.py`: errors 3→3 (all pre-existing in `tariff.py`, E1), warnings 18→17 (removed "register-rollover: rule has no test"). No new findings.
- Reproduction: `python -m wattwise run 2026-11` exit 0, 5/5 invoices printed.
- Before/after billing diff, all customers × {2026-10, 2026-11}: only change is
  ```
  < 2026-11 C-1004 InvalidReadingError: Meter M-20004: reading decreased from 99870 to 95
  > 2026-11 C-1004 103.61 [('Base fee (29 days)', '9.44'), ('Energy (225 kWh)', '77.63')]
  ```
  No unintended changes.

## 8. Independent review

`reviewer` subagent (fresh context): **APPROVE, no blocking findings.** Independently confirmed the 3 new tests fail without the meter.py change and pass with it; existing tests only appended to; no wiki/data edits; rule IN SYNC.
- Nit (not applied): `consumption_kwh` docstring could mention rollover. Left as-is to keep the diff minimal.
- Follow-up: separate ticket for CLI batch isolation (C2) in `cli.py` — any remaining `BillingError` (e.g. an implausible "rollover" from a meter swap) still aborts `wattwise run`.

## 9. Package

- `CHANGELOG.md` Unreleased: `fix: meter register rollover is billed as consumption instead of rejecting the reading (BUG-142)`
- Ticket status: `Fixed (pending review)`
- `rules.json` `Meter-Readings#register-rollover.tests`: the 3 new tests
- Commit message: `reports/BUG-142-commit-msg.txt` (not committed, per run notes)

### PR body (draft)

**Ticket:** BUG-142 — November billing run fails for C-1004, batch aborts.

**Root cause:** `meter.consumption_kwh` (`src/wattwise/meter.py`) raised `InvalidReadingError` for any closing reading lower than the opening reading. Wiki `Meter-Readings#register-rollover` says that is a register rollover: `consumption = 10^digits − opening + closing`, then plausibility check. M-20004 rolled over 99870 → 00095 on 2026-12-01.

**Fix:** on negative delta add `meter.max_value + 1` (= 10^digits); plausibility check unchanged. One domain module, no special cases.

**Tests:** `test_consumption_kwh_handles_register_rollover` (225), `..._six_digits` (200), `test_consumption_kwh_flags_implausible_rollover`. Fail before, pass after. Also turns pre-existing `test_wikiguard.py::test_consumption_kwh_handles_register_rollover[*]` green. Suite: 45 passed / 11 failed — all 11 pre-existing, owned by BUG-151/BUG-158.

**Blast radius / customers needing invoices:**
| Customer | Month | Before | After |
|---|---|---|---|
| C-1004 Paul Hoffmann | 2026-11 | Billing failed (no invoice) | 225 kWh, 103.61 EUR gross |
| C-1005 Mia Fischer | 2026-11 | Not invoiced by CLI batch (aborted) | unchanged amount, 100.53 EUR |

No issued invoice was wrong; no corrections, only the missing invoices. Note: November base fees also depend on BUG-158 (29 vs 30 days) — amounts will change again when that lands.

**Follow-up:** new ticket for C2 batch failure isolation in `cli.py run`.
