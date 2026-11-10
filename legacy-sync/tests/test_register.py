import pytest

from legacy_sync.crm.client import CRMClient
from legacy_sync.registration.register import IdentityConflict, register_kit
from tests.test_order_sync import _account

ORDERS = {"#1": {"order_id": "#1", "is_gift": "false", "ship_address1": "1 Oak St", "ship_city": "Phoenix",
                 "ship_state": "AZ", "ship_zip": "85012"}}
KIT = {"kit_barcode": "KT1", "order_id": "#1"}
OPP = {"opportunity_id": "006A1", "account_id": "001A000001", "ecom_order_id": "#1"}


def _reg(**kw):
    base = {"registration_id": "R1", "email": "ana@x.com", "first_name": "Ana", "last_name": "Lopez",
            "birthdate": "1985-02-03", "phone": "6025550101"}
    base.update(kw)
    return base


def test_registration_attaches_to_buyer():
    crm = CRMClient([_account()], [OPP], {})
    assert register_kit(crm, _reg(), KIT, ORDERS)["account_id"] == "001A000001"


def test_registration_with_someone_elses_email_is_rejected():
    crm = CRMClient([_account()], [OPP], {})
    with pytest.raises(IdentityConflict):
        register_kit(crm, _reg(first_name="Maya", birthdate="2008-07-01", last_name="Reyes"), KIT, ORDERS)
