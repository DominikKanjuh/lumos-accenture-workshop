# Wiki/code drift report

| Rule | Status | Wiki says | Code does | Tests |
| --- | --- | --- | --- | --- |
| `Billing-Rules#billing-period` | **DRIFT** | Both start and end are billable days. The number of billable days is therefore end - start + 1: | `days('2026-11-01 to 2026-11-30') -> 29  [wiki: 30] (+2 more)` | none |
| `Billing-Rules#base-fee` | **IN SYNC** | Since release 1.2.0 the base fee is prorated per day (FEAT-064), so that customers who move in or out mid-m... | `matches 1/1 examples` | 2 |
| `Billing-Rules#invoice-layout` | **DRIFT** (via Billing-Rules#billing-period) | An invoice has exactly two net lines, in this order: 1. Base fee (<days> days) 2. Energy (<kWh> kWh) follow... | `[l.description for l in invoice('BASIC', '2026-11', 247).lines] -> ['Base fee (29 days)', 'Energy (247 kWh)']  [wiki: ['Base fee (30 days)', 'Energy (247 kWh)']]` | 1 |
| `Billing-Rules#vat-and-rounding` | **IN SYNC** | VAT rate is 19%. | `matches 2/2 examples` | 3 |
| `Billing-Rules#full-example` | **DRIFT** (via Billing-Rules#billing-period) | Customer on WattWise Basic, November 2026, 247 kWh: | `amount(invoice('BASIC', '2026-11', 247), 'Base fee (30 days)') -> 9.44  [wiki: 9.76] (+3 more)` | none |
| `Meter-Readings#consumption` | **IN SYNC** | consumption = closing reading − opening reading | `matches 1/1 examples` | 1 |
| `Meter-Readings#register-rollover` | **DRIFT** | A closing reading that is lower than the opening reading means the register rolled over. In that case: | `consumption(5, 99870, 95) -> raises InvalidReadingError: Meter M-1: reading decreased from 99870 to 95  [wiki: 225] (+2 more)` | none |
| `Meter-Readings#plausibility-check` | **IN SYNC** | Since 1.3.0 (FEAT-091): if the average consumption is above 200 kWh per day between the two readings, the r... | `matches 2/2 examples` | 1 |
| `Meter-Readings#validation` | **IN SYNC** | A reading is rejected with InvalidReadingError if: it belongs to a different meter, its value is negative o... | `matches 3/3 examples` | 3 |
| `Tariffs#tariffs` | **UNTESTED** | Tier limits apply per billing period (per month). | `matches 6/6 examples` | none |
| `Tariffs#how-tiered-prices-work` | **DRIFT** | Tiers work like income tax brackets: each tier's price applies only to the kWh that fall inside that tier. | `energy_charge(get_tariff('COMFORT'), 260) -> 95.94  [wiki: 78.44] (+3 more)` | 2 |
| `Tariffs#adding-a-tariff` | **IN SYNC** | Tariffs live in src/wattwise/tariff.py (TARIFFS). | `matches 1/1 examples` | 1 |
| `Billing-Rules#energy-charge` | **NO EXAMPLE** | The energy charge depends on the tariff and consumption. | `matches 0/0 examples` | none |
| `Meter-Readings#where-readings-come-from` | **NO EXAMPLE** | The reading on the 1st opens that month's period and closes the previous month's period. | `matches 0/0 examples` | none |

## Failing examples

- `Billing-Rules#billing-period`: `days('2026-11-01 to 2026-11-30')` wiki **30**, code **29** (wiki table)
- `Billing-Rules#billing-period`: `days('2026-12-01 to 2026-12-31')` wiki **31**, code **30** (wiki table)
- `Billing-Rules#billing-period`: `days('2027-02-01 to 2027-02-28')` wiki **28**, code **27** (wiki table)
- `Billing-Rules#invoice-layout`: `[l.description for l in invoice('BASIC', '2026-11', 247).lines]` wiki **['Base fee (30 days)', 'Energy (247 kWh)']**, code **['Base fee (29 days)', 'Energy (247 kWh)']** (wiki)
- `Billing-Rules#full-example`: `amount(invoice('BASIC', '2026-11', 247), 'Base fee (30 days)')` wiki **9.76**, code **9.44** (wiki table)
- `Billing-Rules#full-example`: `amount(invoice('BASIC', '2026-11', 247), 'Net')` wiki **94.98**, code **94.66** (wiki table)
- `Billing-Rules#full-example`: `amount(invoice('BASIC', '2026-11', 247), 'VAT 19%')` wiki **18.05**, code **17.99** (wiki table)
- `Billing-Rules#full-example`: `amount(invoice('BASIC', '2026-11', 247), 'Total')` wiki **113.03**, code **112.65** (wiki table)
- `Meter-Readings#register-rollover`: `consumption(5, 99870, 95)` wiki **225**, code **raises InvalidReadingError: Meter M-1: reading decreased from 99870 to 95** (wiki)
- `Meter-Readings#register-rollover`: `consumption(6, 999900, 100)` wiki **200**, code **raises InvalidReadingError: Meter M-1: reading decreased from 999900 to 100** (registry)
- `Meter-Readings#register-rollover`: `consumption(5, 50000, 100)` wiki **raises ImplausibleConsumptionError**, code **raises InvalidReadingError: Meter M-1: reading decreased from 50000 to 100** (wiki)
- `Tariffs#how-tiered-prices-work`: `energy_charge(get_tariff('COMFORT'), 260)` wiki **78.44**, code **95.94** (wiki table)
- `Tariffs#how-tiered-prices-work`: `energy_charge(get_tariff('HEATPUMP'), 1220)` wiki **337.18**, code **389.18** (wiki table)
- `Tariffs#how-tiered-prices-work`: `max_step('COMFORT')` wiki **0.37**, code **17.87** (wiki)
- `Tariffs#how-tiered-prices-work`: `max_step('HEATPUMP')` wiki **0.32**, code **40.32** (wiki)

## Coverage

**Wiki rules without tests:** `Billing-Rules#billing-period`, `Billing-Rules#full-example`, `Meter-Readings#register-rollover`, `Tariffs#tariffs`, `Billing-Rules#energy-charge`, `Meter-Readings#where-readings-come-from`

**Wiki sections not in registry:** none

**UNDOCUMENTED code (not referenced by any wiki rule):** `models.BillingPeriod.label`, `money.CENT`, `service.available_months`, `service.bill_customer`, `service.billing_overview`, `service.billing_result`, `service.previous_month`
