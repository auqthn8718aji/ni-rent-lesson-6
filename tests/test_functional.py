import pytest

from src.manager import Manager
from src.models import Bill, Parameters


def test_tenants_settlements_sum_equals_apartment_costs():
    manager = Manager(Parameters())

    apartment_settlement = manager.get_settlement('apart-polanka', 2025, 1)
    assert apartment_settlement.total_due_pln == 910.0

    tenants_settlements = manager.create_tenants_settlements(apartment_settlement)
    assert len(tenants_settlements) == 3

    tenants_total = sum(ts.total_due_pln for ts in tenants_settlements)
    assert tenants_total == apartment_settlement.total_due_pln
    assert tenants_total == manager.get_apartment_costs('apart-polanka', 2025, 1)


@pytest.mark.parametrize("bills_total", [1000.0, 910.0, 1234.57, 0.0])
@pytest.mark.parametrize("tenants_to_remove", [[], ['tenant-1'], ['tenant-1', 'tenant-2']])
def test_money_is_not_lost_or_created(bills_total, tenants_to_remove):
    manager = Manager(Parameters())
    manager.bills = [Bill(
        apartment='apart-polanka',
        date_due='2025-03-15',
        settlement_year=2025,
        settlement_month=2,
        amount_pln=bills_total,
        type='rent',
    )]
    for tenant_key in tenants_to_remove:
        del manager.tenants[tenant_key]

    apartment_settlement = manager.get_settlement('apart-polanka', 2025, 2)
    assert apartment_settlement.total_due_pln == bills_total

    tenants_settlements = manager.create_tenants_settlements(apartment_settlement)
    assert len(tenants_settlements) == 3 - len(tenants_to_remove)

    tenants_total = sum(ts.total_due_pln for ts in tenants_settlements)
    assert tenants_total == bills_total

#Annual report tests
def _apartment(key):
    return {key: {"key": key, "name": key, "location": "x", "area_m2": 50,
                  "rooms": {"r1": {"name": "R1", "area_m2": 20}}}}


def _bill(apartment, year, month, amount, type_='rent'):
    return {"amount_pln": amount, "date_due": f"{year}-{month:02d}-15",
            "apartment": apartment, "settlement_year": year,
            "settlement_month": month, "type": type_}


def _transfer(tenant, year, month, amount):
    return {"amount_pln": amount, "date": f"{year}-{month:02d}-05",
            "settlement_year": year, "settlement_month": month, "tenant": tenant}


def test_annual_report_aggregates_costs_and_revenues(make_manager):
    manager = make_manager(
        apartments={**_apartment('a1'), **_apartment('a2')},
        bills=[
            _bill('a1', 2025, 1, 760.0), _bill('a1', 2025, 2, 150.0, 'electricity'),
            _bill('a2', 2025, 3, 500.0),
        ],
        transfers=[_transfer('t1', 2025, 1, 1000.0), _transfer('t2', 2025, 2, 700.0)],
    )

    report = manager.get_annual_report(2025)

    assert report.year == 2025
    assert report.total_costs_pln == 1410.0
    assert report.total_revenues_pln == 1700.0
    assert report.balance_pln == 290.0
    assert report.costs_by_apartment == {'a1': 910.0, 'a2': 500.0}
    assert report.costs_by_type == {'rent': 1260.0, 'electricity': 150.0}


def test_annual_report_ignores_other_years(make_manager):
    manager = make_manager(
        apartments=_apartment('a1'),
        bills=[_bill('a1', 2024, 12, 999.0), _bill('a1', 2025, 1, 100.0), _bill('a1', 2026, 1, 888.0)],
        transfers=[_transfer('t1', 2024, 12, 999.0), _transfer('t1', 2025, 1, 150.0)],
    )

    report = manager.get_annual_report(2025)

    assert report.total_costs_pln == 100.0
    assert report.total_revenues_pln == 150.0


def test_annual_report_for_year_without_data_is_all_zeros(make_manager):
    manager = make_manager(apartments=_apartment('a1'), bills=[_bill('a1', 2025, 1, 100.0)])

    report = manager.get_annual_report(2020)

    assert report.total_costs_pln == 0.0
    assert report.total_revenues_pln == 0.0
    assert report.balance_pln == 0.0
    assert report.costs_by_apartment == {}
    assert report.costs_by_type == {}


def test_annual_report_breakdowns_sum_to_total_costs(make_manager):
    manager = make_manager(
        apartments={**_apartment('a1'), **_apartment('a2')},
        bills=[
            _bill('a1', 2025, 1, 760.0), _bill('a1', 2025, 1, 150.0, 'electricity'),
            _bill('a2', 2025, 2, 500.0, 'water'),
        ],
    )

    report = manager.get_annual_report(2025)

    assert sum(report.costs_by_apartment.values()) == report.total_costs_pln
    assert sum(report.costs_by_type.values()) == report.total_costs_pln