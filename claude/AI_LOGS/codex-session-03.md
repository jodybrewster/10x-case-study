# Codex session 3

Redacted export: prompts and assistant replies. Tool calls, tool output and private configuration are left out.


## Prompt (2026-11-09 22:26:41 UTC)

# AGENTS.md instructions for ~/Projects/10x-case-study

<INSTRUCTIONS>
# Start here

The record of who [owner] is, how work flows, the project hierarchy, the rules and the decisions is `~/Projects/hq/AGENTS.md`.
Read it at the start of a session, then `~/Projects/hq/STATUS.md` for where every stream stands.
Each project under `~/Projects/hq/projects/` has its own `AGENTS.md` or `CLAUDE.md`; read that next.

--- project-doc ---

# 10X Health case study

This repository holds the Solution Architect case study from 10X Health and the work done on it.
Start with the two source documents, then the request that came with them.

## Source material

- [BRIEF.pdf](BRIEF.pdf): the case study brief as sent by 10X Health.
- [BRIEF.md](BRIEF.md): the same brief transcribed to Markdown, word for word, for agents and search.
- [RECRUITER_EMAIL.md](RECRUITER_EMAIL.md): the recruiter's email that delivered the brief and asks for availability for a 90-minute review session.
- [OUTCOME.md](OUTCOME.md): an early read of the brief and the code, with suggested next steps.
- [data/](data/): eight CSV files from the four fictional systems, about 2,000 customer records.
- [legacy-sync/](legacy-sync/): the current sync service in Python, with its git history at commit `f6bf641`.

## What the brief asks for

Six deliverables plus an AI log, budgeted at 6 to 8 hours.
The full text is in [BRIEF.md](BRIEF.md); the short form is:

1. Explain how orders and registrations flow through `legacy-sync` and find the root cause of the six reported symptoms, citing files and line numbers.
2. Design a single customer identity across the four systems: data model, matching and uncertainty, how each system uses it, how it treats protected health information.
3. A working slice that reads `data/` and writes `identities.csv` and `review_queue.csv` with one command.
4. A build specification for one component.
5. A 90-day rollout in which a kit registration is never blocked waiting on identity.
6. A one-page summary for a non-technical executive.
7. `AI_LOG.md`: tools used, moments AI helped, at least two moments it was wrong and how that was caught, transcripts if available.

## Working rules

- Treat everything in `data/` as protected health information, as the brief instructs, even though it is synthetic.
- Do not modify `data/` or `legacy-sync/`. They are the evidence. Cite them, run them, trace them, but leave them as delivered. Set `PYTHONDONTWRITEBYTECODE=1` or use `sys.dont_write_bytecode` when importing the legacy code so no cache folders appear.
- Each agent works in its own directory: `claude/` for Claude Code sessions, `codex/` for Codex sessions. Do not edit the other agent's directory unless asked.
- Everything written here is part of a hiring submission. Keep the owner's name and words out of documents, code, comments and commit messages.
- Run `python3 -m legacy_sync.replay --data ../data` from `legacy-sync/` to reproduce the shipped replay summary. `pytest` is not installed system-wide; `uv run --no-project --with pytest python -m pytest` runs the four tests.

## Where the work is

- `claude/docs/current-system.html`: how `legacy-sync` works today, the six symptoms with evidence, topology, customer journey, IDs and data shape.
- `claude/docs/target-architecture.html`: the future-state design.
- `claude/docs/executive-summary.html`: the one-page summary.
- `claude/analysis/legacy_trace.py`: the instrumented replay behind every count in those pages.
- `claude/docs/diagrams/build.py`: generates the SVG diagrams for the pages.
- `codex/`: the Codex session's versions of the same deliverables.
- `.claude/skills/10x-document-writer/`: a skill for writing further HTML documents in the theme of `codex/executive-summary.html`.

</INSTRUCTIONS>


## Prompt (2026-11-09 22:26:42 UTC)

As a solution architect, can we review the claude directory and provide your feedback please?


## Assistant (2026-11-09 22:26:46 UTC)

I’ll review the `claude/` deliverables as a solution architect: check the project guidance, trace the claims back to the supplied evidence, and assess whether the architecture and rollout satisfy the brief. I’ll keep this read-only.


## Assistant (2026-11-09 22:26:58 UTC)

The project instructions confirm that `data/` and `legacy-sync/` are evidence and must stay untouched. I’ve located the three `claude/` documents and the replay analysis; I’m now checking their claims against the brief and source code, including any gaps between the target design and the required working slice.


## Assistant (2026-11-09 22:28:40 UTC)

## Overall assessment

