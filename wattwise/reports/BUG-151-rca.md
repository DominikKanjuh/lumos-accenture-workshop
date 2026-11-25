# BUG-151 RCA: Comfort bill jumped far more than consumption (tiers priced on whole consumption)

## 1. Triage

**Facts**
- C-1002 (WattWise Comfort): Oct 240 kWh → energy 71.76 EUR; Nov 260 kWh → energy 95.94 EUR. Consumption +8.3%, energy line +33.7%.
- 240 × 0.2990 = 71.76 and 260 × 0.3690 = 95.94 → in November the **whole** consumption was priced at the upper tier.
- Ticket totals (102.89 / 131.08) predate BUG-158. With BUG-158 fixed the current totals are 103.47 / 131.66. The energy lines are the same.

**Claims (hypotheses)**
- Customer: "you only pay the higher price for what you use above your allowance". Confirmed by the wiki (below).
- CS agent: C-1003 (HeatPump) "looks too high as well". Confirmed: 910 kWh (Oct) and 1,220 kWh (Nov) are both above the first tier limit.

**Drift check (before)**: `Tariffs#how-tiered-prices-work` = **DRIFT** (0/4 examples):
- `energy_charge(COMFORT, 260)` wiki 78.44, code 95.94
- `energy_charge(HEATPUMP, 1220)` wiki 337.18, code 389.18
- `max_step('COMFORT')` wiki 0.37, code 17.87 (going from 250 → 251 kWh adds 17.87 EUR)
- `max_step('HEATPUMP')` wiki 0.32, code 40.32

## 2. Reproduce

```
$ .venv/bin/python -m wattwise invoice C-1002 2026-11
Base fee (30 days)                    14.70 EUR
Energy (260 kWh)                      95.94 EUR
Net                                  110.64 EUR
VAT 19%                               21.02 EUR
Total                                131.66 EUR
$ .venv/bin/python -m wattwise invoice C-1002 2026-10
Energy (240 kWh)                      71.76 EUR
Total                                103.47 EUR
```

## 3. Root cause

**Wiki says** (`wiki/Tariffs.md#how-tiered-prices-work`):
> Tiers work like **income tax brackets**: each tier's price applies only to the kWh that fall **inside that tier**. A customer who goes over a tier limit pays the higher price only for the kWh above the limit, never for their whole consumption.
> Comfort, 260 kWh: 250 × 0.2990 = 74.75 + 10 × 0.3690 = 3.69 → **78.44**
> HeatPump, 1,220 kWh: 99.60 + 167.40 + 70.18 → **337.18**
> Round the energy charge to cents **once**, after adding up all tiers.

**Code does** (`src/wattwise/tariff.py:101-103`, before the fix): finds the first tier whose limit is ≥ kWh and returns `round_eur(kwh × that tier's price)`. So the whole consumption is priced at the highest tier reached (a "cliff" tariff). This breaks the wiki rule and guideline N5 (+1 kWh never costs more than the top unit price). The tier data in `TARIFFS` is correct. Only the algorithm is wrong.

**Why tests missed it**
- `test_tariff.py` tested tiered tariffs only at or below the first limit (200 and 250 kWh). There the cliff and bracket formulas give the same result.
- `rules.json` mapped only those two tests. Neither wiki worked example was a test (Q1 violated).
- `test_wikiguard.py::test_energy_charge_is_continuous_in_consumption` (the N5 invariant) already failed, but it came with the WikiGuard install and nobody had acted on it.

**Blast radius**: every customer on a tiered tariff (COMFORT, HEATPUMP) in any month where consumption is above the first tier limit. They are **overbilled**. BASIC (flat) is not affected. Comfort ≤ 250 kWh and HeatPump ≤ 400 kWh are not affected. Re-billed all customers for all months in `data/`:

| Month | Customer | Tariff | kWh | Energy | Net | Gross | Δ gross EUR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10 | C-1003 | HEATPUMP | 910 | 253.89 → 241.89 | 274.17 → 262.17 | 326.26 → 311.98 | −14.28 |
| 2026-11 | C-1002 | COMFORT | 260 | 95.94 → 78.44 | 110.64 → 93.14 | 131.66 → 110.84 | −20.82 |
| 2026-11 | C-1003 | HEATPUMP | 1220 | 389.18 → 337.18 | 408.81 → 356.81 | 486.48 → 424.60 | −61.88 |

Unaffected: C-1001, C-1004 (BASIC), C-1005 (COMFORT, 210/235 kWh), C-1002 Oct (240 kWh).
Total overbilled (gross) in data/: **96.98 EUR**, across 2 customers and 3 invoices. In production, every tiered invoice above the first limit since 1.4.0 (FEAT-117, the tier refactor) is likely affected. **Corrected invoices / refunds are needed (C1, C4).**

## 4. Failing regression tests

Added to `tests/test_tariff.py` (the wiki examples, used unchanged):
- `test_energy_charge_comfort_prices_only_kwh_above_limit_at_higher_tier` (260 → 78.44)
- `test_energy_charge_heatpump_prices_each_tier_separately` (1220 → 337.18)
- `test_energy_charge_comfort_one_kwh_above_limit_costs_top_price_only` (251 → 75.12, boundary)

