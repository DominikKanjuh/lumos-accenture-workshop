BUG-151 is fixed and marked `Fixed (pending review)`. Nothing is committed. The full suite is not green: 62 tests pass and `test_wikiguard_lint_has_no_errors` still fails. That failure was there before this change (details below).

- **Root cause:** `tariff.energy_charge` charged the customer's entire consumption at the price of the highest tier they reached. The wiki rule (`Tariffs#how-tiered-prices-work`) says each tier's price applies only to the kWh inside that tier. Going from 250 to 251 kWh on Comfort added 17.87 EUR.
- **Fix:** only `src/wattwise/tariff.py` changed. Each tier's kWh are now charged at that tier's price, and the total is rounded once with `round_eur`.
- **Tests:** I added three tests to `test_tariff.py`: the two wiki examples (Comfort 260 kWh → 78.44, HeatPump 1220 kWh → 337.18) and one boundary case (Comfort 251 kWh → 75.12). All three failed before the fix and pass now.
- **Checks:** the drift check now shows 0 DRIFT, with the tier rule IN SYNC.
- **Remaining failure:** it comes from 3 lint errors in `tariff.py` where the code raises built-in Python exceptions (`ValueError`, `AssertionError`) instead of the project's own error types. I left them because changing `ValueError` would break an existing test, and we may not rewrite existing tests. They need a separate ticket.
- **Ticket check:** C-1002 for 2026-11 now shows energy 78.44 EUR and a total of 110.84 EUR. The CS agent's hunch about C-1003 was right; that customer was overcharged too.
- **Overcharged customers in `data/`:** only these three invoices changed in the before/after run of all customers and months:

| Invoice | Overcharged (gross) |
| --- | --- |
| C-1002, 2026-11 | 20.82 EUR |
| C-1003, 2026-10 | 14.28 EUR |
| C-1003, 2026-11 | 61.88 EUR |
| **Total** | **96.98 EUR** |

  Production invoices since 1.4.0, when tiers were introduced, are probably affected too and need corrected invoices.
- **Review:** the reviewer subagent approved. I applied its minor findings: added a `Raises:` section to the docstring and filled in section 8 of the RCA.
- **Untracked file:** `reports/BUG-151-agent-output.md` is an empty file that was there before this run; I left it alone.

Files are in `reports/`:
- BUG-151-rca.md
- BUG-151-commit-msg.txt
