# BUG-158 RCA: Base fee revenue lower than planned (billing period off by one day)

## 1. Triage

**Facts**
- Invoice C-1001 (WattWise Basic, 9.90 EUR/month), 2026-11: `Billing period 01 Nov 2026 – 30 Nov 2026`, `Base fee (29 days) 9.44 EUR`.
- November has 30 days. Base fee revenue ~3% below plan every month since 1.2.0 (daily proration). 1/30 ≈ 3.3%, 1/31 ≈ 3.2% → consistent with exactly one day missing per period.

**Claims (hypotheses, not facts)**
- "Existing tests for the base fee pass, so the calculation itself might be fine": partly true. `tariff.prorated_base_fee` matches the wiki formula, but it gets the wrong day count. Passing tests don't prove correctness: no test checked `BillingPeriod.days` against the wiki.

**Drift check (before)**: `Billing-Rules#billing-period` = **DRIFT** (0/3 examples), `tests: NONE`:
- `days('2026-11-01 to 2026-11-30')` wiki 30, code 29
- `days('2026-12-01 to 2026-12-31')` wiki 31, code 30
- `days('2027-02-01 to 2027-02-28')` wiki 28, code 27

Inherited DRIFT: `Billing-Rules#invoice-layout` ('Base fee (29 days)' vs '(30 days)') and `Billing-Rules#full-example` (base 9.44 vs 9.76, net 94.66 vs 94.98, VAT 17.99 vs 18.05, total 112.65 vs 113.03).
Out of scope: `Tariffs#how-tiered-prices-work` (BUG-151), left alone.

## 2. Reproduce

```
$ .venv/bin/python -m wattwise invoice C-1001 2026-11
Period:  2026-11-01 to 2026-11-30
Base fee (29 days)                     9.44 EUR
Energy (247 kWh)                      85.22 EUR
Net                                   94.66 EUR
VAT 19%                               17.99 EUR
Total                                112.65 EUR
```

## 3. Root cause

**Wiki says** (`wiki/Billing-Rules.md#billing-period`):
> **Both `start` and `end` are billable days.** The number of billable days is therefore `end - start + 1`
> | 2026-11-01 to 2026-11-30 | 30 |

and `wiki/Billing-Rules.md#base-fee`: `9.90 × 12 / 365 × 30 = 9.7643… → 9.76 EUR`.

**Code does** (`src/wattwise/models.py:86`): `BillingPeriod.days` returns `(self.end - self.start).days`, which counts the end day as exclusive. That is one day short (violates guideline T1, periods inclusive). `service.month_period` builds the period correctly (1st to last day). `billing.create_invoice` (`billing.py:63,66`) passes `period.days` to `tariff.prorated_base_fee` and the line label. The symptom shows in the base fee, but the cause is in `models`, not `tariff`.

**Why tests missed it**
- `rules.json` listed `tests: []` for `Billing-Rules#billing-period` and `Billing-Rules#full-example`.
- `test_models.py` tested only `label()` and the end<start check, never `days`.
- `test_billing.py` checks line descriptions only by prefix (`split(" (")[0]`), and checks net/VAT only for internal consistency, never against the wiki amounts.
- `test_tariff.py` calls `prorated_base_fee` with explicit day counts, so it skips `BillingPeriod`.
- (`test_wikiguard.py::test_billing_period_days_counts_every_calendar_day` came with the WikiGuard install and already failed.)

**Blast radius**: every invoice for every customer and month is underbilled by one day of base fee. This is independent of tariff and consumption. Re-billed all customers for all months in `data/` (2026-10, 2026-11):

| Month | Customer | Tariff | Base fee | Net | Gross | Δ gross EUR |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-10 | C-1001 | BASIC | 9.76 → 10.09 | 94.29 → 94.62 | 112.21 → 112.60 | +0.39 |
| 2026-10 | C-1002 | COMFORT | 14.70 → 15.19 | 86.46 → 86.95 | 102.89 → 103.47 | +0.58 |
| 2026-10 | C-1003 | HEATPUMP | 19.63 → 20.28 | 273.52 → 274.17 | 325.49 → 326.26 | +0.77 |
| 2026-10 | C-1004 | BASIC | 9.76 → 10.09 | 89.11 → 89.44 | 106.04 → 106.43 | +0.39 |
| 2026-10 | C-1005 | COMFORT | 14.70 → 15.19 | 77.49 → 77.98 | 92.21 → 92.80 | +0.59 |
| 2026-11 | C-1001 | BASIC | 9.44 → 9.76 | 94.66 → 94.98 | 112.65 → 113.03 | +0.38 |
| 2026-11 | C-1002 | COMFORT | 14.21 → 14.70 | 110.15 → 110.64 | 131.08 → 131.66 | +0.58 |
| 2026-11 | C-1003 | HEATPUMP | 18.97 → 19.63 | 408.15 → 408.81 | 485.70 → 486.48 | +0.78 |
| 2026-11 | C-1004 | BASIC | 9.44 → 9.76 | 87.07 → 87.39 | 103.61 → 103.99 | +0.38 |
| 2026-11 | C-1005 | COMFORT | 14.21 → 14.70 | 84.48 → 84.97 | 100.53 → 101.11 | +0.58 |

Total underbilled (gross) in data/: **5.42 EUR**, all 5 customers, both months. Every month billed since 1.2.0 is affected in production. Corrected invoices need a product/finance decision (C4).
Note: the C-1002/C-1003/C-1005 energy amounts are also affected by BUG-151 (tiers). The deltas above are base-fee-only, and energy lines did not change.

## 4. Failing regression tests

Added, using the wiki examples unchanged:
- `tests/test_models.py::test_billing_period_days_includes_start_and_end` (3 rows of the wiki table)
- `tests/test_billing.py::test_create_invoice_matches_wiki_full_example` (wiki full example, 247 kWh)

