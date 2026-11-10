"""Pair scoring: transparent additive log-odds, mapped to 0..1 with a logistic.

score = sigmoid(BIAS + sum of weights). Every weight is in the table below so a
reviewer can read why a pair scored what it did. The reason codes name the terms used.
"""
import math

BIAS = -4.0
W = {
    "first_agree": 2.0,       # equal after nickname mapping
    "first_differ": -4.0,     # relatives and household members land here
    "last_agree": 1.5,
    "last_differ": -2.5,      # could be a name change, so not a veto
    "birthdate_agree": 4.0,
    "email_exact": 4.0,
    "email_exact_weak": 3.0,  # one side is a CRM address (contaminated by the legacy sync)
    "email_dotless": 1.5,     # same address once dots are removed
    "email_plus_tag": 1.5,    # same address once a +tag is removed: review only, never auto
    "phone_agree": 1.5,       # shared by relatives, so household evidence at most
    "household_agree": 0.8,   # same street number and zip
    "related_buyer": 1.0,     # kit/order/CRM-stamp relationship, only if full name also agrees
}
# Provisional thresholds. Scores are a logistic of hand-set weights: they rank pairs,
# they are not calibrated probabilities. AUTO stays provisional until the false-match
# rate has been measured on a random sample of auto links (see analysis/evaluate.py).
AUTO = 0.90
REVIEW = 0.60
# A pair carrying this reason is never linked automatically, whatever it scores.
REVIEW_ONLY = "email_plus_tag_variant_review_only"


def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))


def score_pair(a, b):
    """Return (score, reasons, vetoed)."""
    reasons = []
    if a.bd and b.bd and a.bd != b.bd:
        return 0.0, ["birthdate_conflict"], True
    s = BIAS
    first_ok = a.canon_first == b.canon_first
    last_ok = a.last_norm == b.last_norm
    if first_ok:
        s += W["first_agree"]; reasons.append("first_name_agree")
    else:
        s += W["first_differ"]; reasons.append("first_name_differs")
    if last_ok:
        s += W["last_agree"]; reasons.append("surname_agree")
    else:
        s += W["last_differ"]; reasons.append("surname_differs")
    if a.bd and b.bd:
        s += W["birthdate_agree"]; reasons.append("birthdate_agree")
    else:
        reasons.append("birthdate_missing")
    shared = a.emails & b.emails
    if shared:
        weak = a.weak_email or b.weak_email
        s += W["email_exact_weak" if weak else "email_exact"]
        reasons.append("email_shared_crm_weak" if weak else "email_shared")
    elif a.email_keys & b.email_keys:
        s += W["email_dotless"]; reasons.append("email_dot_variant")
    elif (a.email_bases & (b.emails | b.email_bases)) or (b.email_bases & a.emails):
        s += W["email_plus_tag"]; reasons.append(REVIEW_ONLY)
    if a.phone and a.phone == b.phone:
        s += W["phone_agree"]; reasons.append("phone_shared")
    if a.hh and a.hh == b.hh:
        s += W["household_agree"]; reasons.append("same_household_address")
    if first_ok and last_ok:
        ids_a = {("ecommerce", i) for i in a.related_buyers}
        ids_b = {("ecommerce", i) for i in b.related_buyers}
        if (a.system == "ecommerce" and a.rid in b.related_buyers) or \
           (b.system == "ecommerce" and b.rid in a.related_buyers) or (a.related_buyers & b.related_buyers):
            s += W["related_buyer"]; reasons.append("record_relationship_name_agrees")
    return sigmoid(s), reasons, False
