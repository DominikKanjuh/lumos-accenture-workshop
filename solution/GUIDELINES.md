# WattWise Engineering Guidelines

Company-wide principles for every system that touches customers, money or energy data. They apply to humans and AI agents alike. Each guideline has an ID; **Enforced by** names the automated check (`lint` = `tools/wikiguard_lint.py`, `inv` = `tests/test_wikiguard.py` invariants, `hook` = `tools/guard.py`, `drift` = drift checker). Unenforced guidelines are checked in review.

Every guideline traces to a real failure. The three open WattWise incidents are cited as *Why*.

## C — Customer first

| ID | Guideline | Why | Enforced by |
| --- | --- | --- | --- |
| C1 | **What we promise is what we bill.** Product sheets, wiki rules and code must say the same thing; the wiki rule is the contract. | BUG-151: sheet promised "higher price only above allowance"; code charged it on everything | drift, inv |
| C2 | **One customer's problem never blocks another customer.** Batch jobs isolate failures per record, report them, and carry on. | BUG-142: one meter aborted the whole run; C-1005 got no invoice | review |
| C3 | **When in doubt, hold and escalate; never guess.** An implausible invoice is held for review, not sent and not silently "fixed". | | review |
| C4 | **Find all affected customers, not just the one who called.** Every billing bug ships with a blast-radius list and corrected invoices. | BUG-151: C-1003 October overcharge was never reported | fix-bug skill |
| C5 | **Every invoice line is explainable** in plain language and traceable to a rule ID. | | drift (rule map) |

## N — Numbers, money and counters

| ID | Guideline | Why | Enforced by |
| --- | --- | --- | --- |
| N1 | **Never use binary floating point for money or energy.** `Decimal` built from str/int, or integer minor units (cents, Wh). | float errors compound over millions of invoices | lint |
| N2 | **Round once, in one place,** at the end of each line (`money.round_eur`, half-up). | BUG-098 | lint |
| N3 | **No overflow, ever.** Use arbitrary-precision or 64-bit integers for counters, sums and aggregates (Python `int` is unbounded; in JS use `BigInt`, in Java `long`/`BigDecimal`, in SQL `BIGINT`/`NUMERIC`). Never 32-bit for energy, money or IDs. Validate ranges at the boundary. | 32-bit Wh overflows at 2.1 GWh: one feeder in a year | review |
| N4 | **Physical counters are bounded and wrap.** Model the limit (`10^digits`) and handle rollover explicitly; never assume a counter only grows. | BUG-142: 99870 → 00095 | inv, drift |
| N5 | **Prices are continuous in consumption.** One extra kWh never costs more than the highest unit price. | BUG-151: +1 kWh at tier boundary cost 17.87 EUR | inv |
| N6 | **Units in names** (`kwh`, `eur`, `days`, `_net`, `_gross`). | | review |

## T — Time and periods

| ID | Guideline | Why | Enforced by |
| --- | --- | --- | --- |
| T1 | **Periods are inclusive of first and last day** (`end - start + 1`). Test month ends, February and leap years. | BUG-158: one day lost on every invoice, about 3% of base-fee revenue | inv, drift |
| T2 | **No hard-coded month or year lengths** in logic; derive from the calendar. | | review |
| T3 | **Domain logic never reads the clock;** dates are parameters. Use `Europe/Berlin` for interval data and test DST days (23/25 h). | | review |

## Q — Quality and testing

| ID | Guideline | Why | Enforced by |
| --- | --- | --- | --- |
| Q1 | **Every wiki worked example is an executable test.** Green tests that ignore the rules prove nothing. | all three bugs passed 39 tests | drift, lint |
| Q2 | **Test boundaries and invariants, not just happy paths:** tier boundaries, 0 kWh, rollover, month ends, full-year sums. | | inv |
| Q3 | **Every bug fix ships a regression test that fails without the fix.** | CONTRIBUTING | review |
| Q4 | **Reconcile automatically.** Totals (base-fee revenue, kWh billed vs metered) are checked against plan every run; don't wait for finance. | BUG-158 found by controlling months later | review |

## E — Errors and resilience

| ID | Guideline | Enforced by |
| --- | --- | --- |
| E1 | Raise domain exceptions (`errors.py`), never built-ins; messages name the entity and the values. | lint |
| E2 | Validate at system boundaries (files, APIs, UI); keep domain functions pure. | review |
| E3 | Errors are data: the billing run reports each failure with customer, reason and suggested action. | review |

## K — Knowledge and source of truth

| ID | Guideline | Enforced by |
| --- | --- | --- |
| K1 | **The wiki owns the rules, the code owns the mechanics.** If they disagree, the code is wrong until the product owner says otherwise. | drift, hook |
| K2 | Every rule has a stable ID mapped to code and tests (`tools/drift-check/rules.json`). No orphan rules, no undocumented business logic. | lint |
| K3 | Rule changes need product-owner sign-off via `wiki/_proposals/`; docs change in the same PR as code. | hook, review |
| K4 | Keep the *why* in the wiki; documentation that only restates the code is noise. | review |

## P — Privacy and security

| ID | Guideline | Enforced by |
| --- | --- | --- |
| P1 | Meter and consumption data is personal data (GDPR): minimise, pseudonymise in logs, tests and prompts. | review |
| P2 | No customer data goes to external AI services without an approved data-processing agreement. | review |
| P3 | No new third-party dependencies without approval; no secrets in the repo. | lint (deps), review |

## A — AI-assisted engineering

| ID | Guideline | Enforced by |
| --- | --- | --- |
| A1 | Agents follow `AGENTS.md` and these guidelines; hard boundaries are enforced by hooks, not trust. | hook |
| A2 | **Humans approve, agents propose.** Agents never merge, close tickets or change rules. | hook, review |
| A3 | Every agent action is logged (`reports/agent-audit.log`) and every fix has a written RCA. | hook |
| A4 | Escalating ("I'm not sure which side is right") is a success, not a failure. | skill |
