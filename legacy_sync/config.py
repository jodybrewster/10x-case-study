"""Runtime settings for the sync service."""

# Mirrors the CRM's person-account duplicate rule. "block" rejects the create call,
# "alert" allows it and flags the record.
DUPLICATE_RULE_ACTION = "block"

# Fields the CRM duplicate rule compares on create.
DUPLICATE_RULE_FIELDS = ("first_name", "last_name", "mailing_zip")

# Placeholder some intake forms write when date of birth is unknown.
DOB_PLACEHOLDER = "1920-01-01"
