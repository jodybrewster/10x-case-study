# 10X Health case study

Reviewer index for the solution architect case study.
The active submission and implementation are in `claude/`.
`codex/` contains an independent alternative set of written deliverables for comparison.
[index.html](index.html) is the same index as a page for a browser; open it from a local clone.

## Suggested review order

1. [Executive summary](claude/docs/executive-summary.html) for the recommendation and business impact.
2. [Current system and diagnosis](claude/docs/current-system.html) for the six symptoms, code evidence and replay findings.
3. [Target architecture](claude/docs/target-architecture.html) for the identity model, matching approach, system responsibilities and PHI boundary.
4. [Build specification](claude/docs/build-spec.html) for the registration intake component, including its event contract, retries, replay and acceptance tests.
5. [90-day rollout](claude/docs/rollout.html) for phases, decision gates, success measures and fallback plans.
6. [Working slice](claude/README.md) for the matching rules, the run command and the limitations, with its outputs [identities.csv](claude/identities.csv) and [review_queue.csv](claude/review_queue.csv).
7. [AI log](claude/AI_LOGS/AI_LOG.md) for tools used, examples where AI helped and mistakes caught.
8. [Adversarial review](claude/adversarial-review.md) for review findings and open risks.
9. [Agentic reviews](AGENTIC_REVIEWS.md) for the code review, security audit and HIPAA and SOC 2 design challenge, with the changes still needed.
10. [Task tracker](claude/TASKS.md) for completion status and outstanding decisions.

## Deliverables from the brief

| # | The brief asks for | Where it is |
|---|---|---|
| 1 | Understand the current system | [Current system and diagnosis](claude/docs/current-system.html), backed by [legacy_trace.py](claude/analysis/legacy_trace.py) |
| 2 | Target architecture | [Target architecture](claude/docs/target-architecture.html) |
| 3 | Working slice | [Slice README](claude/README.md), [identities.csv](claude/identities.csv), [review_queue.csv](claude/review_queue.csv), code in `claude/identity/` |
| 4 | Build specification | [Build specification: registration intake](claude/docs/build-spec.html) |
| 5 | 90-day rollout | [90-day rollout](claude/docs/rollout.html) |
| 6 | One-page executive summary | [Executive summary](claude/docs/executive-summary.html) |
| 7 | AI log | [AI log](claude/AI_LOGS/AI_LOG.md), with the transcripts listed below |

Two further pages support these.
[Solution design](claude/docs/solution-design.html) consolidates deliverables 1, 2, 4 and 5 into one document.
[Worked examples](claude/docs/worked-examples.html) follows ten people through the current system and the design.

## AI log and session transcripts

The [AI log](claude/AI_LOGS/AI_LOG.md) is the written deliverable.
The transcripts are redacted exports of the sessions behind it.

- Claude Code, in `claude/AI_LOGS/`: [session 8](claude/AI_LOGS/claude-session-08.md) is the main session and [session 9](claude/AI_LOGS/claude-session-09.md) ran the agentic reviews.
  The short sessions are [1](claude/AI_LOGS/claude-session-01.md), [2](claude/AI_LOGS/claude-session-02.md), [3](claude/AI_LOGS/claude-session-03.md), [4](claude/AI_LOGS/claude-session-04.md), [5](claude/AI_LOGS/claude-session-05.md), [6](claude/AI_LOGS/claude-session-06.md) and [7](claude/AI_LOGS/claude-session-07.md).
- Codex, in `claude/AI_LOGS/`: sessions [1](claude/AI_LOGS/codex-session-01.md), [2](claude/AI_LOGS/codex-session-02.md), [3](claude/AI_LOGS/codex-session-03.md) and [4](claude/AI_LOGS/codex-session-04.md).
- Codex's own exports, in `codex/AI_LOGS/`: [about these exports](codex/AI_LOGS/README.md), the [work session](codex/AI_LOGS/codex-work-session-2026-11-09.md), the [review session](codex/AI_LOGS/codex-review-session-2026-11-09.md) and the [latest session](codex/AI_LOGS/this-session-2026-11-09.md).

## Codex deliverables

These are an independent comparison set, not the active implementation.

- [Current system diagnosis](codex/current-system-diagnosis.html)
- [Future-state target architecture](codex/future-state-target-architecture.html)
- [Executive summary](codex/executive-summary.html)
- [Adversarial review of the Codex pages](codex/adversarial-review.md)

## Run the working slice

From the repository root, run:

```sh
cd claude
python3 -m identity --data ../data --out .
```

The command uses only the Python 3 standard library and writes `claude/identities.csv` and `claude/review_queue.csv`.
The documented test command is `python3 -m unittest discover -s tests` from `claude/`.

The current snapshot contains 1,994 source records grouped into 610 person keys.
The review queue has 26 person-pair items covering 132 supporting record pairs.
The 0.90 auto-link threshold is provisional, and match scores are not calibrated probabilities.
Precision and recall have not yet been measured against labelled pairs.
See the [slice README](claude/README.md) for output columns, matching rules and limitations.

## Source evidence and data handling

- [Case study brief](BRIEF.md), transcribed from [BRIEF.pdf](BRIEF.pdf)
- [Initial findings and next steps](OUTCOME.md)
- [`legacy-sync/`](legacy-sync/) contains the supplied sync service as delivered, at commit `f6bf641`.
  Its seven original commits are kept on the `legacy-sync-history` branch of this repository, with their original hashes: `git log legacy-sync-history`.
- [`data/`](data/) contains the eight supplied CSV files.

The company and records are fictional, but the brief requires treating `data/` as protected health information.
Treat derived identity outputs and review files as sensitive too.
Do not modify `data/` or `legacy-sync/`; they are the evidence for the case study.
