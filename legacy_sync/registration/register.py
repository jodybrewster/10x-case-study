"""Kit registration from the member portal."""

from .. import config
from ..crm.client import DuplicateDetected


class RegistrationBlocked(Exception):
    pass


class IdentityConflict(Exception):
    pass


def _same_person(account, reg):
    dob = account["birthdate"]
    if dob in ("", config.DOB_PLACEHOLDER):
        return account["last_name"].lower() == reg["last_name"].lower()
    return dob == reg["birthdate"] and account["last_name"].lower() == reg["last_name"].lower()


def register_kit(crm, reg, kit, orders_by_id):
    """Register a kit. The registrant's CRM account must be resolved before the kit
    is accepted, so downstream systems always have a person to attach results to."""
    order = orders_by_id[kit["order_id"]]
    opp = next(o for o in crm.opportunities.values() if o["ecom_order_id"] == order["order_id"])

    matches = crm.find_by_email(reg["email"])
    if matches:
        account = matches[0]
        if not _same_person(account, reg):
            raise IdentityConflict(
                f"registration {reg['registration_id']}: email belongs to account {account['account_id']}")
    else:
        try:
            account = crm.create_account({
                "first_name": reg["first_name"], "last_name": reg["last_name"],
                "primary_email": reg["email"], "phone": reg["phone"], "birthdate": reg["birthdate"],
                "mailing_street": order["ship_address1"], "mailing_city": order["ship_city"],
                "mailing_state": order["ship_state"], "mailing_zip": order["ship_zip"],
            })
        except DuplicateDetected as exc:
            raise RegistrationBlocked(str(exc)) from exc

    if order["is_gift"] == "true" and opp["account_id"] != account["account_id"]:
        crm.move_opportunity(opp["opportunity_id"], account["account_id"])

    return account
