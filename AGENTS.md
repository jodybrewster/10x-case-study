# 10X Health case study

This repository holds the Solution Architect case study from 10X Health and the work done on it.
Start with the two source documents, then the request that came with them.

## Source material

- [BRIEF.pdf](BRIEF.pdf): the case study brief as sent by 10X Health.
- [BRIEF.md](BRIEF.md): the same brief transcribed to Markdown, word for word, for agents and search.
- `RECRUITER_EMAIL.md`: the recruiter's email that delivered the brief and asks for availability for a 90-minute review session. It is kept in the local working copy only and is not committed.
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
7. `AI_LOG.md` (kept at `claude/AI_LOGS/AI_LOG.md`, with redacted transcripts beside it): tools used, moments AI helped, at least two moments it was wrong and how that was caught, transcripts if available.

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
- `AGENTIC_REVIEWS.md`: the agentic code review, security audit and HIPAA and SOC 2 design challenge of 2026-11-09, with the list of changes still needed. Read it before editing the slice or the design pages.
- `.claude/skills/10x-document-writer/`: a skill for writing further HTML documents in the theme of `codex/executive-summary.html`.