The `claude/` work is a strong architecture review package, especially the current-state diagnosis. It traces the six symptoms to code and replay evidence, distinguishes observed behavior from assumptions, and treats gifts as separate buyer, registrant and patient roles. The target design also correctly puts the identity service outside the CRM and keeps registration moving while identity is unresolved.

I reviewed the files read-only; I did not run the replay or tests.

## Highest-priority feedback

1. **The directory is not a complete submission on its own.** It contains the three HTML documents and the replay trace, but no working slice, `identities.csv`, `review_queue.csv`, standalone build specification or `AI_LOG.md`. The architecture page calls the working slice its reference implementation, but there is no such implementation in `claude/`. See [the matching section](<~/Projects/10x-case-study/claude/docs/target-architecture.html:468>) and [the directory inventory](<~/Projects/10x-case-study/claude/>). If those items live elsewhere, make the submission path explicit.

2. **The automatic-match confidence needs more support before it can justify linking records.** The design calls scores calibrated probabilities and sets automatic linking at 0.90, but the page proposes starting with about 80 hand-labelled pairs and recalibrating from review decisions. That may not establish sufficiently high precision for links that could expose health information. Also, dropping email plus tags and comparing phone numbers by their last ten digits can collapse distinct identifiers; allowing a one-digit birthdate transposition despite describing birthdate conflict as a veto needs a precise rule. See [normalization and matching](<~/Projects/10x-case-study/claude/docs/target-architecture.html:379>) and [scoring and thresholds](<~/Projects/10x-case-study/claude/docs/target-architecture.html:439>). I’d initially make these cases review-only, then set thresholds from a representative, independently labelled validation set.

3. **“Registration never waits” needs its reliability contract.** The design says the portal accepts the registration and events queue if the identity service is down, but does not specify durable event capture, idempotency, retry behavior, duplicate submissions, or recovery after prolonged failure. Those details determine whether the registration is truly accepted and can later reconcile without losing or duplicating kit, chart or marketing state. See [registration without waiting](<~/Projects/10x-case-study/claude/docs/target-architecture.html:491>) and [the event and source-record model](<~/Projects/10x-case-study/claude/docs/target-architecture.html:246>).

4. **The rollout milestones need to agree.** The executive summary says to ensure the CRM cannot block registration in weeks 1–2, then says to switch registration to the person key in weeks 7–10. Those can be compatible if the first milestone decouples portal acceptance from the CRM and the later one changes identity resolution, but that distinction should be stated. See [the rollout](<~/Projects/10x-case-study/claude/docs/executive-summary.html:90>).

5. **Keep the marketing diagnosis visibly conditional in the executive summary.** The detailed diagnosis says no code in the repo calls the stage helper and that its replay attribution is an assumption. The executive summary presents the 60 kits as a direct business outcome. Preserve that caveat near the figure so a reviewer does not read it as confirmed evidence of actual campaigns. See [the detailed caveat](<~/Projects/10x-case-study/claude/docs/current-system.html:930>) and [the summary figure](<~/Projects/10x-case-study/claude/docs/executive-summary.html:69>).

## Additional design refinements

- Treat `person_key` plus kit stage as sensitive, potentially identifying health information in the marketing flow. “Pseudonymous” should not imply unrestricted sharing; tighten the access and vendor boundary language. See [the PHI controls](<~/Projects/10x-case-study/claude/docs/target-architecture.html:524>).
- Define consent behavior for unknown or conflicting status, and exactly how address-scoped opt-outs behave after a person merge. “Strictest wins” is a good safety direction but needs operational semantics.
- Clarify the executive’s email metric: the summary says 45 records were rewritten by someone else’s order, while the diagnosis reports 77 orders that changed an email. Label the numerator and denominator consistently. See [the diagnosis counts](<~/Projects/10x-case-study/claude/docs/current-system.html:906>) and [the summary](<~/Projects/10x-case-study/claude/docs/executive-summary.html:69>).

The most valuable next improvement is to close the submission gaps, then make the matching safety and asynchronous registration guarantees precise enough that an implementation team could build and operate them.


## Prompt (2026-11-09 22:34:31 UTC)

can you write this review as adversarial-review.md in the claude directory


## Assistant (2026-11-09 22:34:37 UTC)

I’ll save the review in `claude/adversarial-review.md`, keeping the findings prioritized and the evidence paths and line references intact.


## Assistant (2026-11-09 22:35:14 UTC)

Wrote the review to [adversarial-review.md](~/Projects/10x-case-study/claude/adversarial-review.md). It prioritizes the submission gaps, matching risks and registration reliability requirements, with evidence references.


## Prompt (2026-11-09 22:56:05 UTC)

