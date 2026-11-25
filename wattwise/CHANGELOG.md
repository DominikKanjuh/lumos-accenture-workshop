# Changelog

All notable changes to this project are documented here.

## Unreleased

- fix: meter register rollover is billed as consumption instead of rejecting the reading (BUG-142)
- fix: billing period counts both start and end day, so the prorated base fee covers every supplied day (BUG-158)

## 1.4.0 - 2026-09-15

- feat: web UI for billing operations: billing run dashboard and invoice pages (FEAT-121)
- feat: new tariff **WattWise HeatPump** with three price tiers (FEAT-117)
- refactor: tariffs are now defined as a list of tiers instead of a single price (FEAT-117)

## 1.3.1 - 2026-06-02

- fix: VAT is now computed on the rounded net amount instead of per line (BUG-098)

## 1.3.0 - 2026-04-20

- feat: support for 6-digit meters (FEAT-085)
- feat: plausibility check for unusually high consumption (FEAT-091)

## 1.2.0 - 2026-01-12

- feat: base fee is prorated per day instead of per month (FEAT-064)
