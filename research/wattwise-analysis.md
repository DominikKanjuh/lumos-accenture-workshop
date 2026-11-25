# WattWise Billing — Ground-Truth Analysis

Scope: `wattwise/` (v1.4.0, Python 3.10+, zero runtime deps). Nothing in `wattwise/` was modified.
Baseline: `python -m pytest` → **39 passed** (all three bugs ship with a green suite).
All numbers below come from actually running the CLI and from an out-of-tree script that monkeypatched each fix in-process (`scratchpad/quant.py`).

---

## 1. Architecture, conventions, workflow

### 1.1 Modules & data flow

```
data/customers.json ─┐
data/readings.csv  ──┴─> repository.DataRepository ──> service.bill_customer / billing_result / billing_overview
                                                              │       (month_period(), previous_month(), available_months())
                                                              v
                                                   billing.create_invoice()
                                       ┌──────────────────┼──────────────────────┐
                                       v                  v                      v
                           meter.consumption_kwh()  tariff.energy_charge()   money.round_eur()
                                                    tariff.prorated_base_fee()
                                                              ^
                                       models.BillingPeriod.days ── feeds base fee + line label
UI:  web.route() (pure) -> views.render_* (pure HTML)      CLI: cli.main -> format_invoice
```

| Module | Role | Notes |
| --- | --- | --- |
| `models.py` | Frozen dataclasses `Meter`(digits 5/6, `max_value`), `MeterReading`, `Customer`, `BillingPeriod`(`days`, `label`) | **BUG-158 lives here** |
| `meter.py` | `consumption_kwh`: validate, order check, delta, plausibility (200 kWh/day) | **BUG-142 lives here** |
| `tariff.py` | `TARIFFS` (BASIC/COMFORT/HEATPUMP), `Tier(up_to_kwh, price)`, `energy_charge`, `prorated_base_fee` | **BUG-151 lives here** |
| `billing.py` | `create_invoice`: 2 lines, net = sum, VAT 19% on net, gross | correct |
| `money.py` | `round_eur` (HALF_UP to cents) — only allowed rounding | correct |
| `errors.py` | `BillingError` ← `InvalidPeriodError`, `InvalidReadingError`, `ImplausibleConsumptionError`, `UnknownTariffError` | |
| `repository.py` | Loads JSON/CSV; `reading()` raises `InvalidReadingError`, `find_reading()` returns None | |
| `service.py` | `month_period` (calendar month, end = last day), `bill_customer` (opening on start, closing on end+1), `billing_result` (catches `BillingError` for UI) | |
| `web.py` / `views.py` | stdlib http.server, `route()` pure; dashboard + invoice page w/ month-on-month comparison | no business logic allowed |
| `cli.py` | `serve`, `invoice <id> <YYYY-MM>`, `run <YYYY-MM>` | `run` has no error handling |

Sample data: 5 customers, readings on 2026-10-01, 11-01, 12-01 → billable months **Oct and Nov 2026 only**.

| Cust | Name | Tariff | Meter (digits) | Oct kWh | Nov kWh |
| --- | --- | --- | --- | --- | --- |
| C-1001 | Anna Becker | BASIC | M-20001 (5) | 245 | 247 |
| C-1002 | Jonas Schmidt | COMFORT | M-20002 (5) | 240 | 260 |
| C-1003 | Lea Wagner | HEATPUMP | M-20003 (6) | 910 | 1220 |
| C-1004 | Paul Hoffmann | BASIC | M-20004 (5) | 230 | 99870→95 (rollover, 225) |
| C-1005 | Mia Fischer | COMFORT | M-20005 (6) | 210 | 235 |

Note: the wiki examples are **golden values that exactly match the sample data**: Billing-Rules full example (Basic, Nov, 247 kWh → 113.03) = C-1001 Nov; Tariffs examples (Comfort 260 → 78.44, HeatPump 1220 → 337.18) = C-1002/C-1003 Nov; Meter-Readings rollover example (99870 → 00095 = 225) = C-1004 Nov. An agent should use them as expected values in regression tests.

### 1.2 Key rules (verbatim)

