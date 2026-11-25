from wattwise.repository import DataRepository
from wattwise.usage import daily_usage
from wattwise.web import route


def test_daily_usage_has_one_entry_per_month() -> None:
    usage = daily_usage(DataRepository(), "C-1001")
    assert [u.month for u in usage] == ["2026-10", "2026-11"]


def test_daily_usage_total_matches_readings() -> None:
    # C-1001 November: 41702 - 41455 = 247 kWh
    november = daily_usage(DataRepository(), "C-1001")[-1]
    assert november.total_kwh == 247
    assert november.kwh_per_day > 0


def test_invoice_page_shows_daily_consumption_chart() -> None:
    response = route(DataRepository(), "/invoice/C-1001/2026-11")
    assert "Daily consumption" in response.body
    assert "<svg" in response.body
