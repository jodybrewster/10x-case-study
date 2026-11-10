## What they’re asking for

The brief estimates **6 to 8 hours**. It asks you to:

- Explain how the current sync works and diagnose the six reported customer-data problems, citing code locations.
- Design a single customer identity across e-commerce, CRM, the member portal, and the EHR, including how you handle uncertain matches and protect health information.
- Build a runnable prototype that reads the supplied data and writes `identities.csv` (one row per source record, with a person key and confidence) and `review_queue.csv` (uncertain links with reasons).
- Write a precise build spec for one part of the design, a 90-day rollout plan, and a one-page executive summary.
- Add `AI_[LOG.md](http://LOG.md)` describing the tools you used, examples where AI helped and where it was wrong, and transcripts if available.

They want a repository or zip with the code, both CSVs, the AI log, and your written answers. The review is 90 minutes: about 30 minutes presenting, 20 minutes navigating code live, 20 minutes discussing a changed requirement, and 20 minutes for questions. The brief says the company and records are fictional, but asks you to design as if the data were protected health information. BRIEF.pdf

## What stands out in the code

There are several concrete issues to investigate and explain:

- **Orders can attach to the wrong household member:** when ID and email lookups fail, the sync can match on last name and ZIP, then take the first result. legacy-sync/legacy_sync/sync/order\_[sync.py](http://sync.py) legacy-sync/legacy_sync/crm/[client.py](http://client.py)
- **CRM email can be overwritten:** each order updates the matched account’s primary email from the order email. legacy-sync/legacy_sync/crm/[client.py](http://client.py) legacy-sync/legacy_sync/sync/order\_[sync.py](http://sync.py)
- **Registrations can be blocked as duplicates:** account creation is blocked when first name, last name, and ZIP match another account. The registration code turns that block into a failed registration. legacy-sync/legacy_sync/crm/duplicate\_[rules.py](http://rules.py) legacy-sync/legacy_sync/registration/[register.py](http://register.py)
- **Some gift moves can fail:** the registration flow moves the opportunity to the registrant, but the CRM stand-in rejects moves to accounts owned by inactive users. legacy-sync/legacy_sync/registration/[register.py](http://register.py) legacy-sync/legacy_sync/crm/[client.py](http://client.py)
- **Opt-out can be lost during account merges:** the merge omits consent fields, while new accounts default to opted in. legacy-sync/legacy_sync/consent/[merge.py](http://merge.py) legacy-sync/legacy_sync/crm/[client.py](http://client.py)

For the marketing symptom, be careful about the claim: the stage helper returns `results_ready` first when it receives results keyed by account, but this repo doesn’t show how results get mapped to accounts. That leaves an identity-linking gap to investigate, rather than a confirmed bug in the helper itself. legacy-sync/legacy_sync/marketing/[stage.py](http://stage.py)

## Suggested next steps

1. Reply to the recruiter with a few windows for the 90-minute review and ask when they’d like the submission.
2. Work through the six symptoms, clearly marking what the code proves and what needs validation against the data.
3. Build the identity resolver with a review queue for uncertain matches. The key design constraint is that registration must continue even when identity is unresolved; reconciliation can happen afterward.
4. Package the prototype, written deliverables, and AI log, then prepare a short presentation and a few code-navigation examples.