# Task list

Status of the case study submission in `claude/`.
Updated 2026-11-09.
Status values: done, in progress, to do.

## Deliverables from the brief

| # | Deliverable | Where | Status |
|---|---|---|---|
| 1 | Understand the current system | `docs/current-system.html`, `analysis/legacy_trace.py` | done |
| 2 | Target architecture | `docs/target-architecture.html` | done, review fixes pending |
| 3 | Working slice | `identity/`, `identities.csv`, `review_queue.csv`, `README.md`, `tests/` | built and checked: 1,994 rows, 610 persons, 26 review items (132 record pairs), 21 tests pass. Precision not yet measured |
| 4 | Build specification | `docs/build-spec.html` | done, needs the owner's read |
| 5 | 90-day rollout | `docs/rollout.html` | done, needs the owner's read |
| 6 | One-page executive summary | `docs/executive-summary.html` | done, review fixes pending |
| - | Solution design document (consolidates 1, 2, 4 and 5) | `docs/solution-design.html` | written, 23 sections. Needs the owner's read and confirmation of the proposed targets |
| 7 | AI log | `AI_LOGS/AI_LOG.md` plus redacted session transcripts in `AI_LOGS/` | written. Needs the owner's read |

## Working slice follow-ups

- [x] Check the outputs against the source data: no person with two birthdates, surnames or charts; all 406 results agree.
- [x] Confidence documented as an uncalibrated match score. 92 records are at exactly 1.0 (an earlier note here said 1,976, which was a rounding mistake).
- [x] Review queue grouped to one item per pair of persons, with the supporting record pairs kept.
- [x] Plus-tag email matches are review only. Non-US phone numbers match on every digit only.
- [ ] Hand-label `analysis/pairs_to_label.csv`: a random sample of 100 auto links plus 26 review and 20 near-threshold pairs. This needs a person. `--label-auto 600` draws the full gate sample.
- [ ] Run `analysis/evaluate.py` on the labels and record precision and false-match rate.
- [ ] Put the measured numbers into the architecture page and the executive summary.

## Fixes from the adversarial review

| Finding | Severity | Fix | Status |
|---|---|---|---|
| Missing submission artifacts | High | Deliverables 3, 4, 5 and 7 above | done, AI log still a draft |
| Auto-link threshold not validated | High | Threshold stated as provisional, transposition exception removed, unvalidated rules review only, random sampling plan and interval defined. Labels still needed | done except the labelling |
| Registration reliability contract | High | Covered by the build specification | done |
| Rollout milestones ambiguous | Medium | Resolved in the rollout page and the executive summary | done |
| Marketing figure overstated | Medium | Labelled a replay estimate, assumption stated in the footnote | done |
| Person key and kit stage sharing too loose | Medium | Both reclassified as sensitive, per-consumer field table and contract condition added | done |
| Consent merge rules imprecise | Medium | Eight consent rules added to the architecture page | done |
| Email figures use different units | Low | Executive summary label corrected | done |

## Second review (static review of the new artifacts)

| Finding | Fix | Status |
|---|---|---|
| Label sample not random, interval not valid | Seeded simple random sample of auto links, Wilson interval on the false-match rate, 600 defined as labelled automatic links | done |
| Review-only safeguards not enforced | Enforced in the slice and aligned in the architecture and rollout pages | done |
| Expired relay leases bypass the retry limit | Attempt counted at claim, lease expiries tracked | done |
| Handler locks miss some matching paths | Lock on every blocking key, plus a sweep for duplicate provisional people | done |
| Review queue duplicated per cluster pair | Grouped: 132 record pairs become 26 items | done |
| Person keys guessable and unstable | Marked as a prototype shortcut in code and README | done, by disclosure |
| AI log and status notes inaccurate | Counts corrected, attribution of the trace check corrected | done, log still a draft |
| Executive summary lacks the estimate caveat | Added | done |

## Packaging

- [x] Add links to the build spec and rollout pages in the navigation of the other pages.
- [x] Session transcripts exported, redacted, into `AI_LOGS/` and referenced from `AI_LOGS/AI_LOG.md`.
- [ ] `claude/README.md` covers the slice. Add a list of every deliverable.
- [ ] Decide on three numbers the subagents proposed: 600 labelled pairs before trusting the threshold, 14 days as one full cycle, the retry schedule in the build spec.
- [ ] Decide what is submitted: `claude/` alone, or with `codex/`.
- [x] Initialise a git repository for the submission, or zip it.
- [ ] Replace the text wordmark with an official 10X Health logo file, if one is supplied.

## Outside the repository

- [ ] Reply to the recruiter with availability for the 90-minute review session.
- [ ] Prepare the 30-minute presentation.
- [ ] Rehearse live code navigation in `legacy-sync/`.
- [ ] Prepare for the changed-requirement discussion: what if email is not unique, what if the EHR cannot store a key, what if households must share an account.
