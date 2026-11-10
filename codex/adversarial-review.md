# Adversarial review of the Codex deliverables

Reviewed on 2026-11-09 from a solution architect's seat.

## Scope and method

This review covers the three pages in this directory: [current-system-diagnosis.html](current-system-diagnosis.html), [future-state-target-architecture.html](future-state-target-architecture.html) and [executive-summary.html](executive-summary.html).
Each page was read against [BRIEF.md](../BRIEF.md), the source in [legacy-sync/](../legacy-sync/) and the CSVs in [data/](../data/).
Every count quoted in the diagnosis page was recomputed from the CSVs.
Replay figures that go beyond the shipped summary come from the instrumented replay in [claude/analysis/legacy_trace.py](../claude/analysis/legacy_trace.py).
No patient-level values are reproduced here.

## Verdict

The work is accurate but incomplete.
It covers three of the seven deliverables in the brief.
It hedges where the brief asks for a position.
The diagnosis stops short on symptom 5 even though the supplied code and data are enough to explain it, and it misses that the six symptoms form one causal chain.

## What holds up

All recomputed counts match the diagnosis page.
That includes the 873, 6 and 26 split of opportunity links by customer ID, email and address, the replay outcomes of 401 accepted, 20 duplicate blocks, 11 identity conflicts and 1 inactive owner, the 87 duplicate-rule groups covering 181 accounts and the 520 e-commerce IDs of which 518 are distinct.

The file and line references for symptoms 1, 2, 3 and 6 point at the right code.
The commit hashes in the history note are right.

Keeping buyer, recipient, registrant and patient as separate roles is the right core idea.
The data backs it: there are 30 gift orders and the gift-recipient field is blank on all 905 opportunities.

Holding consent by channel and purpose, apart from identity, with the most restrictive state winning on a merge answers symptom 6 directly.

The pages show good hygiene with protected health information.
No names, emails, birthdates or result values appear.

The note on `matcher_v1.py` is a good find.
Two blank emails and two blank phones each score as a match, so two records with the same name and nothing else reach 0.8 against a 0.75 threshold.

## Where the diagnosis falls short

### Symptom 5 is traceable

The page marks symptom 5 as "not established by supplied code".
The cause can be traced from what was supplied.
`marketing/stage.py:6-14` computes the stage per CRM account.
The purchase sits on one account while the registration sits on another account or was rejected, so the purchasing account never leaves "bought".
The instrumented replay finds 59 kits with a final result whose purchasing account is still at "bought".
Of those, 36 have the registration on a different account, 15 had the registration blocked by the duplicate rule and 9 had it blocked by an identity conflict.
The campaign sender is absent from the repository, but the stage it would read is already wrong.

### The symptoms are a chain

The page treats the six symptoms as six separate bugs.
They are linked.
The address fallback at `sync/order_sync.py:20-24` puts an order on a relative's account.
`sync/order_sync.py:42` then overwrites that account's primary email with the buyer's order email.
When the relative later registers a kit, the email lookup at `registration/register.py:28` finds nothing, the flow tries to create an account and the duplicate rule blocks it.
In the replay, 16 of the 20 duplicate blocks hit an account that once held the registrant's email before an order overwrote it.
Six of the 11 identity conflicts trace to an overwritten email.
The blocked registrations then feed symptom 5.
This is the most important finding in the codebase and the page does not have it.

### Two code behaviours are missing

`sync/order_sync.py:39-40` stamps the buyer's e-commerce customer ID onto any matched account that has none, including one reached through the address fallback.
This happened on 6 of the 43 fallback matches in the replay.
It makes a wrong link permanent on the strongest lookup, so every later order from that buyer goes to the same wrong account by ID.

`registration/register.py:15-19` compares last name only when the account's birthdate is blank or the `1920-01-01` placeholder.
A registration can therefore be accepted onto a relative's account without any error.
The trace shows 11 registrations accepted onto an account with a different first name.
These sit inside the 401 "accepted" count, which the page reports without qualification.

