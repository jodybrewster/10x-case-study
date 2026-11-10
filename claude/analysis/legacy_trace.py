"""Trace the legacy sync replay and count how each order and registration was handled.

Imports legacy-sync and reads data/ without modifying either. The loop mirrors
legacy_sync/replay.py and adds bookkeeping around each call.

    python3 analysis/legacy_trace.py                        (run from claude/)
    python3 analysis/legacy_trace.py --interleave           (orders and registrations in time order)
    python3 analysis/legacy_trace.py --no-address-fallback  (what-if: config.py:5 off)
"""

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CUTOFF = "2026-06-15"  # same cutoff as legacy_sync/replay.py:22


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=str(ROOT / "data"))
    parser.add_argument("--legacy", default=str(ROOT / "legacy-sync"))
    parser.add_argument("--no-address-fallback", action="store_true")
    parser.add_argument("--interleave", action="store_true")
    parser.add_argument("--examples", type=int, default=3)
    args = parser.parse_args()

    sys.dont_write_bytecode = True
    sys.path.insert(0, args.legacy)
    from legacy_sync import config
    from legacy_sync.crm.client import CRMClient, DuplicateDetected, InactiveOwner
    from legacy_sync.crm.duplicate_rules import find_duplicates
    from legacy_sync.marketing.stage import stage_for_account
    from legacy_sync.registration.register import IdentityConflict, RegistrationBlocked, register_kit
    from legacy_sync.store import load, normalize_email
    from legacy_sync.sync.order_sync import sync_order

    if args.no_address_fallback:
        config.MATCH_FALLBACK_ADDRESS = False

    t = load(args.data)
    owners_active = {a["owner_id"]: a["owner_active"] == "true" for a in t["crm_accounts"]}
    existing = [a for a in t["crm_accounts"] if a["created_at"] < CUTOFF]
    crm = CRMClient(existing, [], owners_active)
    customers = {c["customer_id"]: c for c in t["ecom_customers"]}
    orders = {o["order_id"]: o for o in t["ecom_orders"]}
    kits = {k["kit_barcode"]: k for k in t["kits"]}

    email_history = defaultdict(list)  # account_id -> every primary email it has held
    for a in crm.accounts.values():
        email_history[a["account_id"]].append(normalize_email(a["primary_email"]))

    def note_emails():
        for aid, a in crm.accounts.items():
            e = normalize_email(a["primary_email"])
            if not email_history[aid] or email_history[aid][-1] != e:
                email_history[aid].append(e)

    c = Counter()
    ex = defaultdict(list)

    def example(key, text):
        if len(ex[key]) < args.examples:
            ex[key].append(text)

    # ------------------------------------------------------------------ orders
    def handle_order(order):
        cust = customers[order["customer_id"]]
        by_id = crm.find_by_ecom_customer_id(order["customer_id"])
        by_email = crm.find_by_email(order["order_email"])
        by_addr = crm.find_by_address(order["ship_name"].split()[-1], order["ship_zip"])
        if by_id:
            path, cands = "ecom id", by_id
        elif by_email:
            path, cands = "email", by_email
        elif config.MATCH_FALLBACK_ADDRESS and by_addr:
            path, cands = "address fallback", by_addr
        else:
            path, cands = "create account", []
        before_email = normalize_email(cands[0]["primary_email"]) if cands else None
        before_ecom_id = cands[0]["ecom_customer_id"] if cands else None

        try:
            account = sync_order(crm, order, cust)
        except DuplicateDetected:
            c["orders: sync raised DuplicateDetected (uncaught in replay.py)"] += 1
            return
        note_emails()
        n = len(crm.opportunities) + 1
        crm.opportunities[f"006R{n:06d}"] = {
            "opportunity_id": f"006R{n:06d}", "account_id": account["account_id"],
            "ecom_order_id": order["order_id"], "product": order["product_name"], "amount": order["amount"]}

        c[f"orders: resolved by {path}"] += 1
        if len(cands) > 1:
            c[f"orders: {path} had more than one candidate, took the first"] += 1
        if not cands:
            return
        wrong_first = account["first_name"].lower() != cust["first_name"].lower()
        if wrong_first:
            c[f"orders: {path} landed on an account with a different first name"] += 1
            if order["is_gift"] == "true":
                c[f"orders: {path} different first name, gift order"] += 1
            example(f"order via {path} on different first name",
                    f"{order['order_id']} buyer {cust['first_name']} {cust['last_name']} <{order['order_email']}> "
                    f"-> {account['account_id']} {account['first_name']} {account['last_name']} "
                    f"(email was {before_email})")
        if path == "address fallback":
            if not wrong_first:
                c["orders: address fallback, same first name (same person, new email)"] += 1
            if not before_ecom_id:
                c["orders: address fallback stamped the buyer's ecom id on the account"] += 1
            else:
                c["orders: address fallback, account already had another ecom id"] += 1
        if before_email != normalize_email(order["order_email"]):
            c["orders: primary email overwritten"] += 1
            c[f"orders: primary email overwritten after {path} match"] += 1
            if wrong_first:
                c["orders: primary email overwritten with a different person's email"] += 1

    # ----------------------------------------------------------- registrations
    reg_account = {}
    reg_result = {}
    def handle_reg(reg):
        kit = kits[reg["kit_barcode"]]
        order = orders[kit["order_id"]]
        gift = order["is_gift"] == "true"
        opp = next((o for o in crm.opportunities.values() if o["ecom_order_id"] == order["order_id"]), None)
        if opp is None:
            c["registrations: no opportunity for the kit's order"] += 1
            reg_result[reg["registration_id"]] = "no opportunity"
            return
        opp_account_before = opp["account_id"]
        matches = crm.find_by_email(reg["email"])
        remail = normalize_email(reg["email"])
        tag = " (gift)" if gift else ""
        try:
            account = register_kit(crm, reg, kit, orders)
        except RegistrationBlocked:
            result = "blocked: duplicate rule"
            fields = {"first_name": reg["first_name"], "last_name": reg["last_name"],
                      "mailing_zip": order["ship_zip"]}
            dupe = find_duplicates(crm.accounts.values(), fields)[0]
            hist = email_history[dupe["account_id"]]
            if remail in hist:
                why = "account once had this email, the order sync overwrote it"
            else:
                why = "registrant used an email the account never had"
            c[f"registrations: duplicate rule, {why}"] += 1
            dob = dupe["birthdate"]
            if dob in ("", config.DOB_PLACEHOLDER):
                c["registrations: duplicate rule, blocking account has no usable birthdate"] += 1
            elif dob == reg["birthdate"]:
                c["registrations: duplicate rule, blocking account has the same birthdate"] += 1
            else:
                c["registrations: duplicate rule, blocking account has a different birthdate"] += 1
            if gift:
                c["registrations: duplicate rule, gift order"] += 1
            example("registration blocked by duplicate rule",
                    f"{reg['registration_id']}{tag} {reg['first_name']} {reg['last_name']} <{remail}> blocked by "
                    f"{dupe['account_id']} <{normalize_email(dupe['primary_email'])}>, history {hist}")
        except IdentityConflict:
            result = "blocked: identity conflict"
            acct = matches[0]
            dob = acct["birthdate"]
            if acct["last_name"].lower() != reg["last_name"].lower():
                why = "last name differs"
            elif dob not in ("", config.DOB_PLACEHOLDER) and dob != reg["birthdate"]:
                why = "same last name, birthdate differs"
            else:
                why = "other"
            c[f"registrations: identity conflict, {why}"] += 1
            hist = email_history[acct["account_id"]]
            if hist[0] != remail and normalize_email(acct["secondary_email"]) != remail:
                c["registrations: identity conflict, account got this email from an order overwrite"] += 1
            if acct["first_name"].lower() == reg["first_name"].lower():
                c["registrations: identity conflict, same first name"] += 1
            if gift:
                c["registrations: identity conflict, gift order"] += 1
            example("registration identity conflict",
                    f"{reg['registration_id']}{tag} {reg['first_name']} {reg['last_name']} {reg['birthdate']} "
                    f"<{remail}> vs {acct['account_id']} {acct['first_name']} {acct['last_name']} "
                    f"{acct['birthdate'] or 'no dob'}, history {hist}")
        except InactiveOwner:
            result = "failed: inactive owner"
            if gift:
                c["registrations: inactive owner, gift order"] += 1
            example("registration failed on inactive owner",
                    f"{reg['registration_id']}{tag} {reg['first_name']} {reg['last_name']} <{remail}>, "
                    f"opportunity stays on {opp_account_before}")
        else:
            result = "accepted"
            reg_account[reg["registration_id"]] = account["account_id"]
            how = "email match" if matches else "new account"
            c[f"registrations: accepted via {how}"] += 1
            if len(matches) > 1:
                c["registrations: email matched more than one account, took the first"] += 1
            if matches and account["first_name"].lower() != reg["first_name"].lower():
                c["registrations: accepted onto an account with a different first name"] += 1
                if account["birthdate"] in ("", config.DOB_PLACEHOLDER):
                    c["registrations: ... of which checked on last name only (no usable birthdate)"] += 1
                example("registration accepted onto different first name",
                        f"{reg['registration_id']}{tag} {reg['first_name']} {reg['last_name']} {reg['birthdate']} "
                        f"-> {account['account_id']} {account['first_name']} {account['last_name']} "
                        f"{account['birthdate'] or 'no dob'}")
            if account["account_id"] != opp_account_before:
                if gift:
                    c["registrations: accepted, gift opportunity moved to the registrant"] += 1
                else:
                    c["registrations: accepted on a different account than the purchase (not a gift, not moved)"] += 1
        note_emails()
        c[f"registrations: {result}"] += 1
        if gift:
            c[f"registrations (gift): {result}"] += 1
        reg_result[reg["registration_id"]] = result

    # replay.py runs every order first and every registration second (replay.py:29, :36).
    # --interleave processes both in timestamp order, as production would have.
    events = [(o["created_at"], 0, o) for o in t["ecom_orders"]]
    events += [(r["registered_at"], 1, r) for r in t["portal_registrations"]]
    order_key = (lambda e: e[:2]) if args.interleave else (lambda e: (e[1], e[0]))
    for _, is_reg, row in sorted(events, key=order_key):
        (handle_reg if is_reg else handle_order)(row)

    flips = {aid: h for aid, h in email_history.items() if len(h) > 2}
    c["accounts: primary email changed at least once"] = sum(1 for h in email_history.values() if len(h) > 1)
    c["accounts: primary email changed two or more times"] = len(flips)
    for aid, h in list(flips.items())[:args.examples]:
        example("account email history", f"{aid} {crm.accounts[aid]['first_name']} {crm.accounts[aid]['last_name']}: "
                + " -> ".join(h))

    # ------------------------------------------------------------------ stages
    regs_by_kit = {r["kit_barcode"]: r for r in t["portal_registrations"]}
    registrations_by_account = defaultdict(list)
    results_by_account = defaultdict(list)
    for rid, aid in reg_account.items():
        registrations_by_account[aid].append(rid)
    for res in t["lab_results"]:
        reg = regs_by_kit.get(res["kit_barcode"])
        if reg and reg["registration_id"] in reg_account:
            results_by_account[reg_account[reg["registration_id"]]].append(res["result_id"])
    opps = list(crm.opportunities.values())
    opp_by_order = {o["ecom_order_id"]: o for o in opps}
    nagged = set()
    for res in t["lab_results"]:
        kit = kits[res["kit_barcode"]]
        opp = opp_by_order.get(kit["order_id"])
        if opp is None:
            continue
        reg = regs_by_kit[res["kit_barcode"]]
        stage = stage_for_account(opp["account_id"], opps, registrations_by_account, results_by_account)
        c[f"stage: kit has a final result, purchasing account is at '{stage}'"] += 1
        if stage != "results_ready":
            nagged.add(opp["account_id"])
            outcome = reg_result[reg["registration_id"]]
            if outcome != "accepted":
                why = f"registration {outcome}"
            elif orders[kit["order_id"]]["is_gift"] == "true":
                why = "gift, registration is on another account"
            else:
                why = "registration is on another account"
            c[f"stage: wrong stage because {why}"] += 1
            example("stale stage", f"{res['kit_barcode']} result {res['result_id']}: purchase on "
                    f"{opp['account_id']} at '{stage}', {why}")
    c["stage: accounts that would get the wrong nurture message"] = len(nagged)

    # ----------------------------------------------- consent in the CRM snapshot
    groups = defaultdict(list)
    for a in t["crm_accounts"]:
        if a["primary_email"]:
            groups[normalize_email(a["primary_email"])].append(a)
    shared = [g for g in groups.values() if len(g) > 1]
    c["consent: emails held by more than one account in crm_accounts.csv"] = len(shared)
    for field in ("sms_opt_out", "do_not_call"):
        mixed = [g for g in shared if len({a[field] for a in g}) > 1]
        c[f"consent: shared-email groups that disagree on {field}"] = len(mixed)
        for g in mixed[:args.examples]:
            example(f"consent disagreement on {field}",
                    ", ".join(f"{a['account_id']} {a['first_name']} {a['last_name']} {field}={a[field]}" for a in g))
    c["consent: accounts with sms_opt_out=true"] = sum(a["sms_opt_out"] == "true" for a in t["crm_accounts"])
    c["consent: accounts with do_not_call=true"] = sum(a["do_not_call"] == "true" for a in t["crm_accounts"])

    # ------------------------------------------ replay end state vs the snapshot
    pre_ids = {a["account_id"] for a in existing}
    for o in t["crm_opportunities"]:
        mine = opp_by_order.get(o["ecom_order_id"])
        if mine is None:
            continue
        if o["account_id"] in pre_ids and mine["account_id"] in pre_ids:
            same = "same" if o["account_id"] == mine["account_id"] else "different"
            c[f"snapshot: opportunity on a pre-cutoff account in both, {same} account"] += 1
        else:
            c["snapshot: opportunity on a post-cutoff account in the snapshot or the replay"] += 1
    c["snapshot: accounts in crm_accounts.csv"] = len(t["crm_accounts"])
    c["snapshot: accounts created before the replay cutoff"] = len(existing)
    c["snapshot: accounts after replay"] = len(crm.accounts)

    print(f"MATCH_FALLBACK_ADDRESS={config.MATCH_FALLBACK_ADDRESS} DUPLICATE_RULE_ACTION={config.DUPLICATE_RULE_ACTION} "
          f"interleave={args.interleave}")
    for k in sorted(c):
        print(f"  {c[k]:5d}  {k}")
    print()
    for k in sorted(ex):
        print(k)
        for line in ex[k]:
            print("   ", line)


if __name__ == "__main__":
    main()
