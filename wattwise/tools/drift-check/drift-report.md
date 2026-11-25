# Wiki/code drift report

| Rule | Status | Wiki says | Code does | Tests |
| --- | --- | --- | --- | --- |
| `Billing-Rules#billing-period` | **IN SYNC** | Both start and end are billable days. The number of billable days is therefore end - start + 1: | `matches 3/3 examples` | 1 |
| `Billing-Rules#base-fee` | **IN SYNC** | Since release 1.2.0 the base fee is prorated per day (FEAT-064), so that customers who move in or out mid-m... | `matches 1/1 examples` | 2 |
| `Billing-Rules#invoice-layout` | **IN SYNC** | An invoice has exactly two net lines, in this order: 1. Base fee (<days> days) 2. Energy (<kWh> kWh) follow... | `matches 1/1 examples` | 2 |
| `Billing-Rules#vat-and-rounding` | **IN SYNC** | VAT rate is 19%. | `matches 2/2 examples` | 3 |
| `Billing-Rules#full-example` | **IN SYNC** | Customer on WattWise Basic, November 2026, 247 kWh: | `matches 5/5 examples` | 1 |
| `Meter-Readings#consumption` | **IN SYNC** | consumption = closing reading − opening reading | `matches 1/1 examples` | 1 |
| `Meter-Readings#register-rollover` | **IN SYNC** | A closing reading that is lower than the opening reading means the register rolled over. In that case: | `matches 3/3 examples` | 3 |
| `Meter-Readings#plausibility-check` | **IN SYNC** | Since 1.3.0 (FEAT-091): if the average consumption is above 200 kWh per day between the two readings, the r... | `matches 2/2 examples` | 1 |
| `Meter-Readings#validation` | **IN SYNC** | A reading is rejected with InvalidReadingError if: it belongs to a different meter, its value is negative o... | `matches 3/3 examples` | 3 |
| `Tariffs#tariffs` | **UNTESTED** | Tier limits apply per billing period (per month). | `matches 6/6 examples` | none |
| `Tariffs#how-tiered-prices-work` | **IN SYNC** | Tiers work like income tax brackets: each tier's price applies only to the kWh that fall inside that tier. | `matches 4/4 examples` | 6 |
| `Tariffs#adding-a-tariff` | **IN SYNC** | Tariffs live in src/wattwise/tariff.py (TARIFFS). | `matches 1/1 examples` | 1 |
| `Billing-Rules#energy-charge` | **NO EXAMPLE** | The energy charge depends on the tariff and consumption. | `matches 0/0 examples` | none |
| `Meter-Readings#where-readings-come-from` | **NO EXAMPLE** | The reading on the 1st opens that month's period and closes the previous month's period. | `matches 0/0 examples` | none |

## Failing examples

- none

## Coverage

**Wiki rules without tests:** `Tariffs#tariffs`, `Billing-Rules#energy-charge`, `Meter-Readings#where-readings-come-from`

**Wiki sections not in registry:** none

**UNDOCUMENTED code (not referenced by any wiki rule):** `models.BillingPeriod.label`, `money.CENT`, `service.available_months`, `service.bill_customer`, `service.billing_overview`, `service.billing_result`, `service.previous_month`
