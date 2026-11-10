# Adversarial architecture review

## Scope

This review covers the deliverables in `claude/` against the case study brief.
It is a read-only review; the replay and tests were not run.

## Overall assessment

The current-state diagnosis is strong: it traces the six symptoms to code and replay evidence, separates observed behavior from assumptions, and models gifts as separate buyer, registrant and patient roles.
The target design also puts identity outside the CRM and allows registration to proceed while identity is unresolved.

The architecture is a good direction, but the matching safety rules and the registration reliability contract need more precision before implementation.
The `claude/` directory is also not a complete submission on its own.

## Findings

### High: The directory does not contain all required submission artifacts

`claude/` contains the three HTML documents and the replay trace, but no working slice, `identities.csv`, `review_queue.csv`, standalone build specification or `AI_LOG.md`.
The architecture page describes the working slice as its reference implementation, but no implementation is present in this directory.

The brief requires these artifacts in the submission.
If they live elsewhere, document the submission path and the command needed to run the slice.

References: `claude/docs/target-architecture.html:468`; case study brief, “A working slice,” “A build specification” and “How you use AI.”

### High: Automatic matching thresholds are not supported by enough validation detail

The design describes scores as calibrated probabilities and automatically links pairs at 0.90 or above.
It proposes checking weights against about 80 hand-labelled pairs and recalibrating monthly from review decisions.
That does not yet explain how the labels represent the population or how the automatic-link precision will be shown to be safe for data that can expose one person’s health information to another.

Some normalization rules can also collapse distinct identifiers.
Dropping plus tags may merge different addresses, and comparing only the last ten phone digits can create collisions across country codes.
The scoring table calls a birthdate difference a veto while allowing a one-digit transposition, but does not define when that exception applies.

Until these rules are validated, send those cases to review rather than auto-linking them.
Set the production threshold using a representative, independently labelled validation set and report false-match rates as well as precision.

References: `claude/docs/target-architecture.html:379-386`; `claude/docs/target-architecture.html:439-459`.

### High: “Registration never waits” needs an operational reliability contract

The design says the portal accepts the registration and queues events when the identity service is down.
It does not specify durable event capture, idempotency, retry behavior, duplicate submissions or recovery after a prolonged outage.
Those details determine whether acceptance can be trusted and whether the kit, chart and marketing state can reconcile without loss or duplication.

Specify the acceptance boundary, event ownership, idempotency key, retry policy, dead-letter handling and replay procedure.
Include behavior for a registration accepted by the portal when identity storage is unavailable.

References: `claude/docs/target-architecture.html:491-521`; `claude/docs/target-architecture.html:246-379`.

### Medium: The rollout milestones are ambiguous

The executive summary says to ensure the CRM cannot block registration in weeks 1–2, then says to switch registration to the person key in weeks 7–10.
These milestones can coexist if the first decouples portal acceptance from the CRM and the second changes identity resolution, but the distinction is not stated.

Name the week 1–2 change as an immediate registration-path decoupling, then reserve the later milestone for consuming identity results.

Reference: `claude/docs/executive-summary.html:90-97`.

### Medium: The marketing outcome is stated more definitively in the summary than the evidence allows

The detailed diagnosis says no code in the repository calls the stage helper and that the replay’s attribution to CRM accounts is an assumption.
The executive summary presents 60 kits with results as customers still being told to register, which reads as a confirmed campaign outcome.

Keep the assumption visible beside the summary figure, or describe the figure as a replay estimate under the stated account-attribution assumption.

References: `claude/docs/current-system.html:930-935`; `claude/docs/executive-summary.html:69-75`.

### Medium: Pseudonymous identifiers and kit stages need a tighter sharing boundary

The PHI section classifies `person_key` as pseudonymous and says it may go to any connected system.
It also permits marketing to receive a kit stage.
When those values are linked to a person or contact address, they can reveal participation in a health test, so pseudonymization alone should not be treated as a reason for unrestricted sharing.

Describe the key and stage as sensitive health-related data, limit each consumer to the fields it needs, and make the marketing vendor’s access and contract requirements explicit.

Reference: `claude/docs/target-architecture.html:524-591`.

### Medium: Consent merge behavior needs precise rules

“Strictest wins” is a sound safety direction, but the design does not define how unknown status behaves or how address-scoped opt-outs apply after a person merge.
Without those rules, separate addresses or channels could be treated as one preference, or an unknown value could be mistaken for permission.

Specify consent state, channel and address scope, source and timestamp, behavior for unknown values, and how a merge or split preserves the audit history.

References: `claude/docs/target-architecture.html:250-371`; `claude/docs/target-architecture.html:582-591`.

### Low: Email rewrite figures use different units

The diagnosis reports 77 orders that changed an email, while the executive summary reports 45 records rewritten by someone else’s order.
The two counts may both be valid, but their units and relationship are not explained where the figures appear.

Label both counts with their numerator and denominator, or use one clearly defined metric throughout.

References: `claude/docs/current-system.html:906-912`; `claude/docs/executive-summary.html:69-75`.

## Recommended order of work

1. Make the submission artifacts and run instructions discoverable.
2. Tighten match normalization and validate the auto-link threshold against representative labels.
3. Specify the durable registration and event-recovery contract.
4. Align the rollout language and qualify the marketing estimate.
5. Clarify PHI access and consent merge semantics.
