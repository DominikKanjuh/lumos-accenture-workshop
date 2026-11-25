from datetime import date
from decimal import Decimal

from tests.conftest import reading
from wattwise.billing import VAT_RATE, create_invoice
from wattwise.models import BillingPeriod, Customer, Meter
from wattwise.money import round_eur
from wattwise.tariff import get_tariff

NOV_1 = date(2026, 11, 1)
DEC_1 = date(2026, 12, 1)


def _invoice(customer: Customer, meter: Meter, period: BillingPeriod):
    return create_invoice(
        customer,
        get_tariff("BASIC"),
        meter,
        period,
        reading(41210, NOV_1),
        reading(41455, DEC_1),
    )


def test_create_invoice_has_base_fee_and_energy_lines(customer, meter, november) -> None:
    invoice = _invoice(customer, meter, november)
    assert [line.description.split(" (")[0] for line in invoice.lines] == [
        "Base fee",
        "Energy",
    ]
    assert invoice.consumption_kwh == 245


def test_create_invoice_net_is_sum_of_lines(customer, meter, november) -> None:
    invoice = _invoice(customer, meter, november)
    assert invoice.net == sum(line.amount for line in invoice.lines)


def test_create_invoice_vat_is_computed_on_net(customer, meter, november) -> None:
    invoice = _invoice(customer, meter, november)
    assert invoice.vat == round_eur(invoice.net * VAT_RATE)
    assert invoice.gross == invoice.net + invoice.vat


def test_create_invoice_copies_customer_data(customer, meter, november) -> None:
    invoice = _invoice(customer, meter, november)
    assert invoice.customer_id == "C-1"
    assert invoice.tariff_name == "WattWise Basic"
    assert invoice.period == november


# Regression test for BUG-158
# Wiki Billing-Rules#full-example, WattWise Basic, November 2026, 247 kWh:
# base fee 9.90 * 12 / 365 * 30 = 9.7643... -> 9.76 (30 days, not 29)
# energy 247 * 0.3450 = 85.215 -> 85.22 · net 9.76 + 85.22 = 94.98
# VAT 94.98 * 0.19 = 18.0462 -> 18.05 · total 94.98 + 18.05 = 113.03
def test_create_invoice_matches_wiki_full_example(customer, meter, november) -> None:
    invoice = create_invoice(
        customer,
        get_tariff("BASIC"),
        meter,
        november,
        reading(41210, NOV_1),
        reading(41457, DEC_1),
    )
    assert [(line.description, line.amount) for line in invoice.lines] == [
        ("Base fee (30 days)", Decimal("9.76")),
        ("Energy (247 kWh)", Decimal("85.22")),
    ]
    assert invoice.net == Decimal("94.98")
    assert invoice.vat == Decimal("18.05")
    assert invoice.gross == Decimal("113.03")
