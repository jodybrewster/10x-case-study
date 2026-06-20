"""Push e-commerce orders into the CRM as opportunities."""

from .. import config


def resolve_account(crm, order, customer):
    """Find the CRM account for an order.

    Accounts are matched strictly by the customer's email address, so an order is
    only ever attached to the person who placed it.
    """
    by_id = crm.find_by_ecom_customer_id(order["customer_id"])
    if by_id:
        return by_id[0]

    by_email = crm.find_by_email(order["order_email"])
    if by_email:
        return by_email[0]

    if config.MATCH_FALLBACK_ADDRESS:
        last_name = order["ship_name"].split()[-1]
        by_address = crm.find_by_address(last_name, order["ship_zip"])
        if by_address:
            return by_address[0]

    return None


def sync_order(crm, order, customer):
    account = resolve_account(crm, order, customer)
    if account is None:
        account = crm.create_account({
            "first_name": customer["first_name"], "last_name": customer["last_name"],
            "primary_email": order["order_email"], "phone": customer["phone"], "birthdate": "",
            "mailing_street": order["ship_address1"], "mailing_city": order["ship_city"],
            "mailing_state": order["ship_state"], "mailing_zip": order["ship_zip"],
            "ecom_customer_id": order["customer_id"],
        })
    elif not account["ecom_customer_id"]:
        account["ecom_customer_id"] = order["customer_id"]
    return account