Alright this is from claude, can you review this work next...

All four missing artifacts now exist in claude/, though two are not submission-ready: the slice's precision is unmeasured and the AI log is a draft for you to check.

┌────────────────┬─────────────────────────────────┬────────────────────────────────────────────┐
│    Artifact    │              Where              │                   State                    │
├────────────────┼─────────────────────────────────┼────────────────────────────────────────────┤
│                │ identity/, identities.csv,      │ Runs with python3 -m identity --data       │
│ Working slice  │ review_queue.csv, README.md,    │ ../data --out . from claude/. 1,994 rows,  │
│                │ tests/                          │ 610 persons, 132 review items, 19 tests    │
│                │                                 │ pass.                                      │
├────────────────┼─────────────────────────────────┼────────────────────────────────────────────┤
│ Build          │ docs/build-spec.html            │ Registration intake, 17 sections.          │
│ specification  │                                 │                                            │
├────────────────┼─────────────────────────────────┼────────────────────────────────────────────┤
│ 90-day rollout │ docs/rollout.html               │ Four phases, eight decision gates.         │
├────────────────┼─────────────────────────────────┼────────────────────────────────────────────┤
│ AI log         │ AI_LOG.md                       │ Draft, no transcripts exported yet.        │
└────────────────┴────────────────────────────────────────────────────┘

The build spec answers the review's four form or kit errors can reject acustomer. The registration and its outbox event commit in one transaction, and the portal owns the
event until the identity service acko sets idempotency keys, a ten-attempt retry schedule, dead-letter handling, a replay procedure and nightly reconciliation, and it has 36
acceptance tests.

I checked each artifact rather than rts:
- Slice: I re-ran it and tested the outputs against the source data.
- Pages: all five are cross-linked a prose and design checks.
- Renders: I looked at the top of the rollout page and one section of the build spec. I have not viewed the rest of either page, intate-machine diagram.

Decisions for you:
- Hand-label the pairs. analysis/pairs_to_label.csv has 80 pairs with an empty label column. Until
  that is done, the 0.90 threshold iw's second high finding stays open.
- Three proposed numbers. The subagents chose these and nothing in the brief or the data backs them:
  600 labelled pairs before trusting "one full cycle" before retiringlegacy-sync, and the retry schedule (about 14 hours over ten attempts).

Still open on my side, all tracked in TASKS.md:
- the five remaining review fixes in executive summary;
- making the slice's confidence values more informative (1,976 of 1,994 are 1.0);
- de-duplicating the review queue.


## Assistant (2026-11-09 22:56:12 UTC)

I’ll review the newly added slice, build specification, rollout and AI log against the brief and the issues in my previous review. I’ll inspect the artifacts and their consistency without rerunning tests or changing files.


## Assistant (2026-11-09 23:00:26 UTC)

## Review

The new artifacts materially improve the package. The build spec now gives registration a clear acceptance boundary, transactional outbox and replay path. The rollout separates immediate CRM decoupling from later identity cutover, and the slice produces the required CSV columns.

I reviewed the current files and outputs statically. I did not rerun tests or inspect the full pages in a browser.

## Findings

1. **The validation sample cannot yet substantiate the rollout gate.** The 80-pair sample is selected by evenly spreading across score-sorted lists, not by random sampling ([sample.py](<~/Projects/10x-case-study/claude/identity/sample.py:7>)). The evaluator reports a Wilson interval as if those observations support that estimate ([evaluate.py](<~/Projects/10x-case-study/claude/analysis/evaluate.py:11>)). The rollout also shifts between “600 labelled pairs” and “600 audited auto-links.” Define a probability sample of auto-links, specify whether 600 means auto-links or all labels, and make the interval calculation match the sampling plan. The 80-pair file currently has 30 auto, 30 review and 20 near-threshold pairs, so it cannot establish precision for 600 auto-links.

2. **The rollout’s review-only safeguards are not enforced by the slice.** The rollout says plus-tag email variants and last-ten-digit phone matches must stay in review until measured, but the current matcher still uses dotless email keys and last-ten phone normalization when scoring pairs ([pipeline.py](<~/Projects/10x-case-study/claude/identity/pipeline.py:20>), [normalize.py](<~/Projects/10x-case-study/claude/identity/normalize.py:41>)). I also found the target architecture still describes a birthdate transposition exception and an automatic 0.90 threshold ([target-architecture.html](<~/Projects/10x-case-study/claude/docs/target-architecture.html:445>)). Align the implementation, rollout claims and architecture document so the promised safeguards actually apply.