CONTRIBUTING.md:
- "The **wiki is the source of truth** for business rules ... If code and wiki disagree, the code is wrong."
- "Do not change a business rule in the wiki without sign-off from the product owner. If you think a rule is wrong, raise it in the pull request; do not change it yourself."
- "Python 3.10+, full type hints on all public functions." / "Google-style docstrings on all public functions and classes (`Args:`, `Returns:`, `Raises:`)."
- "Keep functions small and side-effect free; I/O only in `repository.py`, `web.py` and `cli.py`."
- "No business logic in the UI (`web.py`, `views.py`) or the CLI. Fix bugs in the domain modules."
- "No new third-party dependencies without team approval."
- Money: "All monetary values are `decimal.Decimal`. **Never use `float` for money**, not even in intermediate steps." / "Build Decimals from strings or ints" / "Round with `wattwise.money.round_eur` only. Do not call `round()` or `quantize()` in business code." / "Round **each invoice line once**, at the end of its calculation. Do not round intermediate results (e.g. a daily rate or a single tier)."
- Errors: "Raise the domain exceptions from `wattwise/errors.py`, never bare `Exception`." / "Error messages name the affected entity (meter id, customer id) and the offending values."
- Tests: "Every **bug fix** comes with at least one regression test that fails without the fix. Put the ticket id in a comment above the test: `# Regression test for BUG-123`" / "Test names: `test_<function>_<expected behaviour>`." / "Put the hand calculation for expected amounts in a comment" / "The full suite must pass: `pytest`."
- Changelog/commits: "Add a line to `CHANGELOG.md` under **Unreleased** for every user-visible change, with the ticket id." / "Commit messages follow Conventional Commits and end with the ticket id: `fix(meter): handle register rollover (BUG-123)`. Allowed types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`." / "One ticket per pull request."

Definition of done (verbatim):
- [ ] Root cause understood and described in the PR
- [ ] Fix follows the wiki rules and the conventions above
- [ ] Regression test added, full suite green
- [ ] CHANGELOG updated
- [ ] Reviewed by a second person

wiki/Development-Workflow.md (bug ticket flow): 1 Reproduce (UI/CLI, then failing test) → 2 "Find the root cause. Compare the code to the business rules in the wiki. Fix the cause, not the symptom (no special cases for single customers or meters)." → 3 regression test that fails before fix → 4 fix → 5 full suite + check customer in UI → 6 CHANGELOG under *Unreleased* → 7 PR with "ticket id, root cause, fix, how it was tested"; second-person review. Ticket files: "When a ticket is fixed, set its status to `Fixed (pending review)` and add the PR link."

No explicit branch naming convention exists. Suggest `fix/BUG-142-register-rollover` etc. (one ticket per branch/PR). Changelog line format from history: `- fix: <description> (BUG-xxx)`.

---

## 2. Bugs

### BUG-142 — November run aborts at C-1004 (register rollover) — Critical

**Reproduce**
```
$ PYTHONPATH=src python -m wattwise invoice C-1004 2026-11
  File ".../meter.py", line 51, in consumption_kwh
wattwise.errors.InvalidReadingError: Meter M-20004: reading decreased from 99870 to 95

$ PYTHONPATH=src python -m wattwise run 2026-11 ; echo $?
→ prints C-1001, C-1002, C-1003 invoices, then traceback; exit 1. C-1005 never printed.
```
UI (`billing_result` catches `BillingError`): dashboard Nov "4 / 5", Failed: 1.

**Root cause** — `src/wattwise/meter.py:49-54`:
```python
delta = current.value - previous.value
if delta < 0:
    raise InvalidReadingError(... "reading decreased from ...")
```
Violates wiki/Meter-Readings.md: "**A closing reading that is lower than the opening reading means the register rolled over.** In that case: `consumption = 10^digits − opening reading + closing reading`" and "A rolled-over reading must go through the plausibility check below like any other."

**Fix sketch** (meter.py, domain module):
```python
delta = current.value - previous.value
if delta < 0:  # register rolled over (wiki/Meter-Readings.md)
    delta += 10**meter.digits      # == meter.max_value + 1
# existing plausibility check below then runs on the rolled-over delta
```
Must use `meter.digits` / `meter.max_value` (5 and 6-digit meters, FEAT-085), never hard-coded 100000. Keep order: rollover → plausibility. Update docstring (`Raises:` wording).

