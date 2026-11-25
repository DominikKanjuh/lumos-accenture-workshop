"""WikiGuard gate inside the normal test suite (installed as tests/test_wikiguard.py).

1. The knowledge layer is in place (lint has no errors).
2. Wiki and code agree (drift check).
3. Guideline invariants that hold for ANY input, not just hand-picked examples.
"""
import importlib.util
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from wattwise.models import BillingPeriod, Meter, MeterReading
from wattwise.meter import consumption_kwh
from wattwise.tariff import TARIFFS, energy_charge, prorated_base_fee

REPO = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_wikiguard_lint_has_no_errors() -> None:
    lint = _load("wikiguard_lint", REPO / "tools" / "wikiguard_lint.py").run(REPO)
    errors = [f"{a}: {m}" for lvl, a, m in lint.findings if lvl == "ERROR"]
    assert not errors, "\n".join(errors)


def test_wiki_and_code_are_in_sync() -> None:
    drift = _load("drift_check", REPO / "tools" / "drift-check" / "drift_check.py")
    rep = drift.check(REPO, json.loads((REPO / "tools/drift-check/rules.json").read_text()))
    drifted = [f"{r['id']}: {r['failed'][0][0]} -> {r['failed'][0][2]} (wiki {r['failed'][0][1]})"
               for r in rep["results"] if r["status"] == "DRIFT"]
    assert not drifted, "\n".join(drifted)


# N5: one extra kWh never costs more than the highest unit price (+ 1 cent rounding).
@pytest.mark.parametrize("code", sorted(TARIFFS))
def test_energy_charge_is_continuous_in_consumption(code: str) -> None:
    tariff = TARIFFS[code]
    max_step = max(t.price_per_kwh for t in tariff.tiers) + Decimal("0.01")
    for kwh in range(0, 3000):
        step = energy_charge(tariff, kwh + 1) - energy_charge(tariff, kwh)
        assert Decimal("0") <= step <= max_step, f"{code}: {kwh}->{kwh + 1} kWh costs {step} EUR"


# T1: billable days are inclusive; a calendar month bills as many days as it has.
@pytest.mark.parametrize("year,month,days", [(2026, 2, 28), (2028, 2, 29), (2026, 11, 30), (2026, 12, 31)])
def test_billing_period_days_counts_every_calendar_day(year: int, month: int, days: int) -> None:
    assert BillingPeriod(date(year, month, 1), date(year, month, days)).days == days


# T1/Q2: twelve monthly periods of a year bill exactly twelve base fees.
@pytest.mark.parametrize("code", sorted(TARIFFS))
def test_base_fee_over_calendar_year_equals_twelve_months(code: str) -> None:
    tariff = TARIFFS[code]
    ends = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    total = sum(prorated_base_fee(tariff, BillingPeriod(date(2026, m, 1), date(2026, m, d)).days)
                for m, d in enumerate(ends, start=1))
    assert abs(total - 12 * tariff.monthly_base_fee) <= Decimal("0.12")


# N4: bounded counters wrap; consumption across rollover is 10^digits - opening + closing.
@pytest.mark.parametrize("digits,opening,closing,expected", [(5, 99870, 95, 225), (6, 999990, 10, 20)])
def test_consumption_kwh_handles_register_rollover(digits: int, opening: int, closing: int, expected: int) -> None:
    meter = Meter("M-TEST", digits)
    prev = MeterReading("M-TEST", date(2026, 11, 1), opening)
    curr = MeterReading("M-TEST", date(2026, 12, 1), closing)
    assert consumption_kwh(meter, prev, curr) == expected