Before the fix:
```
E       AssertionError: assert Decimal('95.94') == Decimal('78.44')
E       AssertionError: assert Decimal('389.18') == Decimal('337.18')
E       AssertionError: assert Decimal('92.62') == Decimal('75.12')
FAILED tests/test_tariff.py::test_energy_charge_comfort_prices_only_kwh_above_limit_at_higher_tier
FAILED tests/test_tariff.py::test_energy_charge_heatpump_prices_each_tier_separately
FAILED tests/test_tariff.py::test_energy_charge_comfort_one_kwh_above_limit_costs_top_price_only
3 failed, 13 passed
```
They fail for the right reason: the whole consumption is priced at the top tier reached (260 × 0.369, 1220 × 0.319, 251 × 0.369).

## 5. Human gate

- Root cause: `tariff.energy_charge` prices all kWh at the highest tier reached instead of pricing each tier's share separately.
- Wiki: Tariffs#how-tiered-prices-work, "each tier's price applies only to the kWh that fall inside that tier", with two worked examples. The wiki is explicit, matches the marketing promise and N5. Code and wiki are not both plausible.
- Proposed fix: sum `(kWh inside tier) × tier price` over all tiers and round once with `round_eur`. Change only `tariff.energy_charge`, no data changes.
- Blast radius: C-1002 Nov, C-1003 Oct + Nov, −96.98 EUR gross total (customers were overcharged).

STATUS: approved by PO (pre-approved run)

## 6. Fix

`src/wattwise/tariff.py` `energy_charge`: walks the tiers in order, adds `(min(kwh, up_to_kwh) − previous limit) × price` as Decimal, and stops at the tier that contains `kwh` (or the open-ended tier). Rounds once via `round_eur`. The validation and exceptions stay as they were. No float, no special cases.

## 7. Verify

- New tests: green (3/3). `test_wikiguard.py::test_energy_charge_is_continuous_in_consumption[COMFORT|HEATPUMP]` and `test_wiki_and_code_are_in_sync` now pass.
- `pytest`: 62 passed, 1 failed. The remaining failure is `test_wikiguard_lint_has_no_errors`: 3 E1 errors in `tariff.py` (built-in `ValueError`/`AssertionError`). They were there before and are unchanged (only the line numbers moved). Replacing `ValueError` would break `test_energy_charge_rejects_negative_consumption` (`pytest.raises(ValueError)`), which we may not rewrite. This is out of scope and left for a separate ticket.
- Drift: `Tariffs#how-tiered-prices-work` IN SYNC (4/4). Summary 11 IN SYNC, 0 DRIFT.
- Lint: 3 errors before / 3 after (same ones), 15 warnings before / 15 after.
- Reproduction: C-1002 2026-11 → `Energy (260 kWh) 78.44`, Net 93.14, VAT 17.70, Total 110.84. Energy +9.3% vs Oct for +8.3% kWh, in line with the product sheet.
- Before/after diff (all customers, both months): only the 3 invoices in §3 changed, and only in energy/net/VAT/gross. Base fees are identical and no other invoice changed.

## 8. Independent review

`reviewer` subagent (fresh context): **APPROVE**, no blockers or majors. It ran the old function from a copy outside the repo and got 95.94 / 389.18 / 92.62, so all 3 new tests fail without the fix. It also compared the new function with an independent bracket calculation for 0–3000 kWh on every tariff: 0 differences, and N5 holds.
Findings and what was done:
- minor: the `energy_charge` docstring had no `Raises:` section → added (ValueError, AssertionError).
- minor: §8 was a placeholder → this section.
- minor: the PO approval is asserted by the agent → the run instructions said the PO pre-approved this run. A human still reviews and merges.
- nit: `reports/BUG-151-agent-output.md` is an empty untracked file. It was there before this run and is not part of this change. Left for a human.
- nit: `AssertionError` only fires when consumption is above every capped tier. Same behaviour as before, so no change.
- Follow-ups: corrected invoices (C1/C4, see the PR body). A separate ticket for the E1 lint errors in `tariff.py`.

## 9. Package

- `CHANGELOG.md` (Unreleased): `fix: tiered tariffs charge each tier's price only for the kWh inside that tier, not for the whole consumption (BUG-151)`
- Ticket status: `Fixed (pending review)`
- `rules.json` tests for `Tariffs#how-tiered-prices-work`: added the 3 new tests + `test_wikiguard.py::test_energy_charge_is_continuous_in_consumption`
- Commit message: `reports/BUG-151-commit-msg.txt` (not committed, a human reviews and merges)

### PR body (draft)

**fix(tariff): price each tier only for the kWh inside it (BUG-151)**

- **Ticket:** BUG-151. A Comfort customer's bill rose 27% for 8% more consumption.
- **Root cause:** `tariff.energy_charge` priced the whole consumption at the highest tier reached. Wiki rule Tariffs#how-tiered-prices-work requires bracket pricing (like income tax). Going one kWh over a limit made the bill jump (Comfort 250→251 kWh: +17.87 EUR).
- **Fix:** sum each tier's share × its price and round once via `round_eur`. Only `tariff.py` changed.
- **Tests:** wiki examples Comfort 260 → 78.44 and HeatPump 1220 → 337.18, plus boundary 251 → 75.12. All failed before the fix and pass after. The N5 continuity invariant and the drift-sync test now pass. The only remaining failure is the E1 lint errors in `tariff.py`, which were already there.
- **Drift:** how-tiered-prices-work → IN SYNC. 0 DRIFT overall.
- **Blast radius:** COMFORT > 250 kWh and HEATPUMP > 400 kWh, every month since 1.4.0 (FEAT-117). Customers were overbilled.
- **Customers needing corrected invoices (data/):** C-1002 2026-11 (−20.82 EUR gross), C-1003 2026-10 (−14.28), C-1003 2026-11 (−61.88). Total refund 96.98 EUR gross. Production months before 2026-10 need re-billing too (C4).
