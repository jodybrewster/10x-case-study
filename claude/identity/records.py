"""Load the eight CSVs into a flat list of Record objects (one per customer record)."""
import csv
import os
from dataclasses import dataclass, field

from . import normalize as N

SYSTEMS = ("ecommerce", "crm", "portal", "ehr")


@dataclass
class Record:
    system: str
    rid: str
    first: str
    last: str
    canon_first: str
    last_norm: str
    bd: object            # str or None
    emails: set = field(default_factory=set)
    email_keys: set = field(default_factory=set)
    phone: str = ""
    zip: str = ""
    hh: str = ""          # street number + zip
    weak_email: bool = False   # CRM emails are contaminated by the legacy sync
    related_buyers: set = field(default_factory=set)   # ecom customer ids tied by a RECORD relationship
    relation_kind: str = ""
    email_bases: set = field(default_factory=set)   # +tag removed; review-only evidence

    @property
    def uid(self):
        return (self.system, self.rid)


def _read(path, name):
    with open(os.path.join(path, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load(data_dir):
    ecom = _read(data_dir, "ecom_customers.csv")
    crm = _read(data_dir, "crm_accounts.csv")
    portal = _read(data_dir, "portal_registrations.csv")
    ehr = _read(data_dir, "ehr_patients.csv")
    orders = {r["order_id"]: r for r in _read(data_dir, "ecom_orders.csv")}
    kits = {r["kit_barcode"]: r for r in _read(data_dir, "kits.csv")}
    opps = _read(data_dir, "crm_opportunities.csv")
    labs = _read(data_dir, "lab_results.csv")

    recs = []

    def mk(system, rid, r, emails, bd, street, zip_, weak=False):
        em = {e for e in (N.norm_email(x) for x in emails) if e}
        x = Record(system, rid, r["first_name"], r["last_name"], N.canon_first(r["first_name"]),
                   N.norm_name(r["last_name"]), N.norm_birthdate(bd), em,
                   {N.email_dot_key(e) for e in em}, phone=N.norm_phone(r.get("phone", "")),
                   zip=N.norm_zip(zip_), hh=N.household_key(street, zip_), weak_email=weak)
        x.email_bases = {b for b in (N.email_plus_base(e) for e in em) if b}
        return x

    for r in ecom:
        recs.append(mk("ecommerce", r["customer_id"], r, [r["email"]], None, r["default_address1"], r["default_zip"]))
    for r in crm:
        x = mk("crm", r["account_id"], r, [r["primary_email"], r["secondary_email"]], r["birthdate"],
               r["mailing_street"], r["mailing_zip"], weak=True)
        if r["ecom_customer_id"]:
            x.related_buyers.add(r["ecom_customer_id"])
        recs.append(x)
    for r in portal:
        recs.append(mk("portal", r["registration_id"], r, [r["email"]], r["birthdate"], "", ""))
    for r in ehr:
        recs.append(mk("ehr", r["chart_id"], r, [r["email"]], r["birthdate"], "", ""))

    by = {x.uid: x for x in recs}
    # CRM opportunity -> order -> customer: same weak record relationship as ecom_customer_id
    for o in opps:
        order = orders.get(o["ecom_order_id"])
        acct = by.get(("crm", o["account_id"]))
        if order and acct:
            acct.related_buyers.add(order["customer_id"])
    # registration -> kit -> order -> buyer (record relationship, not identity)
    reg_kit = {}
    for r in portal:
        reg_kit[r["registration_id"]] = r["kit_barcode"]
        kit = kits.get(r["kit_barcode"])
        order = orders.get(kit["order_id"]) if kit else None
        if order:
            by[("portal", r["registration_id"])].related_buyers.add(order["customer_id"])
    # deterministic: registration -> lab result -> chart (same kit barcode)
    kit_to_reg = {r["kit_barcode"]: r["registration_id"] for r in portal}
    det = []
    for l in labs:
        reg = kit_to_reg.get(l["kit_barcode"])
        if reg and ("ehr", l["chart_id"]) in by:
            det.append((("portal", reg), ("ehr", l["chart_id"]), l))
    return recs, det
