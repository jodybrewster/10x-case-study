"""Merge two CRM accounts that belong to the same person."""

MERGE_FIELDS = ("first_name", "last_name", "primary_email", "phone", "birthdate",
                "mailing_street", "mailing_city", "mailing_state", "mailing_zip", "ecom_customer_id")


def merge_accounts(crm, survivor_id, loser_id):
    survivor = crm.accounts[survivor_id]
    loser = crm.accounts.pop(loser_id)
    for field in MERGE_FIELDS:
        if not survivor.get(field) and loser.get(field):
            survivor[field] = loser[field]
    if loser["primary_email"] and loser["primary_email"] != survivor["primary_email"]:
        survivor["secondary_email"] = loser["primary_email"]
    for opp in crm.opportunities.values():
        if opp["account_id"] == loser_id:
            opp["account_id"] = survivor_id
    return survivor
