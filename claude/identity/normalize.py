"""Field normalisation. Pure functions, no I/O."""
import re
import unicodedata

UNKNOWN_BIRTHDATES = {"", "1920-01-01"}

# nickname -> canonical first name
NICKNAMES = {
    "tony": "anthony", "rick": "richard", "ricky": "richard", "rich": "richard", "dick": "richard",
    "bob": "robert", "rob": "robert", "bobby": "robert", "robbie": "robert",
    "jess": "jessica", "jessie": "jessica", "bill": "william", "billy": "william", "will": "william",
    "willy": "william", "matt": "matthew", "joe": "joseph", "joey": "joseph", "drew": "andrew",
    "andy": "andrew", "jen": "jennifer", "jenny": "jennifer", "dan": "daniel", "danny": "daniel",
    "josh": "joshua", "nate": "nathan", "nat": "nathan", "trish": "patricia", "tricia": "patricia",
    "pat": "patricia", "patty": "patricia", "mike": "michael", "mikey": "michael", "tom": "thomas",
    "tommy": "thomas", "jim": "james", "jimmy": "james", "jamie": "james", "liz": "elizabeth",
    "beth": "elizabeth", "lizzie": "elizabeth", "betty": "elizabeth", "becky": "rebecca",
    "becca": "rebecca", "steve": "steven", "stephen": "steven", "chris": "christopher",
    "kate": "katherine", "katie": "katherine", "kathy": "katherine", "sue": "susan", "suzy": "susan",
    "barb": "barbara", "babs": "barbara", "maggie": "margaret", "peggy": "margaret",
    "sandy": "sandra", "mandy": "amanda", "manda": "amanda", "ben": "benjamin", "sam": "samuel",
    "alex": "alexander", "ken": "kenneth", "kenny": "kenneth", "ed": "edward", "eddie": "edward",
    "ted": "edward", "greg": "gregory", "jeff": "jeffrey", "larry": "lawrence", "nick": "nicholas",
    "pete": "peter", "tim": "timothy", "zach": "zachary", "zack": "zachary", "abby": "abigail",
    "mel": "melissa", "missy": "melissa", "cindy": "cynthia", "deb": "deborah", "debbie": "deborah",
    "vicky": "victoria", "vicki": "victoria", "mary": "mary", "maria": "maria",
}


def _fold(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.casefold().strip()


def norm_email(e):
    e = _fold(e)
    return e if "@" in e else ""


def email_dot_key(e):
    """Dot-insensitive variant: local part without dots. A +tag is kept, so tagged addresses stay distinct."""
    e = norm_email(e)
    if not e:
        return ""
    local, domain = e.rsplit("@", 1)
    return f"{local.replace('.', '')}@{domain}"


def email_plus_base(e):
    """The address with its +tag removed, or "" when it has none.

    Whether a tagged address is the same mailbox depends on the mail provider, so a
    match on this key is evidence for a reviewer and never for an automatic link.
    """
    e = norm_email(e)
    if not e or "+" not in e.rsplit("@", 1)[0]:
        return ""
    local, domain = e.rsplit("@", 1)
    return f"{local.split('+', 1)[0]}@{domain}"


def norm_phone(p):
    """US national number as 10 digits. Other country codes keep every digit, so they only match exactly."""
    d = re.sub(r"\D", "", p or "")
    if len(d) == 10:
        return d
    if len(d) == 11 and d[0] == "1":
        return d[1:]
    return f"+{d}" if len(d) > 10 else ""


def norm_name(n):
    return re.sub(r"[^a-z]", "", _fold(n))


def canon_first(n):
    n = norm_name(n)
    return NICKNAMES.get(n, n)


def norm_birthdate(b):
    b = (b or "").strip()
    return None if b in UNKNOWN_BIRTHDATES else b


def street_number(street):
    m = re.match(r"\s*(\d+)", street or "")
    return m.group(1) if m else ""


def norm_zip(z):
    return re.sub(r"\D", "", z or "")[:5]


def household_key(street, zip_):
    n, z = street_number(street), norm_zip(zip_)
    return f"{n}|{z}" if n and z else ""
