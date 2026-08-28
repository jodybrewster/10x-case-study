"""Lifecycle stage used by marketing nurtures."""

STAGES = ["bought", "registered", "results_ready"]


def stage_for_account(account_id, opportunities, registrations_by_account, results_by_account):
    """The customer's current stage, from the records on their CRM account."""
    if results_by_account.get(account_id):
        return "results_ready"
    if registrations_by_account.get(account_id):
        return "registered"
    if any(o["account_id"] == account_id for o in opportunities):
        return "bought"
    return None
