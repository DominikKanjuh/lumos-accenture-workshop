# FEAT-163: Bill movers only for the days they are supplied

| Field | Value |
| --- | --- |
| Status | Open |
| Type | Feature |
| Priority | High - customers who move are overcharged |
| Reported by | Billing product owner |
| Reported on | 2026-12-04 |
| Component | Invoicing |
| Spec | [wiki/Move-In-Move-Out.md](../wiki/Move-In-Move-Out.md) |

## Description

Since release 1.2.0 (FEAT-064) the wiki says the base fee is prorated per day "so that
customers who move in or out mid-month only pay for the days they are supplied". The
product sheet promises the same.

Billing only knows full calendar months: there is no move-in or move-out date on the customer,
and every invoice covers the whole month. A customer who moves in on 16 November is billed
the base fee for all of November.

The product owner has written the rules in [wiki/Move-In-Move-Out.md](../wiki/Move-In-Move-Out.md).

## Expected result

The worked examples in the wiki page hold:

1. Billable days match the table in *Billable days for a partial month*, including the
   0-days case (no invoice).
2. *Example: move-in, WattWise Basic* gives Total **55.07 EUR**, with the base fee line
   `Base fee (15 days)`.
3. *Example: move-out, WattWise Comfort* gives Total **75.71 EUR**, with the base fee line
   `Base fee (20 days)`.
4. Customers supplied the whole month get exactly the same invoice as today.

## Notes

- The customer record needs `supply_start` and `supply_end` fields. The sample data in `data/`
  has no movers; do not edit it. Use test fixtures.
- Tier limits are **not** prorated. This was a deliberate product decision, so do not change it.
- Depends on BUG-158 (billable days must count both the first and the last day).
