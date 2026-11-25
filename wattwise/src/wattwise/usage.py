"""Daily consumption per customer, for the consumption chart on the customer page."""

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from wattwise.models import BillingPeriod
from wattwise.repository import DataRepository
from wattwise.service import available_months, month_period


@dataclass(frozen=True)
class MonthlyUsage:
    """Consumption of one customer in one calendar month.

    Attributes:
        month: Month as ``YYYY-MM``.
        period: The calendar month as a billing period.
        total_kwh: Energy consumed in the month.
        days: Number of days in the month.
        kwh_per_day: Average daily consumption.
    """

    month: str
    period: BillingPeriod
    total_kwh: int
    days: int
    kwh_per_day: Decimal


def daily_usage(repo: DataRepository, customer_id: str) -> list[MonthlyUsage]:
    """Average daily consumption of a customer for every month with readings.

    Args:
        repo: Data access.
        customer_id: Customer to look up, e.g. ``"C-1001"``.

    Returns:
        One entry per month, oldest first. Months without both readings are skipped.
    """
    meter_id = repo.customer(customer_id).meter_id
    usage: list[MonthlyUsage] = []
    for month in available_months(repo):
        period = month_period(month)
        opening = repo.find_reading(meter_id, period.start)
        closing = repo.find_reading(meter_id, period.end + timedelta(days=1))
        if opening is None or closing is None:
            continue
        total_kwh = max(closing.value - opening.value, 0)  # never show negative usage
        days = (period.end - period.start).days
        usage.append(
            MonthlyUsage(
                month=month,
                period=period,
                total_kwh=total_kwh,
                days=days,
                kwh_per_day=Decimal(total_kwh) / Decimal(days),
            )
        )
    return usage