**Tests to add** (tests/test_meter.py)
- `# Regression test for BUG-142` `test_consumption_kwh_handles_register_rollover`: 5-digit, 99870 → 95 = 225 (hand calc `(99999 − 99870) + 95 + 1`).
- 6-digit rollover: e.g. 999900 → 100 = 200.
- `test_consumption_kwh_flags_implausible_rollover`: 5-digit, 50000 → 100 over 30 days = 50100 kWh > 6000 → `ImplausibleConsumptionError` (meter replaced, not rolled).
- Optional: service-level / web test that `route(repo, "/?month=2026-11")` shows "5 / 5".
- Expected C-1004 Nov after fix (with current days bug): 9.44 / 77.63 / net 87.07 / total 103.61. After all three fixes: base 9.76, energy 77.63 (225 × 0.3450 = 77.625 → 77.63), net 87.39, VAT 16.60, **total 103.99**.

**Blast radius**: data only shows C-1004 Nov. But any meter rolling over (wiki: "happens to every meter sooner or later") blocks that customer AND (CLI) aborts the whole nightly batch for every customer after it alphabetically. Unbilled revenue in sample: 103.99 EUR (C-1004) + C-1005's 101.11 EUR blocked in batch.

**Traps / red herrings**
- "Nobody touched the code since the last release" — true; it's a latent rule gap triggered by data, not a regression.
- Reporter confirms the reading 00095 is correct → do NOT "fix" `data/readings.csv`.
- `abs(delta)` gives 99775 → turns into an `ImplausibleConsumptionError`, still failing (and conceptually wrong).
- Removing the check entirely → negative consumption → `energy_charge` raises ValueError.
- Wrapping `cli run` in try/except only hides the symptom (and is "business logic in the CLI"). The batch-abort is a real separate robustness defect (see §3) — mention in PR, don't scope-creep (one ticket per PR).
- Special-casing M-20004 / C-1004 is explicitly forbidden ("no special cases for single customers or meters").
- The CONTRIBUTING commit example is literally `fix(meter): handle register rollover (BUG-123)` — a hint to where the fix belongs.

### BUG-151 — Comfort bill jumps (whole consumption priced at top tier) — High

**Reproduce**
```
$ PYTHONPATH=src python -m wattwise invoice C-1002 2026-11
Base fee (29 days)    14.21 EUR
Energy (260 kWh)      95.94 EUR      # = 260 × 0.3690
Net 110.15  VAT 20.93  Total 131.08
Oct: Energy (240 kWh) 71.76, Total 102.89   → +27.4% for +8.3% kWh
```

**Root cause** — `src/wattwise/tariff.py:101-103`:
```python
for tier in tariff.tiers:
    if tier.up_to_kwh is None or kwh <= tier.up_to_kwh:
        return round_eur(Decimal(kwh) * tier.price_per_kwh)
```
Selects the single tier containing total kWh and applies its price to **all** kWh (slab pricing). Violates wiki/Tariffs.md: "Tiers work like **income tax brackets**: each tier's price applies only to the kWh that fall **inside that tier**. ... never for their whole consumption." and "using one extra kWh must never make the bill jump." Also "Round the energy charge to cents **once**, after adding up all tiers." Likely introduced by the FEAT-117 tier refactor in 1.4.0 (2026-09-15).

**Fix sketch**
```python
total = Decimal("0")
lower = 0
for tier in tariff.tiers:
    upper = kwh if tier.up_to_kwh is None else min(kwh, tier.up_to_kwh)
    if upper > lower:
        total += Decimal(upper - lower) * tier.price_per_kwh
    if tier.up_to_kwh is None or kwh <= tier.up_to_kwh:
        return round_eur(total)          # round once, after summing
    lower = tier.up_to_kwh
raise AssertionError(...)               # keep open-ended guard
```
`up_to_kwh` is an inclusive upper bound (Tier docstring + wiki "401–1000"), so kWh in tier = `min(kwh, up_to) − previous_up_to`.

**Tests to add** (tests/test_tariff.py)
- `# Regression test for BUG-151` `test_energy_charge_comfort_above_tier_only_surplus_at_higher_price`: 260 → 78.44 (`250 × 0.2990 = 74.75; 10 × 0.3690 = 3.69`).
- HeatPump three tiers: 1220 → 337.18 (`400×0.2490=99.60; 600×0.2790=167.40; 220×0.3190=70.18`).
- HeatPump middle tier: 910 → 241.89 (`99.60 + 510×0.2790=142.29`).
- Monotonic/no-jump property: `energy_charge(t, n+1) - energy_charge(t, n) <= max price` around each boundary (250/251, 400/401, 1000/1001).
- Rounding-once test where per-tier rounding would differ (choose kWh/prices giving half-cent remainders) — guards against rounding each tier.
- Existing boundary tests (200, 250 → within tier 1) keep passing — they never exercised >1 tier, which is why the suite is green.

