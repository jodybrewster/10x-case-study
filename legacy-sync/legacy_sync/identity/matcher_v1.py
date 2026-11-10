"""Fuzzy person matcher.

Scores two person records on name, email, phone and date of birth.
"""

from difflib import SequenceMatcher

from ..store import normalize_email, normalize_phone

WEIGHTS = {"name": 0.3, "email": 0.3, "phone": 0.2, "dob": 0.2}
THRESHOLD = 0.75


def score(a, b):
    name = SequenceMatcher(None, f"{a['first_name']} {a['last_name']}".lower(),
                           f"{b['first_name']} {b['last_name']}".lower()).ratio()
    email = 1.0 if normalize_email(a.get("primary_email") or a.get("email")) == \
        normalize_email(b.get("primary_email") or b.get("email")) else 0.0
    phone = 1.0 if normalize_phone(a.get("phone")) == normalize_phone(b.get("phone")) else 0.0
    dob = 1.0 if (a.get("birthdate") or "") == (b.get("birthdate") or "") and a.get("birthdate") else 0.0
    return sum(WEIGHTS[k] * v for k, v in {"name": name, "email": email, "phone": phone, "dob": dob}.items())


def is_match(a, b):
    return score(a, b) >= THRESHOLD
