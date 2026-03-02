"""In-memory stand-in for the CRM API used by the sync jobs."""

from .. import config
from ..store import normalize_email
from .duplicate_rules import find_duplicates


class DuplicateDetected(Exception):
    pass


class InactiveOwner(Exception):
    pass


class CRMClient:
    def __init__(self, accounts, opportunities, owners_active):
        self.accounts = {a["account_id"]: dict(a) for a in accounts}
        self.opportunities = {o["opportunity_id"]: dict(o) for o in opportunities}
        self.owners_active = owners_active
        self._seq = len(self.accounts)

    # ---------------------------------------------------------------- lookups
    def find_by_ecom_customer_id(self, customer_id):
        return [a for a in self.accounts.values() if a["ecom_customer_id"] == customer_id]

    def find_by_email(self, email):
        e = normalize_email(email)
        return [a for a in self.accounts.values()
                if normalize_email(a["primary_email"]) == e or normalize_email(a["secondary_email"]) == e]

    def find_by_address(self, last_name, zip_code):
        return [a for a in self.accounts.values()
                if a["last_name"].lower() == (last_name or "").lower() and a["mailing_zip"] == zip_code]

    # ---------------------------------------------------------------- writes
    def create_account(self, fields):
        dupes = find_duplicates(self.accounts.values(), fields)
        if dupes and config.DUPLICATE_RULE_ACTION == "block":
            raise DuplicateDetected(f"possible duplicate of {[d['account_id'] for d in dupes]}")
        self._seq += 1
        account = {"account_id": f"001N{self._seq:06d}", "secondary_email": "", "ecom_customer_id": "",
                   "owner_id": "U001", "owner_active": "true", "sms_opt_out": "false", "do_not_call": "false",
                   **fields}
        self.accounts[account["account_id"]] = account
        return account

    def update_contact_details(self, account_id, email=None, phone=None):
        """Keep the account's contact details current with the latest touchpoint."""
        account = self.accounts[account_id]
        if email:
            account["primary_email"] = email
        if phone:
            account["phone"] = phone
        return account

    def move_opportunity(self, opportunity_id, to_account_id):
        account = self.accounts[to_account_id]
        if account.get("owner_active") == "false":
            raise InactiveOwner(f"account {to_account_id} is owned by inactive user {account['owner_id']}")
        self.opportunities[opportunity_id]["account_id"] = to_account_id