**Blast radius** (issued vs correct energy line, net):

| Month | Cust | kWh | Issued | Correct | Overcharge net | Overcharge gross* |
| --- | --- | --- | --- | --- | --- | --- |
| Oct | C-1003 HeatPump | 910 | 253.89 | 241.89 | 12.00 | 14.28 |
| Nov | C-1002 Comfort | 260 | 95.94 | 78.44 | 17.50 | 20.83 |
| Nov | C-1003 HeatPump | 1220 | 389.18 | 337.18 | 52.00 | 61.88 |
| | | | | **Total** | **81.50** | **96.99** |

*gross = invoice total issued minus total with only this fix (VAT recomputed). C-1002 Oct (240), C-1005 (210/235), all BASIC customers unaffected. Every Comfort customer >250 kWh and every HeatPump customer >400 kWh since 1.4.0 (Sept 2026 onward, likely incl. September — not in data) was overcharged.

**Traps**
- CS agent's "C-1003 looks too high but not sure" — it is, and by more than C-1002 (52 EUR net in Nov), plus **October C-1003 is also wrong** even though no one complained (Oct hasn't been flagged by the reporter at all).
- Ticket table lists an "Energy line" row the UI comparison card doesn't actually show (UI shows only Consumption and Total) — reporter assembled it by hand; numbers are still accurate.
- The +27% is distorted by BUG-158 too (Nov base fee 29 days, Oct 30 days) — the "correct" bill comparison needs both fixes: Oct 103.47 → Nov 110.84 (+7.1%).
- Don't round per tier (CONTRIBUTING: "Do not round intermediate results (e.g. ... a single tier)").
- Don't touch `views._tariff_rows` or wiki; and don't change prices in `TARIFFS`.
- Ticket explicitly asks "If this affects more customers, we need to know" → agent should report the blast-radius table in the PR.

### BUG-158 — Base fee ~3% low (off-by-one in billable days) — Medium

**Reproduce**
```
$ PYTHONPATH=src python -m wattwise invoice C-1001 2026-11
Period:  2026-11-01 to 2026-11-30
Base fee (29 days)    9.44 EUR      # expected 30 days, 9.76
Total 112.65                         # wiki full example says 113.03
$ ... invoice C-1001 2026-10
Period:  2026-10-01 to 2026-10-31
Base fee (30 days)    9.76 EUR      # October has 31 days → should be 10.09
```

**Root cause** — `src/wattwise/models.py:86`:
```python
return (self.end - self.start).days      # exclusive; missing + 1
```
Violates wiki/Billing-Rules.md: "**Both `start` and `end` are billable days.** The number of billable days is therefore `end - start + 1`" (table: Nov = 30, Dec = 31, Feb 2027 = 28). Docstring even says "Number of billable days". Consumed at `billing.py:63` (fee) and `billing.py:66` (label). Present since 1.2.0 (FEAT-064 daily proration, 2026-01-12) — consistent with "since the switch to daily proration".

**Fix sketch**: `return (self.end - self.start).days + 1` in `BillingPeriod.days`. Nothing in `tariff.py` changes.

**Tests to add**
- `# Regression test for BUG-158` `test_billing_period_days_includes_start_and_end` in tests/test_models.py, parametrized with wiki table: Nov 30, Dec 31, Feb 2027 28 (+ leap Feb 2028 29, single-day period = 1).
- Integration: `create_invoice` Basic, Nov, 247 kWh → lines `Base fee (30 days)` 9.76, energy 85.22, net 94.98, VAT 18.05, total 113.03 (wiki full example).

**Blast radius**: every invoice, every customer, every month since Jan 2026. Base-fee shortfall = 1 day's fee = monthly × 12/365 ≈ 3.2–3.4% of base fee (29/30 = −3.3%, 30/31 = −3.2%) → matches finance's "about 3%".

| Month | Net base-fee shortfall | Gross shortfall (invoice totals) |
| --- | --- | --- |
| Oct (5 cust) | 0.33+0.49+0.65+0.33+0.49 = 2.29 | 0.39+0.58+0.77+0.39+0.59 = 2.72 |
| Nov (4 invoiced + C-1004 once billable) | 0.32+0.49+0.66+0.32+0.49 = 2.28 | ≈2.70 |

