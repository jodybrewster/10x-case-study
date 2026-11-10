# Agentic reviews

Three AI reviewers read the Claude deliverables on 2026-11-09: a code review of the working slice, a security audit of the repository and an architecture challenge of the design with a HIPAA and SOC 2 lens.
This file records what they found.

**Status: open.**
The reviews were read-only and none of the changes below has been made yet.
The items in [Changes needed](#changes-needed) are to be made before the submission is final, or carried into the review session as known gaps.

## How the reviews were run

Each reviewer was a Claude Opus subagent started with a fresh context from the main Claude Code session.
Each followed a role file from the pro-dev-skillset plugins: the pro-quality code reviewer, the pro-security audit skill and the pro-security architect in challenge mode.
None saw another reviewer's output or the sessions that wrote the work.

- The code reviewer ran the 21 tests, re-ran the pipeline into a scratch folder and reproduced C1 on the shipped data.
  C2, C3 and C4 were reproduced on made-up records.
- The security auditor built value sets from the CSVs (645 emails, 561 phones, 547 full names, 500 birthdates, 499 street lines, 4,757 record IDs) and matched them against every text file outside `data/`.
  It could not dispatch an independent verifier, so its findings are self-verified.
  No web search was used, so no CVE check was made.
- The architect runs on the same model family as the sessions that wrote the design.
  Treat it as a fresh read, not a fully independent one.

The main session then checked by hand: the code paths behind C1, C3 and C4, the nickname table behind C2, the scoring weights behind the 0.978 and 0.97 figures and the quoted design lines behind D1, D2, D4 to D9, D15, D16 and D18.
It ran a separate count-only scan that confirmed S1, S2 and S4.
Not re-checked: S5, S6, the legacy-sync findings and the HIPAA and SOC 2 table rows beyond those quotes.

The regulatory citations are an engineer's reading and not legal advice.
Counsel should confirm any that are relied on.

No value from `data/` appears in this file.
Findings cite files, line numbers and column names only.

## Verdict

The design can proceed with required changes.
It has two blocking design gaps, four important code defects and a set of HIPAA and SOC 2 gaps that centre on wrong merges, the review queue and PHI reaching commercial systems.
The security audit found no critical issue and no secrets.
Its largest finding is that values from `data/` were copied into design pages, a transcript and tests.

## Changes needed

Eight changes, in the order a review panel is most likely to reach them.
All are open.

| # | Change | Why it comes first | Effort | Findings |
|---|---|---|---|---|
| 1 | Remove values copied from `data/` out of `claude/docs/current-system.html`, `claude/docs/worked-examples.html`, `claude/AI_LOGS/claude-session-08.md`, `claude/tests/test_identity.py` and `claude/docs/build-spec.html`. Rewrite line 82 of the document-writer skill. Correct the redaction claim in the AI log. | The submission says it treats `data/` as PHI and a reader can open a page that shows a full profile. | 2 to 3 hours | S1, S2, S4, S5, S6, S8 |
| 2 | Run the cluster conflict check on review-band pairs. | Nine of 26 shipped review items invite a merge of two people with different birthdates. This changes `review_queue.csv`. | 1 hour with a test | C1 |
| 3 | Queue every lab-result identity mismatch whatever it scores. | A wrong-patient result currently raises nothing. | 30 minutes with a test | C3 |
| 4 | State who authorizes a result view and that a merge never widens it. | It is the root of the wrong-merge breach risk and the first question on PHI treatment. | Design text plus one acceptance test | D1 |
| 5 | Make the build-spec constraint list match the clustering section. | The spec as written merges twins. | 15 minutes | D2 |
| 6 | Reconcile what the CRM and marketing receive: drop `stage:read` from the CRM, no send list without a BAA, one payload rule. Name the missing vendors on the BAA list. | The design contradicts itself on PHI in commercial systems. | 1 hour | D5, D6 |
| 7 | Correct the two de-identification claims and the log scope claim. | A wrong claim about 164.514 is worse than silence. | 30 minutes | D7, D8 |
| 8 | Add the breach path for a wrong merge: portal view logs, the four-factor assessment, marketing as a disclosure path. | The panel will ask what happens after a bad merge. | 1 hour | D13, D14 |

After those: the unisex nickname entries (C2), the flag default (D4), the Phase 0 conflict between build spec and rollout (A2) and verified identifiers (D3).
Any item not changed should be listed as a known gap in the design pages.

## Code review

Scope: `claude/identity/`, `claude/tests/test_identity.py`, `claude/analysis/evaluate.py` and `claude/analysis/legacy_trace.py`, checked against the brief, the build spec and `claude/README.md`.

Result: four important findings and five nits.
The 21 tests pass.
The pipeline reproduces the shipped CSVs byte for byte and the output is stable across three hash seeds.
Only C1 changes the shipped output.
The other three are latent on this dataset but each contradicts a claim in the README or build spec.

| # | Location | Defect | Failure | On shipped data |
|---|---|---|---|---|
| C1 | `claude/identity/pipeline.py:80` | The cluster conflict check runs only for pairs at 0.90 or above. Pairs between 0.60 and 0.90 go to review unchecked. | A reviewer sees only agreeing reason codes for two people with different known birthdates, answers "same" and merges two relatives' health records. | 9 of 26 review items (`review_queue.csv` lines 8, 9, 10, 12, 15, 17, 19, 20, 24). Five would also put two EHR charts on one person. Line 24 is the pair the spot-check test says must stay apart. |
| C2 | `claude/identity/normalize.py:8-27` | Unisex short names map to one gendered full name: pat, alex, sam, chris, jamie, nat, jess. | A made-up "Pat" with no birthdate against a household "Patricia" scores 0.99 and links automatically. | None of these names occur, so no effect today. |
| C3 | `claude/identity/pipeline.py:65,71` | A lab result that ties a registration to a chart with a different name or birthdate is rejected below 0.60 or on veto, with no review item. | A result posted to the wrong patient's chart, the clinical safety case, raises nothing. | 406 of 406 lab links agree, so no effect today. |
| C4 | `claude/identity/pipeline.py:31` | A plain address is never added to the plus-tag block, so `x@d` and `x+tag@d` are never paired by email. | `claude/README.md` line 53 says plus-tag pairs go to review whatever they score. They do not. | No plus tags in the data. |

Nits:

- `pipeline.py:69`: a record with equally strong links to two persons goes to whichever key sorts first.
  The build spec says two candidates at 0.90 or above means no merge.
  `identities.csv` lines 270 and 325 are examples.
- `pipeline.py:130-134`: reason codes from several record pairs are merged into one row, so `review_queue.csv` line 3 carries both `birthdate_agree` and `birthdate_missing`.
- `tests/test_identity.py:171-177`: the determinism test runs both passes in one interpreter, so it cannot catch set-order dependence.
- `pipeline.py:41-42`: blocks over 60 records are dropped with no count in the summary.
- `test_review_queue_has_no_pii` checks only the header row.

Done well: `cluster.py:22-34` checks birthdate, first name and chart count on the whole component, so a record with no birthdate cannot bridge two people.
No shipped cluster breaks any of the three rules.

## Security audit

Result: no critical finding.
Ten findings pass the 8 of 10 confidence gate: three high and seven medium.
No secret, credential or token exists in the tree or in the `legacy-sync` git history.
The slice and `legacy-sync` use the standard library only.

### New work and repository hygiene

| # | Severity | Location | Finding | Fix |
|---|---|---|---|---|
| S1 | High | `claude/docs/current-system.html:573-580, 599-669, 883-904` | A full eight-record profile of one person from `data/`: emails, phones, street, birthdate, chart ID and result count. A second named person with a kit barcode and result ID. The page says the rows "are in the data as shown". | Replace with invented people as the build spec already does. Keep counts, column names and the record IDs needed for citation. |
| S2 | High | `claude/docs/worked-examples.html:164-266` | Ten data subjects named in headings, navigation and anchors, each tied to record IDs in all four systems and a narrative about charts, gifts or opt-outs. | Label cases by number. Use invented names and IDs. |
| S4 | Medium | `claude/AI_LOGS/claude-session-08.md:942, 1225-1311` | The transcript is described as redacted but keeps data-subject names beside record IDs. Emails and phones were removed; names were not. | Redact with a name list built from `data/`, rescan and correct the claim in `claude/AI_LOGS/AI_LOG.md`. |
| S5 | Medium | `claude/tests/test_identity.py:35-44, 59-60` | Fixtures use name, birthdate and phone tuples that match real rows. | Invented values. |
| S6 | Medium | `claude/docs/build-spec.html:213, 780` and IDs at 354, 771-789 | Real phones and record IDs used as examples. `solution-design.html:876` and `target-architecture.html:396` quote a real email local part. | Invented phones and IDs. |
| S7 | Medium | `claude/analysis/legacy_trace.py:26, 105-108` | `--examples` defaults to 3 and prints names, emails and birthdates to stdout. In an agent session that output goes to the model provider and the local session store. | Default to 0. Print record IDs only. |
| S8 | Medium | `.claude/skills/10x-document-writer/SKILL.md:82` | The skill tells agents to use examples and identifiers from the case data, which treats `data/` as quotable. Likely cause of S1, S2 and S6. | Forbid copying values from `data/`. Require invented placeholder people. |

The count-only confirmation scan found 9 distinct data emails and 11 full names in `current-system.html`, 10 names in `worked-examples.html` and 15 in the session-08 transcript.

Checked and clean: all SVG diagrams, `index.html`, the README files, the executive summary, the rollout page, every other transcript and the Codex pages (record IDs only).

`claude/identities.csv` and `claude/review_queue.csv` hold record IDs, keys, scores and reason codes, with no demographics and no kit or lab content.
That is the minimum for their stated use.
They are still PHI, because a record ID is an identifier and `system=ehr` shows that a person has a chart.

### Already in legacy-sync

`legacy-sync/` is evidence and stays unmodified.
The target design should name the control that removes each of these.

| # | Severity | Location | Finding |
|---|---|---|---|
| S3 | High | `legacy-sync/legacy_sync/sync/order_sync.py:20-24, 42` | An order with a matching surname and zip lands on someone else's CRM account, then overwrites that account's email and phone with no history. A buyer who knows a surname and zip can redirect a stranger's contact channel and block their next registration. The replay counts 43 such orders with no malice involved. |
| S9 | Medium | `legacy-sync/legacy_sync/registration/register.py:17-18` | With a blank or placeholder birthdate, a registration attaches on surname alone. Combined with S3, a kit attaches to the wrong person. |
| S10 | Medium | `legacy-sync/legacy_sync/consent/merge.py:3-12` | An account merge copies no opt-out fields, so the losing account's SMS and call opt-outs disappear. |

Run in production as written, the legacy code has no access control, no audit trail and no authentication (45 CFR 164.312(a), (b), (d)).
S3 and S9 are concrete integrity failures under 164.312(c)(1).

### Below the gate, worth a look

- `claude/identity/pipeline.py:20`: `person_key` is an unsalted truncated hash of system and record ID.
  Record IDs are sequential, so a key shared without IDs can be reversed by enumeration.
  The README already calls it a prototype shortcut.
- `claude/docs/current-system.html:1052` loads a script from a CDN with no integrity attribute, on the page that holds S1.
  The project skill's own rule says no external scripts.
- Agent sessions can read `data/` freely, so raw rows reach the model providers.
  Whether that is acceptable is a process decision to state in the AI log.
- `legacy-sync/` contains `__pycache__` folders dated 2026-11-09, against the no-modify rule.
  The replay command in `AGENTS.md` does not set `PYTHONDONTWRITEBYTECODE`.
- Two Codex transcripts in `claude/AI_LOGS/` keep a third party's name and email, against the redaction claim.

The audit's machine-readable output is at `.pro-dev/security/2026-11-09-191707.json`.
This audit is an AI-assisted first pass and not a substitute for a professional security assessment.

## Design challenge

Scope: `claude/docs/target-architecture.html`, `solution-design.html`, `build-spec.html`, `rollout.html`, `executive-summary.html` and `worked-examples.html`.

Verdict: proceed with required changes.
"New" means neither earlier review in the repository raised it.
Confidence is out of 10.

### Blocking

| # | Attack or failure | Change the design needs | Conf. | Status |
|---|---|---|---|---|
| D1 | Result access is tied to identity merges. The portal shows results through the kit's patient role and stores `person_key` on the registrant row. `build-spec.html:588` shows results to the registrant while a pair is in review. Any wrong or induced merge lets one portal user see another person's results. | State that result authorization is per portal account and per registration on the kit-barcode chain. A merge or split never widens what a session can see. Add an acceptance test for it. | 8 | Partly raised before; merge-driven visibility is new |
| D2 | The build-spec handler drops the first-name constraint. `build-spec.html:493` lists only two birthdates and two EHR charts. Twins who share email, phone and address score sigmoid(3.8) = 0.978 with the prototype weights, above the 0.90 threshold. The prototype's `cluster.py` blocks this; a developer building from the spec would not. | Make the handler's constraint list match the clustering section: two known birthdates, two canonical first names, two EHR charts. Add the twin case to the acceptance tests. | 8 | New |

### Required changes

| # | Attack or failure | Change | Conf. |
|---|---|---|---|
| D3 | Identity poisoning. An attacker places a cheap order with a victim's name and email plus their own phone and address. Email, first name and surname score 0.97 and link automatically. Survivorship then prefers the attacker's shipping address. | A verified flag per identifier. Unverified values support review but never an automatic link or a preferred value. | 7 |
| D4 | The flag fails into the blocking path. `build-spec.html:828`: if the flag service is unreadable with no cache, the mode is off, which is the legacy synchronous CRM path. | After 100 percent rollout the default on an unreadable flag is on. Off needs an explicit audited setting. | 7 |
| D5 | The marketing fallback still discloses. Without a BAA the platform "receives consent and a send list only" (`solution-design.html:1504`). A list of kit buyers with contact addresses is the participation signal the design itself calls sensitive. | No customer list to a vendor without a BAA or the state-law equivalent. One payload rule across the consumer table, ADR-14 and D10. | 7 |
| D6 | The CRM adapter is granted `stage:read` yet "cannot see result status" (`solution-design.html:1413`). Stage includes resulted. | Drop `stage:read` from the CRM or cap its stage at registered. Add a contract test. | 7 |
| D7 | Logs are argued out of BAA scope (`build-spec.html:862`) but carry registration IDs, kit barcodes, person keys and chart IDs. Record numbers are identifiers under 164.514(b)(2). | Put the observability vendor under a BAA or tokenize record IDs before they leave the restricted zone. | 7 |
| D8 | The non-production extract is called de-identified. Date shifting, consistent fake names and preserved households is pseudonymization. It meets neither Safe Harbor nor expert determination. | Call it a pseudonymized data set and keep it in the restricted zone, or require expert determination. | 7 |
| D9 | The matcher regression set takes pairs from production errors (`solution-design.html:2071`) and runs in CI, where the design allows no production identifiers. | Run the production-derived subset inside the restricted zone. Keep synthetic analogues in CI. | 7 |
| D10 | A point-in-time restore undoes review decisions, containment splits and opt-outs. None of those sit in a sender outbox to replay. | Recover forward by re-applying the identity event log after a restore. Test it in the quarterly drill. | 7 |
| D11 | SaaS webhooks cannot do mutual TLS with short-lived tokens and the restricted zone has no internet ingress. A forged or replayed order or opt-in event changes links or consent. | An ingress gateway outside the zone that verifies each vendor signature with a timestamp window and dedups delivery IDs. | 7 |
| D12 | Order events are idempotent on order ID, so the later "shipped with kit barcode" update is dropped as a duplicate. | Key on the platform event ID or on order ID plus updated time. Apply only newer updates. | 7 |
| D13 | The breach assessment asks who read which results, but portal result views are not a required audit record. Without them a low-probability finding cannot be shown, so every wrong merge defaults to notification. | Make portal result views a required audit record with the event log's retention. | 7 |
| D14 | A wrong household merge reaches people through marketing: a "results ready" message goes to a relative's address. | List the marketing feed as a disclosure path in the runbook. Hold stage changes past registered for recently merged persons until the audit clears them. | 7 |
| D15 | Deletion by destroying a key cannot work: keys are per environment and per data class (`solution-design.html:1429`), not per person. The blocking hash also survives. | Per-person data keys. Delete hash rows too. Cover replicas, backups and consumer copies. | 7 |
| D16 | A registration conflict opens a support case "with the two registration attempts" (`build-spec.html:398`). The ticketing tool is on no BAA list. | The case carries registration IDs only. The agent opens identifiers in the restricted view and that read is logged. | 6 (verify) |
| D17 | Reviewers choose their own items, so an agent who knows a target's account ID can claim that person's item. | The system assigns the next item. Show agree or disagree markers and masked values first, with per-field reveal that is logged. | 6 (verify) |
| D18 | After a split, "the old key keeps resolving to the survivor forever" (`solution-design.html:923`). A consumer that missed the split event keeps resolving to the wrong person. | Give the divided-off side its original key back, or have resolve answer "split" with no survivor. | 6 (verify) |
| D19 | The 2 percent blind audit is the main detector of wrong automatic links and the gate accepts a false-match upper bound of 1 percent with no estimate of how many touch result-holding persons. | State the bound as expected wrong merges touching clinical data per month. Oversample merges into persons with a chart or result. | 6 (verify) |

### Open questions

- Is the company a covered entity, a business associate or neither?
  Marketing rules, BAAs, the breach clock and deletion duties all turn on it.
- How does the portal authenticate the person registering a kit: a login with a verified email or a guest form?
  The reach of D3 depends on it.
- How do access, amendment and accounting requests resolve through `person_key` across a later merge or split?
- What is the session timeout on the review screen?
  A 30-minute claim lease is not a logoff.
- Who reviews the event log for merges and splits, how often and against what triggers?

## HIPAA gaps

The design is strong on encryption, unique user identification, break-glass access and the append-only event log.
Its gaps cluster in four places: PHI reaching commercial systems, the review queue, what happens after a wrong merge and two de-identification claims that are incorrect.
Citations are to 45 CFR.

| Requirement | What the design says | Gap | Status | Severity |
|---|---|---|---|---|
| Minimum necessary, 164.502(b), 164.514(d) | Consumer table with receive and never-receive lists, contract tests on payloads, review list without names. | CRM gets `stage:read` against its own rule. One `person_key` is a join key across commercial systems and the EHR. The comparison screen shows full values. | Partly | High |
| PHI in the CRM, 164.502(a), 164.502(e) | CRM sits in the commercial zone "outside the health-data boundary". The executive summary says purchase records name genetic tests and are a health-data exposure. | The design calls CRM purchase records health data, then keeps the CRM and e-commerce outside the boundary with no BAA. | Contradicts itself | High |
| Marketing, 164.508(a)(3), 164.501 | A BAA or equivalent terms gates stage data. Consent is per channel and address. | A BAA governs the vendor, not the use. Messaging triggered by "results ready" needs the 164.501 exclusion or an authorization. Channel consent is not an authorization. Consent has no purpose field. | Silent | High |
| Right of access, 164.524 | Nothing. | Which records form the designated record set for a merged person? A wrong merge returns another person's data on request. | Silent | Medium |
| Amendment, 164.526 | Customer-reported wrong link opens a priority 1 item and a split. | Works as a correction path. No response deadline, no denial handling and no notice to those who received the wrong data. | Partly | Medium |
| Accounting of disclosures, 164.528 | Nothing. | A disclosure caused by a wrong merge is not recorded per individual. | Silent | Medium |
| De-identification, 164.514(a)-(c) | `person_key` is treated as sensitive. Controls lists say "salted hashes" outside the restricted zone; the encryption section says keyed HMAC. Non-production extract is "de-identified" by date shifting. Logs are argued out of BAA scope. | Hashed email and phone are pseudonymous, not de-identified. The extract meets neither method. Logs carry record numbers. | Wrong on extract and logs | High |
| Personal representatives, 164.502(g) | A parent may register a kit for a child. Results show to the registrant. | The registrant is not always the patient or an authorized representative. Minors are not addressed. | Partly | High |
| Risk analysis, 164.308(a)(1)(ii)(A) | Threat model with 11 threats. | No inventory of every ePHI location: outbox, inbox, log copies, backups, CRM, tickets, observability, regression set, labelling extracts. | Partly | Medium |
| Activity review, 164.308(a)(1)(ii)(D) | Read-volume alert per reviewer, quarterly access review. | No cadence for reviewing merge, split and break-glass logs. A median-relative alert misses slow harvesting. | Partly | Medium |
| Workforce access to the review queue, 164.308(a)(3)-(4) | List without names, identifiers only for the claimed item, second reviewer for clinical merges, no self-review. | Reviewers pick their own items. Full values rather than masked. No onboarding or offboarding timeline. | Partly | High |
| Contingency plan, 164.308(a)(7) | RPO 5 minutes, RTO 4 hours, quarterly restore drill. | A point-in-time restore drops human decisions and opt-outs. | Partly | Medium |
| Business associates, 164.502(e), 164.504(e), 164.308(b) | BAAs with hosting, review tooling, the lab feed and marketing when it gets stage. | Not named: CRM SaaS, e-commerce platform, support ticketing, observability, the email and SMS sender, any CDN or WAF in front of the portal. | Partly | High |
| Unique user identification, 164.312(a)(2)(i) | SSO with MFA for people. mTLS and client credentials for services. | None material. | Addressed | |
| Access control, 164.312(a)(1) | Scope table per service role. | The CRM scope contradiction. The resolve API mints persons on read, so a read scope creates records. | Partly | Medium |
| Emergency access, 164.312(a)(2)(ii) | Break-glass with two approvals, time-limited and logged. | None material. | Addressed | |
| Automatic logoff, 164.312(a)(2)(iii) | Nothing. A 30-minute claim lease is a workflow lock. | No idle timeout on the review screen. | Silent | Low |
| Audit controls, 164.312(b) | Event log append-only, hash-chained, copied to write-once storage. Reads by people are logged. | Service reads of key, stage and consent are not logged. Portal result views are not required. | Partly | Medium |
| Integrity, 164.312(c)(1) | Vetoes, 600-link validation gate, 2 percent blind audit, split from the log. | Handler omits the first-name constraint. Unverified identifiers can poison a person. Stale keys after a split. Rolling back weights does not undo links made with them. | Partly | High |
| Authentication, 164.312(d) | mTLS and signed tokens. | SaaS webhook signature checks and replay windows are unspecified. Customer identity proofing at registration is silent. | Partly | High |
| Encryption, 164.312(a)(2)(iv), 164.312(e)(1) | TLS 1.2 or later, AES-256-GCM envelope encryption per field, keys in a KMS or HSM. | Marketing file-drop transport unspecified. Key granularity cannot delete one person's data. | Mostly addressed | Low |
| Breach notification, 164.400-414 | Incident table: detect, contain, assess, counsel decides, remediate. | A wrong merge is treated as an incident, which is right. Missing: the four-factor assessment of 164.402 by name, the discovery rule that starts the clock, portal view logs, marketing sends as a disclosure path and the HHS and media thresholds. Blast radius is not quantified. | Partly | High |

Whether the company is a covered entity, a business associate or neither is an open question the design already lists.
The answer changes four things.
Marketing needs a HIPAA authorization for a covered entity, the BAA's permission for a business associate, or state-law consent under Washington's My Health My Data Act for neither.
Breach handling follows 164.404, 164.410 or the FTC Health Breach Notification Rule (16 CFR Part 318).
Deletion is not a HIPAA right but is a state-law one, which collides with "nothing is deleted".
California's CMIA and its genetic privacy law may apply because the catalogue includes a genetic kit; both need checking by counsel.

## SOC 2 gaps

Change management for match rules is the strongest area.
The high-severity gaps are inbound webhooks, data moving to commercial systems, incident response for a bad merge and the one fail-closed inversion on the registration flag.

| Criterion | What the design says | Gap | Status | Severity |
|---|---|---|---|---|
| CC6.1 logical access | Scope per role. Review screen behind SSO on the corporate network. Support has no SQL access to production identifiers. | No role for database administrators on the identity store. Webhook ingress not covered. | Partly | Medium |
| CC6.2 provisioning | Quarterly access review. | No joiner, mover or leaver process for reviewers or service credentials. | Partly | Medium |
| CC6.3 least privilege | Two-person rule for clinical merges, no bulk decide, dual control on admin changes, break-glass. | Reviewers pick their own items. CRM holds `stage:read`. Resolve mints on read. | Partly | High |
| CC6.6 boundary protection | Restricted zone has no direct internet access. Egress proxies with pinned destinations. | No inbound path for SaaS webhooks is defined. | Silent on ingress | High |
| CC6.7 data in transit and movement | TLS, mTLS, a payload contract test per interface. | CRM receives stage. Marketing send list without a BAA. File-drop transport undefined. A support ticket carries two registrants. | Partly | High |
| CC7.1 change detection | Container scan, CI gates, infrastructure as code. | None material. | Addressed | |
| CC7.2 anomaly monitoring | Alerts on read volume, key use, false-match bound, queue age. | No alert on merge rate after a deploy, cluster size growth, merges into result-holding persons or service-account read volume. | Partly | Medium |
| CC7.3-CC7.4 incident response | Wrong-merge runbook with owners and target times. | No portal view logs, no stated breach clock, marketing not listed as a spread channel, no bulk procedure for a bad weights release. | Partly | High |
| CC8.1 change management | Weights, thresholds, the nickname table and normalisation are controlled changes: regression pass, fresh validation sample, named approver, staged release, rollback plan. | Rollback reverts config but not links already made. The regression set breaks the CI zone rule. Each monthly refit needs a fresh 600-link sample that the staffing model does not cover. | Mostly addressed | Medium |
| CC9.2 vendor risk | BAAs or equivalent terms for vendors that touch the restricted zone. | No vendor due diligence. CRM, e-commerce, ticketing and observability vendors are not named. | Partly | Medium |
| A1.2 availability and backup | Two or more instances, synchronous standby, second-region backups, RPO and RTO. | Point-in-time restore loses human decisions and opt-outs. | Partly | Medium |
| A1.3 recovery testing | Quarterly timed restore. | The drill does not test re-applying decisions made after the restore point. | Partly | Low |
| A1, fail open or closed | Registration fails open. Consent read failure fails closed. Matcher down creates provisional persons. | The flag service fails into the blocking legacy path. Result display depends on unstated portal authorization. | One inversion | High |
| C1.1 identifying confidential data | Classification table and a data dictionary with a class per field. | Logs are classed as free of PHI. | Partly | Medium |
| C1.2 retention and disposal | Inbox 7 days, outbox 30 days, logs 12 months, store follows the clinical record. | Key granularity cannot delete one person. Hash rows survive. Review items kept forever. Backups and consumer copies not covered. | Partly | Medium |
| PI1 processing integrity | Inbox and outbox with event ID idempotency, per-aggregate sequence numbers, nightly reconciliation for registrations. | Order updates dropped by order ID dedup. No ordering rule for e-commerce events. Orders, results and opt-outs are never reconciled, so a lost opt-out webhook repeats symptom 6. | Partly | High |
| P4 retention | As C1.2. | No purpose limit on labelled pairs kept for tuning. | Partly | Medium |
| P5 access and correction | The wrong-link report flow. | No request flow for access or correction through `person_key`. | Partly | Medium |
| P6 disclosure and notification | Per-consumer disclosure matrix, contract tests, incident notification. | No per-individual record of disclosures. Consent has no purpose. | Partly | High |

## Architecture weaknesses

Six weaknesses matter regardless of compliance.
The first is the root of most merge-related PHI risk above.

| # | Weakness | Direction |
|---|---|---|
| A1 | Nothing defines who may see a result. The portal registration row, `kit_role` in the identity store and the EHR chart each look like the source of result access. | Decide that the portal's own account and registration model authorizes result views and that identity never does. |
| A2 | The build spec and the rollout describe two different Phase 0 decouplings. The rollout says Phase 0 needs no identity service and promises 0 writes from it to production before day 46 (`rollout.html:158`). The build spec says the first change to ship is the mode on with the identity service storing and resolving events (`build-spec.html:836`). | Run the build spec's on mode in Phases 0 and 1 with the CRM work item from the rollout. Keep identity CRM tasks and portal callbacks off until the later gates. |
| A3 | Merge and split propagation is one-way. A merge is one clean transaction. A split depends on every consumer handling the split event, including a marketing platform that keeps its last good state and a CRM whose account merges may be destructive. | Define what a consumer does when it already acted on the merge. |
| A4 | The store has no forward recovery. Point-in-time restore plus outbox replay only covers sender-originated events. | Use the event log copy on write-once storage to re-apply decisions after a restore. |
| A5 | Inputs are trusted unevenly. Registration has a thorough durability contract. Orders, results and consent rely on vendor webhooks with no signature check, no ordering rule, a dedup key that drops updates and no reconciliation. | Give every inbound feed the registration feed's contract. |
| A6 | One store owns matching, consent, stage and review. If the matcher or store goes down, consent suppression and stage updates stop with it. | Separate them internally or give consent its own failure path. An earlier review raised this and the design is unchanged. |

Earlier review points that are still open in the design pages: registrant versus patient and the result hold, consent purpose, deletion requests, consumer health law and bridge-record cluster checks.
The salted versus keyed hash wording was fixed in the encryption section but is still wrong in both Controls lists (`target-architecture.html:767`, `solution-design.html:1525`).