3. **Expired relay leases can bypass the retry limit.** The build spec says an expired lease returns the row to pending without incrementing `attempts` ([build-spec.html](<~/Projects/10x-case-study/claude/docs/build-spec.html:408>)). If a relay repeatedly crashes or loses its response, that event can be retried indefinitely without reaching the ten-attempt dead-letter rule. Count attempts when a send is claimed, or track lease expirations separately with a bounded recovery rule.

4. **The registration handler’s locks do not cover all matching paths.** It locks on hashed email and phone, while candidate matching can also use surname plus birthdate or household evidence. Two simultaneous registrations for the same person with different emails and no shared phone may therefore process without a shared lock ([build-spec.html](<~/Projects/10x-case-study/claude/docs/build-spec.html:474>)). Add a concurrency strategy for those cases, or state how duplicate provisional people are detected and reconciled.

5. **The review queue has substantial cluster-level duplication.** In the current CSV, 132 record-pair items reduce to 26 distinct person-cluster pairs; 19 cluster pairs repeat, with one appearing 10 times. That matches the tracked follow-up, but it matters operationally because the rollout assumes a staffed queue with a two-working-day age target. Group review items by cluster pair while retaining the supporting record-pair evidence.

6. **The person keys in the prototype are guessable and can change.** The slice derives each key from the SHA-256 hash of the smallest source record ID, truncated to 12 hex characters ([pipeline.py](<~/Projects/10x-case-study/claude/identity/pipeline.py:15>)). Source IDs are enumerable, and adding a lower-sorting cluster member can change the anchor and therefore the key. This is acceptable only as a clearly marked prototype shortcut; it does not meet the target architecture’s opaque, stable-key model.

7. **The AI log and status notes need correction before submission.** The current CSV has **92** records with confidence `1.0`, not 1,976; the tracked task count is stale. The remaining confidence scores come from a logistic transform of hand-set weights, so they should not be presented as calibrated probabilities ([scoring.py](<~/Projects/10x-case-study/claude/identity/scoring.py:1>), [TASKS.md](<~/Projects/10x-case-study/claude/TASKS.md>)). Also, the AI log says Codex confirmed a count against the trace, but my earlier review in this conversation did not run the trace or verify that count. If another session did, cite or export that session; otherwise correct the account. The log is still marked draft and transcripts are not yet included ([AI_LOG.md](<~/Projects/10x-case-study/claude/AI_LOG.md:1>).

The executive summary also still presents the “60 kits” result without the replay-attribution caveat that appears in the rollout. Qualify that figure before treating the summary as final ([executive-summary.html](<~/Projects/10x-case-study/claude/docs/executive-summary.html:69>), [rollout.html](<~/Projects/10x-case-study/claude/docs/rollout.html:365>)).

## Recommendation

Keep the build spec and rollout as the new direction, but resolve the validation, retry-limit and concurrency inconsistencies before calling the architecture ready. Then deduplicate the queue and reconcile the summary, task list and AI log with the current artifacts.


## Prompt (2026-11-09 23:09:09 UTC)

Can we build a simple index page to link to the html in the codex and claude directories. Please add this to the README.md file. Please include all of the information they will need to review this work. Claude is taking over for the coding tasks.


## Assistant (2026-11-09 23:09:23 UTC)

I’ll make the repository-root `README.md` a reviewer’s index, linking both Claude’s and Codex’s HTML deliverables and explaining which set is active. I’ll include the evidence boundaries and the one-command prototype instructions so a reviewer can navigate and run the work.


## Assistant (2026-11-09 23:10:39 UTC)

Added a repository-root [README.md](~/Projects/10x-case-study/README.md) as the reviewer index. It links the Claude and Codex HTML deliverables, identifies Claude’s set as active, gives the slice run command, and points to the source evidence, task tracker and AI log. All local links resolve.


## Prompt (2026-11-09 23:11:39 UTC)

no but can you also provide an index.html so I can view all of this from a browser?


## Assistant (2026-11-09 23:11:50 UTC)

I’ll add a root `index.html` that opens directly in a browser and links to both document sets. I’ll follow the repository’s 10X document-writing skill so the index fits the existing case-study pages.


## Prompt (2026-11-09 23:12:35 UTC)

like at file://~/Projects/10x-case-study/index.html


## Assistant (2026-11-09 23:12:44 UTC)

Got it. I’ll make the page available at the exact path you gave: `~/Projects/10x-case-study/index.html`, with relative links that work when opened as a local file.


## Assistant (2026-11-09 23:13:57 UTC)

Created [index.html](~/Projects/10x-case-study/index.html) with links to the Claude and Codex documents, review notes, source brief and slice instructions. All 17 local links resolve.

Open it in your browser at:

`file://~/Projects/10x-case-study/index.html`

