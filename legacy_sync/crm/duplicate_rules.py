from .. import config


def find_duplicates(existing_accounts, fields):
    """Return existing accounts the CRM would treat as duplicates of `fields`."""
    keys = config.DUPLICATE_RULE_FIELDS
    target = tuple((fields.get(k) or "").strip().lower() for k in keys)
    if not all(target):
        return []
    return [a for a in existing_accounts
            if tuple((a.get(k) or "").strip().lower() for k in keys) == target]