### Symptom 4 is under-called

The page labels symptom 4 a "specific failure path".
`crm/client.py:57-61` refuses to move an opportunity to an account with an inactive owner, which is exactly "support can't move the purchase to the recipient".
That half of the symptom is confirmed.
The other half, gift registrations failing, is confirmed by the 4 duplicate blocks and 5 identity conflicts among the 25 gift registrations.

### The change list is missing

The brief asks what to change and what to leave alone for now.
The page lists questions for the team but gives no answer to either.

## Where the architecture falls short

### It reopens the one fixed constraint

The validation list asks whether a portal registration can be accepted before identity resolution.
The brief states that a kit registration must never be blocked waiting on identity.
Listing a fixed constraint as an open question reads as not having absorbed the brief.

### It puts results on hold behind identity review

The design holds a result until the patient link is confirmed, and the executive summary repeats this.
Today a result reaches its chart through kit, registration and chart without touching the CRM.
Gating results on a new enterprise link adds a customer-facing delay that does not exist now.
Identity confidence should gate marketing and CRM attachment only.
The clinical path should keep its own deterministic chain.

### It never commits to a matching policy

The page says not to set a numeric threshold until business owners agree on acceptable risk.
The brief requires a confidence from 0 to 1 per record and a review queue.
A starting rule set with thresholds, stated as an assumption and tested on this data, is what the brief asks for.
The page does not say how an EHR chart, which has only name, birthdate, phone and email, joins a person, or how the 78 shared-email groups in the portal are split.

### It ends with questions where the brief asks for assumptions

The brief says to make a reasonable assumption, write it down and keep going.
The page ends with seven questions for production owners and records no assumptions.

### The CRM replacement is not addressed

The phased introduction has five stages but no 90-day timeline.
It does not say how the identity links survive the CRM being replaced, which the brief names as a condition of the rollout.

### Nothing ties the design back to the symptoms

There is no table showing which design element removes which symptom.
There are no volumes, latency targets or technology choices, and no build-versus-buy position.
A reader cannot tell what would be built first or how large it is.

## Smaller points

The pages are branded "10X Health" throughout and never mention Lumen Health, the company whose executive the summary is written for.

The executive summary has no numbers.
"32 of 433 registrations rejected" would land harder than "fewer service failures".
It also has no ask and no timeline.

The Salesforce and Shopify vendor inference is reasonable, but it takes space the causal chain should have had.

The role strip in the executive summary draws buyer, recipient, registrant and patient with arrows between them, which reads as a sequence when the point is that they can be different people.

## Missing deliverables

This directory holds the three HTML pages and nothing else.

| Brief item | Status |
|---|---|
| 1. Current system and root causes | Present, with the gaps above |
| 2. Target architecture | Present, with the gaps above |
| 3. Working slice writing `identities.csv` and `review_queue.csv` | Missing, including the README command |
| 4. Build specification for one component | Missing |
| 5. 90-day rollout | Missing; a five-stage outline exists without dates |
| 6. One-page executive summary | Present |
| 7. `AI_LOG.md` | Missing |

The working slice is the item the brief weighs most: "a focused piece of work that runs".

## Recommended fixes, in order

1. Build the working slice, because nothing else in the submission proves the matching design.
2. Rewrite the findings section around the causal chain and mark symptoms 4 and 5 as confirmed with the counts above.
3. Add the two missing code behaviours with their line references.
4. Add the change list: what to switch off now, what to fix next and what to leave alone.
5. Remove the result hold from the architecture and the executive summary.
6. Replace the open questions with stated assumptions and commit to starting thresholds.
7. Write the 90-day rollout with the registration constraint and the CRM replacement both addressed.
8. Add a symptom-to-design table, the build specification and `AI_LOG.md`.
9. Name Lumen Health and put two or three numbers in the executive summary.
