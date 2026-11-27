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
    assert tenants_total == pytest.approx(apartment_settlement.total_due_pln, abs=0.005)
    assert tenants_total == pytest.approx(manager.get_apartment_costs('apart-polanka', 2025, 1), abs=0.005)


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
    assert apartment_settlement.total_due_pln == pytest.approx(bills_total)

    tenants_settlements = manager.create_tenants_settlements(apartment_settlement)
    assert len(tenants_settlements) == 3 - len(tenants_to_remove)

    tenants_total = sum(ts.total_due_pln for ts in tenants_settlements)
    assert tenants_total == pytest.approx(bills_total, abs=0.005)