Per customer per month: Basic 0.33, Comfort 0.49, HeatPump 0.65 net. Small per invoice, but × whole customer base × 11 months (Jan–Nov 2026) it's material (e.g. 100k Basic customers ≈ 33k EUR/month net).

**Traps**
- Reporter: "Existing tests for the base fee pass, so the calculation itself might be fine." — **True and misleading**: `prorated_base_fee` is correct; tests call it with explicit `days`. The bug is upstream in `models.py`. An agent that only reads `tariff.py`/`test_tariff.py` will be tempted to hack `prorated_base_fee` (`days + 1`, change 365 to 360, or "per month" rounding) — wrong, and breaks `test_prorated_base_fee_full_year_equals_twelve_months`.
- "We always divide by 365, also in leap years" — don't "improve" to 366.
- The reporter only noticed November (29 shown). October shows "30 days", which looks plausible at a glance but is equally wrong (31-day month).
- No customer complaints because it undercharges — revenue not trust issue; but correction invoices for undercharges are a policy decision (usually written off).
- Interaction: fixing BUG-158 changes every expected invoice total; tests that hard-code totals for BUG-142/151 must be computed with the right day count (or test energy line only).

### Combined expected outcome (all three fixes)

| Month | C-1001 | C-1002 | C-1003 | C-1004 | C-1005 | Dashboard gross |
| --- | --- | --- | --- | --- | --- | --- |
| Oct issued | 112.21 | 102.89 | 325.49 | 106.04 | 92.21 | 738.84 |
| Oct correct | 112.60 | 103.47 | 311.98 | 106.43 | 92.80 | 727.28 |
| Nov issued | 112.65 | 131.08 | 485.70 | FAILED | 100.53 | 829.96 (4/5) |
| Nov correct | 113.03 | 110.84 | 424.60 | 103.99 | 101.11 | 853.57 (5/5) |

Net correction per customer (issued − correct, gross): C-1003 refund 13.51 (Oct) + 61.10 (Nov) = **74.61**; C-1002 refund 20.24 (Nov) (Oct under by 0.58); small undercharges ~0.4–0.6 for others; C-1004 Nov still to invoice.

---

## 3. Additional latent bugs / inconsistencies (out of scope for the 3 tickets; raise in PRs)

1. **`cli.py:63-66` batch run aborts on first error** — `run` calls `bill_customer` with no `BillingError` handling, so one bad reading (or a legit `ImplausibleConsumptionError` that wiki says goes "to manual review") kills invoicing for all later customers; exit 1. The UI uses `billing_result` (catches). Fix belongs in `service` (e.g. run via `billing_overview` and report failures). Even after BUG-142 is fixed, the next implausible reading will abort the run again.
2. **Non-domain exceptions** violating CONTRIBUTING ("Raise the domain exceptions from `wattwise/errors.py`"): `tariff.energy_charge` → `ValueError`/`AssertionError`; `prorated_base_fee` → `ValueError`; `repository.customer()/meter()` → raw `KeyError` (CLI `invoice C-9999 2026-11` crashes with KeyError; `billing_result` would not catch it).
3. **Docstrings incomplete** vs "Google-style ... (`Args:`, `Returns:`, `Raises:`)": `get_tariff` (no Args/Returns), `energy_charge`/`prorated_base_fee` (no Raises), `service.*`, `repository.*`, `BillingPeriod.days`.
4. `web.route`: `months[-1]` raises IndexError if no readings exist; `service.month_period` doesn't validate format (route guards via `month not in months`, CLI does not → ValueError traceback for `run 2026-13`).
5. `repository.DEFAULT_DATA_DIR = parents[2] / "data"` only works for src checkout/editable installs.
6. Plausibility uses elapsed days between readings (Nov: 30). Today `period.days` is one less than that; after the BUG-158 fix they're equal, which is a handy consistency check. Nothing verifies readings align with the period (service guarantees it by construction).
7. The month-on-month comparison in `views._comparison` computes percentages — presentation-only, acceptable, but it's the only arithmetic in views.
8. No test covers `BillingPeriod.days`, multi-tier pricing, rollover, or any end-to-end invoice amount — the suite gives zero signal for all three bugs.
9. Wiki/code agree on: VAT on net (BUG-098), HALF_UP rounding, 365 divisor, 200 kWh/day limit, validation rules. No wiki-vs-code conflict other than the three bugs.

