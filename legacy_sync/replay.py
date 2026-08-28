"""Replay the period's orders and registrations through the sync and print what happened.

    python -m legacy_sync.replay --data ../data
"""

import argparse
from collections import Counter

from .crm.client import CRMClient, InactiveOwner
from .registration.register import IdentityConflict, RegistrationBlocked, register_kit
from .store import load
from .sync.order_sync import sync_order


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="../data")
    args = parser.parse_args()
    t = load(args.data)

    owners_active = {a["owner_id"]: a["owner_active"] == "true" for a in t["crm_accounts"]}
    existing = [a for a in t["crm_accounts"] if a["created_at"] < "2026-06-15"]
    crm = CRMClient(existing, [], owners_active)
    customers = {c["customer_id"]: c for c in t["ecom_customers"]}
    orders = {o["order_id"]: o for o in t["ecom_orders"]}
    kits = {k["kit_barcode"]: k for k in t["kits"]}

    outcome = Counter()
    for order in sorted(t["ecom_orders"], key=lambda o: o["created_at"]):
        account = sync_order(crm, order, customers[order["customer_id"]])
        crm.opportunities[f"006R{len(crm.opportunities) + 1:06d}"] = {
            "opportunity_id": f"006R{len(crm.opportunities) + 1:06d}", "account_id": account["account_id"],
            "ecom_order_id": order["order_id"], "product": order["product_name"], "amount": order["amount"]}
        outcome["orders synced"] += 1

    for reg in sorted(t["portal_registrations"], key=lambda r: r["registered_at"]):
        try:
            register_kit(crm, reg, kits[reg["kit_barcode"]], orders)
            outcome["registrations accepted"] += 1
        except RegistrationBlocked:
            outcome["registrations blocked: duplicate rule"] += 1
        except IdentityConflict:
            outcome["registrations blocked: identity conflict"] += 1
        except InactiveOwner:
            outcome["registrations failed: inactive owner"] += 1

    print("Replay summary")
    for k, v in outcome.items():
        print(f"  {k}: {v}")
    print(f"  CRM accounts after replay: {len(crm.accounts)}")


if __name__ == "__main__":
    main()
