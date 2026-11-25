BUG-158 is fixed and marked `Fixed (pending review)`. Nothing is committed or pushed.

**Cause:** `BillingPeriod.days` at `src/wattwise/models.py:86` returned `end - start`, which leaves out the end day. The wiki says both start and end are billable (`end - start + 1`), so every month billed one day too little base fee. That is the ~3% Finance saw. The reporter's guess was half right: the base fee formula is fine, but it was given the wrong number of days. The fix is adding `+ 1` on that line.

**Verification:**
- **Ticket repro:** C-1001 November now shows `Base fee (30 days) 9.76` and a total of 113.03 EUR, matching the wiki.
- **New tests:** two regression tests built from the wiki examples. Both failed before the fix and pass after.
- **Drift check:** the billing-period, invoice-layout and full-example rules are now in sync.
- **pytest is not fully green:** 56 pass, 4 fail. All 4 failures are from other problems, left alone as you asked:
  - three come from the tier pricing bug (BUG-151);
  - one is a lint check that flags 3 errors in `tariff.py`. They were there before this change, and the count didn't change.
- **Before/after billing:** only the base fee line and the totals built on it change. Energy amounts are identical for every customer.

**Blast radius:** all 5 customers in both months in `data/` (Oct and Nov 2026) were underbilled, 5.42 EUR gross in total. In production this affects every invoice since release 1.2.0. Someone in product or finance needs to decide whether to send corrected invoices; the per-customer amounts are in the RCA.

**Review:** the reviewer subagent approved. I fixed two of its points: I added the new full-example test to the invoice-layout rule in `rules.json`, and I wrote the commit message to `reports/BUG-158-commit-msg.txt`. It also flagged that `reports/BUG-158-agent-output.md` is empty. That file was there before this run, so I left it for you.

The full audit trail is in `reports/BUG-158-rca.md`, including the draft PR body. It changed on disk after I last wrote it, probably a hook; I didn't touch it.