---

## 4. Difficulty ranking & agent showcase

| Rank | Bug | Why | Locating signal |
| --- | --- | --- | --- |
| Easiest | **BUG-142** | Traceback points to exact line; wiki gives formula + identical example | Stack trace → meter.py:51 |
| Medium | **BUG-151** | Must understand marginal-tier semantics; must not round per tier; must quantify other affected customers incl. un-reported October C-1003 | Ticket mentions product sheet → wiki/Tariffs.md |
| Hardest (subtle) | **BUG-158** | Symptom appears in tariff output, ticket steers toward "calculation fine", root cause is one level away in `models.py`; fix is one character (`+ 1`) | "29 days" on invoice vs wiki's `end - start + 1` |

**Best showcase**: **BUG-158** for "smart use of repo context" (wiki rule beats misleading reporter note + green tests; agent must trace data flow beyond the obvious module) — tiny diff, great narrative. **BUG-151** for business value + transparent reasoning (blast-radius table, refund list, golden values from wiki). BUG-142 is the reliable demo/fallback (deterministic, traceback-driven). Ideal demo: run the agent on BUG-158 or BUG-151 live, with BUG-142 as warm-up.

**Context an agent MUST read**

| Bug | Must read | Nice to read |
| --- | --- | --- |
| All | CONTRIBUTING.md (tests/changelog/commit/DoD), wiki/Development-Workflow.md, CHANGELOG.md format, the issue file | Architecture.md |
| 142 | wiki/Meter-Readings.md (rollover + plausibility ordering), meter.py, models.Meter (`digits`, `max_value`), tests/test_meter.py, data (M-20004 digits=5) | cli.py (to explain batch abort but not fix it there) |
| 151 | wiki/Tariffs.md (brackets, inclusive tier bounds, round once), tariff.py `Tier` docstring, tests/test_tariff.py (hand-calc comment style), CONTRIBUTING Money section, data/customers+readings for blast radius | Billing-Rules VAT |
| 158 | wiki/Billing-Rules.md (`end - start + 1` table, 365 rule, full example), models.BillingPeriod, billing.py (where `period.days` is consumed), service.month_period (end = last day), tests/test_tariff.py (to see why tests pass) | CHANGELOG 1.2.0 (FEAT-064 origin) |

Agent guardrails worth encoding: never edit `data/` or `wiki/`; fix only domain modules; one ticket per branch; regression test must fail before fix (run suite before & after); use `round_eur` once; generate PR body (root cause / fix / tests / blast radius); set ticket status `Fixed (pending review)`; changelog line `- fix: ... (BUG-xxx)` under Unreleased; commit `fix(<module>): ... (BUG-xxx)`.

---

## 5. Business impact

| Bug | Revenue | Customer trust | Regulatory / corrections |
| --- | --- | --- | --- |
| **BUG-142** | Invoices not issued → cash-flow delay; CLI batch abort blocks *every* customer after the failing one. Grows over time since every meter eventually rolls over. | Late/missing invoices, then a catch-up bill. | Billing SLA breach (ops "by end of week"); no correction invoices, but on-call cost. |
| **BUG-151** | Over-billing: 81.50 EUR net / ~97 EUR gross in 3 invoices of 10 sample bills; scales with every Comfort >250 kWh and HeatPump >400 kWh customer since 1.4.0 (heat-pump usage peaks in winter → worsening). | Directly breaks the marketing promise ("you only pay the higher price for what you use above your allowance") — misleading-advertising / complaint escalation risk, churn. | Corrected invoices + refunds mandatory for overcharges (Oct + Nov, and likely Sept); energy-consumer protection / regulator complaints (e.g. ombudsman). Highest legal exposure. |
| **BUG-158** | Systematic under-billing ≈1 day of base fee per invoice (~3.3% of base-fee revenue) since Jan 2026; ~0.33–0.65 EUR net per customer-month; material at scale. | No complaints (in customers' favour) — but invoice says "29 days" for a 30-day month, undermining credibility of the invoice. | Back-billing small undercharges usually not worth it/needs policy & customer notice; finance must restate plan vs. actual. Fixing changes every invoice from next run → communicate. |

Priority: fix 142 first (operational blocker), 151 next (legal/trust, refunds), 158 (revenue leak). Each as separate PR.
