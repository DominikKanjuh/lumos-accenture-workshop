# drift-check

Checks that the WattWise code still does what the wiki says. WattWise's CONTRIBUTING says
"the wiki is the source of truth ... if code and wiki disagree, the code is wrong", but nothing
enforces it: the three open bugs (BUG-142, -151, -158) are all code that drifted away from a wiki
rule, and the 39 green tests miss every one. This tool closes that gap. It is deterministic,
uses only the stdlib, and never writes into the client repo.

```bash
python tools/drift-check/drift_check.py --repo wattwise          # console report + drift-report.md
python tools/drift-check/drift_check.py --repo wattwise --out /tmp/r.md
```

Exit code `1` on any DRIFT or registry problem, so it can gate CI or a pre-merge hook.

## How it works

1. **Rules come from the wiki.** Each `##`/`###` heading in `wiki/Billing-Rules.md`,
   `Meter-Readings.md` and `Tariffs.md` is one rule with a stable ID: `<Page>#<heading-slug>`,
   e.g. `Tariffs#how-tiered-prices-work`. Headings that start with `Example` are worked examples
   for the rule above them. "Wiki says" is the rule's first sentence that has bold text in it.
2. **Examples come from the wiki tables.** The wiki's worked-example tables are used directly as
   test data (billable days, the full invoice example, the tier examples, the tariff catalogue).
   Prose examples (e.g. `99870 → 00095 = 225 kWh`) are written out in the registry together with
   a `wiki_quote`. The checker confirms that quote is still in the wiki; if it isn't, it reports a
   registry problem.
3. **`rules.json` is the registry.** It maps each rule ID to its code symbols, its tests and its
   executable examples. Small helpers in `drift_check.py` (`days()`, `consumption()`,
   `invoice()`, `max_step()` ...) let each example read like the wiki.
4. **The examples run against `wattwise/src`.** The code is imported through `sys.path`. Each
   result is compared with what the wiki expects; an expected value of `raises X` matches an
   exception.

| Status | Meaning |
| --- | --- |
| `IN SYNC` | All examples match the wiki, and at least one test is mapped to the rule |
| `DRIFT` | At least one example disagrees with the wiki. `via X` means it comes from drift in rule X (`depends_on`) |
| `UNTESTED` | The code matches the wiki today, but no test protects the rule |
| `NO EXAMPLE` | The rule is in the registry but has nothing executable yet |
| UNDOCUMENTED code | A public function, method or constant in a domain module that no rule references |

The coverage section also lists wiki sections that have no registry entry. The checker also
validates the registry itself: every code symbol and test it names must exist (found with `ast`).

## Adding a rule

Add a heading to the wiki, then an entry in `rules.json`:

```json
"Tariffs#how-tiered-prices-work": {
  "code": ["tariff.energy_charge"],
  "tests": ["test_tariff.py::test_energy_charge_comfort_at_tier_boundary"],
  "examples": [
    {"table": 0, "where": {"Tier": "Energy charge"},
     "call": "energy_charge(get_tariff('COMFORT'), {kWh in tier})", "expect": "{Amount}"},
    {"call": "max_step('COMFORT')", "expect": "0.37", "wiki_quote": "must never make the bill jump"}
  ]
}
```

`{Column}` placeholders are filled from each row of the section's n-th table. Bold markers,
backticks, ` EUR` and thousands separators are stripped from the cells.

## Verified

- Current code: 5 DRIFT, which trace back to 3 root rules: BUG-158 `billing-period`, BUG-142
  `register-rollover`, BUG-151 `how-tiered-prices-work`. 1 UNTESTED (tariff catalogue).
  4 wiki rules with no tests. 7 undocumented code symbols.
- A scratch copy with the three fixes applied: 0 DRIFT, exit 0. The 4 UNTESTED left over are the
  regression tests still missing.

## Next steps (not built)

- Store a hash of each wiki section in the registry, so that editing a wiki rule flags it for
  review.
- Have an agent propose `rules.json` entries for new wiki sections, with a human approving them.
- Emit the examples as pytest cases (golden tests generated from the wiki).
