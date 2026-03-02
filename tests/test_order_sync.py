from legacy_sync.crm.client import CRMClient
from legacy_sync.sync.order_sync import sync_order


def _account(**kw):
    base = {"account_id": "001A000001", "first_name": "Ana", "last_name": "Lopez", "primary_email": "ana@x.com",
            "secondary_email": "", "phone": "6025550101", "birthdate": "1985-02-03", "mailing_street": "1 Oak St",
            "mailing_city": "Phoenix", "mailing_state": "AZ", "mailing_zip": "85012", "ecom_customer_id": "",
            "owner_id": "U001", "owner_active": "true", "sms_opt_out": "false", "do_not_call": "false"}
    base.update(kw)
    return base


ORDER = {"order_id": "#1", "customer_id": "9001", "order_email": "ana@x.com", "ship_name": "Ana Lopez",
         "ship_address1": "1 Oak St", "ship_city": "Phoenix", "ship_state": "AZ", "ship_zip": "85012"}
CUSTOMER = {"customer_id": "9001", "first_name": "Ana", "last_name": "Lopez", "phone": "602-555-0101"}


def test_matches_existing_account_by_email():
    crm = CRMClient([_account()], [], {})
    assert sync_order(crm, ORDER, CUSTOMER)["account_id"] == "001A000001"
