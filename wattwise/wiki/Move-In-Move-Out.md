# Move-In and Move-Out

Customers who move in or out during a month are billed **only for the days we supply them**.
This is the promise behind daily proration of the base fee (FEAT-064, release 1.2.0, see
[Billing Rules](Billing-Rules.md#base-fee)): "customers who move in or out mid-month only pay
for the days they are supplied".

Status: approved by the product owner (FEAT-163). Not implemented yet.

## Supply period

Every customer has a supply period:

- `supply_start`: the move-in date, the first day we supply the customer.
- `supply_end`: the move-out date, the **last** day we supply the customer. Empty while the
  customer is still with us.

Both `supply_start` and `supply_end` are supplied days.

## Billable days for a partial month

The billable days of a month are the days that lie both in the calendar month **and** in the
supply period, counting both the first and the last day:

```
first billable day = later of (month start, supply_start)
last billable day  = earlier of (month end, supply_end)
billable days      = last billable day − first billable day + 1
```

| Supply | Month | Billable days |
| --- | --- | --- |
| supplied all month | 2026-11 | 30 |
| move-in 2026-11-16 | 2026-11 | 15 |
| move-out 2026-11-20 | 2026-11 | 20 |
| move-in 2026-11-16, move-out 2026-11-20 | 2026-11 | 5 |
| move-in 2026-12-05 | 2026-11 | 0 |

If a month has **0 billable days**, no invoice is created for that month.

## Meter readings on moving day

The metering service takes an extra reading when a customer moves:

- **Move-in:** a reading on `supply_start` at 00:00. It opens the first, partial period.
- **Move-out:** a reading on the day after `supply_end` at 00:00. It closes the last, partial period.

Consumption is closing reading − opening reading, with register rollover and the plausibility
check exactly as in [Meter Readings](Meter-Readings.md). The plausibility check uses the
actual number of days between the two readings.

## Prices for a partial month

- **Base fee:** daily rate × billable days, as in [Billing Rules](Billing-Rules.md#base-fee).
- **Energy:** the normal tariff. **Tier limits are not prorated**: a customer who moves in on
  the 16th still gets the full 250 kWh first tier on WattWise Comfort.
- Invoice layout, VAT and rounding do not change. The base fee line shows the billable days,
  e.g. `Base fee (15 days)`.

### Example: move-in, WattWise Basic

Move-in 2026-11-16. Readings: 2026-11-16 → 30000, 2026-12-01 → 30120 (120 kWh).

| Line | Calculation | Amount |
| --- | --- | --- |
| Base fee (15 days) | 9.90 × 12 / 365 × 15 = 4.8821… | 4.88 |
| Energy (120 kWh) | 120 × 0.3450 | 41.40 |
| **Net** | | **46.28** |
| VAT 19% | 46.28 × 0.19 = 8.7932 | 8.79 |
| **Total** | | **55.07** |

### Example: move-out, WattWise Comfort

Move-out 2026-11-20 (last supplied day). Readings: 2026-11-01 → 10000, 2026-11-21 → 10180 (180 kWh).

| Line | Calculation | Amount |
| --- | --- | --- |
| Base fee (20 days) | 14.90 × 12 / 365 × 20 = 9.7972… | 9.80 |
| Energy (180 kWh) | 180 × 0.2990 | 53.82 |
| **Net** | | **63.62** |
| VAT 19% | 63.62 × 0.19 = 12.0878 | 12.09 |
| **Total** | | **75.71** |

## Not in scope

- Customers who move within the same month **and** change tariff: handled manually by
  customer service.
- Moving the readings in `data/`: the sample data has no movers yet. Use test fixtures.