Before the fix:
```
E       assert 29 == 30
E        +  where 29 = BillingPeriod(start=datetime.date(2026, 11, 1), end=datetime.date(2026, 11, 30)).days
E       assert 30 == 31
E       assert 27 == 28
E         At index 0 diff: ('Base fee (29 days)', Decimal('9.44')) != ('Base fee (30 days)', Decimal('9.76'))
FAILED tests/test_models.py::test_billing_period_days_includes_start_and_end[start0-end0-30]
FAILED tests/test_models.py::test_billing_period_days_includes_start_and_end[start1-end1-31]
FAILED tests/test_models.py::test_billing_period_days_includes_start_and_end[start2-end2-28]
FAILED tests/test_billing.py::test_create_invoice_matches_wiki_full_example
4 failed, 8 passed
```
Fails for the right reason: day count is one short. The energy line (85.22) already matches.

## 5. Human gate

- Root cause: `models.BillingPeriod.days` counts the end day as exclusive and misses it.
- Wiki: Billing-Rules#billing-period "Both `start` and `end` are billable days … `end - start + 1`". Code and wiki are not both plausible: the wiki is explicit and gives worked examples.
- Proposed fix: `return (self.end - self.start).days + 1` in `models.py`. One line, domain module only.
- Blast radius: all 5 customers, 2026-10 and 2026-11, +5.42 EUR gross total (table above).

STATUS: approved by PO (pre-approved run)

## 6. Fix

`src/wattwise/models.py:86`: `return (self.end - self.start).days + 1`. No other code changes. `service.py` still reads the closing reading on `end + 1 day` (wiki-correct). `meter.py` measures elapsed days between reading dates (unaffected).

## 7. Verify

- New tests: green (4/4).
- `pytest`: 56 passed, 4 failed. All remaining failures belong to other tickets or were already there:
  - `test_energy_charge_is_continuous_in_consumption[COMFORT|HEATPUMP]`, `test_wiki_and_code_are_in_sync` → only `Tariffs#how-tiered-prices-work` DRIFT (BUG-151).
  - `test_wikiguard_lint_has_no_errors` → 3 E1 errors in `tariff.py` (built-in ValueError/AssertionError), unchanged before/after.
  - The 7 T1 invariant tests (`test_billing_period_days_counts_every_calendar_day[*]`, `test_base_fee_over_calendar_year_equals_twelve_months[*]`) now pass.
- Drift: `Billing-Rules#billing-period` IN SYNC (3/3), `invoice-layout` IN SYNC (1/1), `full-example` IN SYNC (5/5). Summary 10 IN SYNC, 1 DRIFT (BUG-151).
- Lint: 3 errors before / 3 after (same, already there), warnings 17 → 15 (two rules now tested).
- Reproduction: `Base fee (30 days) 9.76`, Net 94.98, VAT 18.05, Total 113.03. Matches wiki/ticket expectation.
- Before/after diff (all customers, all months): only the base-fee line and the derived net/VAT/gross changed. Energy lines are identical. See table in §3.

## 8. Independent review

`reviewer` subagent (fresh context): **APPROVE**, no blockers or majors. It confirmed the new tests fail without the fix and that the other users of `BillingPeriod.days` are unaffected (`service.py`, `meter.py` and `views.py` don't use `.days`).
Findings and what was done:
- minor: no commit message → written to `reports/BUG-158-commit-msg.txt`.
- minor: `reports/BUG-158-agent-output.md` is an empty untracked file. It was there before this run and is not part of this change. Left for a human.
- minor: corrected invoices need a PO/finance decision (C4) → raised in the PR body below.
- nit: `invoice-layout` rule should also map the exact-label test → added `test_create_invoice_matches_wiki_full_example` in `rules.json`.

## 9. Package

- `CHANGELOG.md` (Unreleased): `fix: billing period counts both start and end day, so the prorated base fee covers every supplied day (BUG-158)`
- Ticket status: `Fixed (pending review)`
- `rules.json` tests: billing-period → `test_models.py::test_billing_period_days_includes_start_and_end`. full-example and invoice-layout → `test_billing.py::test_create_invoice_matches_wiki_full_example`
- Commit message: `reports/BUG-158-commit-msg.txt` (not committed, a human reviews and merges)

### PR body (draft)

**fix(models): count both start and end day in billing period (BUG-158)**

- **Ticket:** BUG-158, base fee revenue ~3% below plan.
- **Root cause:** `models.BillingPeriod.days` returned `end - start` (end day exclusive). The wiki rule Billing-Rules#billing-period requires `end - start + 1`. Every monthly invoice billed one day too little base fee.
- **Fix:** `src/wattwise/models.py:86` → `(self.end - self.start).days + 1`. One line, domain module only.
- **Tests:** `test_billing_period_days_includes_start_and_end` (wiki table 30/31/28) and `test_create_invoice_matches_wiki_full_example` (9.76 / 85.22 / 94.98 / 18.05 / 113.03). Both failed before the fix and pass after. The 7 existing T1 WikiGuard invariant tests now pass too. Remaining failures belong to BUG-151 or are lint errors in `tariff.py` that were already there.
- **Drift:** billing-period, invoice-layout, full-example → IN SYNC.
- **Blast radius:** all customers and all months since 1.2.0. Only the base-fee line changes, energy is unchanged.
- **Customers needing corrected invoices (data/):** C-1001 (+0.39 Oct, +0.38 Nov), C-1002 (+0.58, +0.58), C-1003 (+0.77, +0.78), C-1004 (+0.39, +0.38), C-1005 (+0.59, +0.58) EUR gross. Total 5.42 EUR. **PO/finance decision needed** on whether to issue corrections (C4).
