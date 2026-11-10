# AI log

How AI tools were used on this case study, where they helped and where they were wrong.
Every incident below happened during the work and can be traced in the session transcripts in this folder.

## Tools used and for what

### Models and agents

| Tool | Used for |
|---|---|
| Claude Code (Claude Fable), one long main session and eight short ones | Reading the brief and the codebase, profiling the data, writing an instrumented replay of `legacy-sync`, the diagnosis, the target architecture, the executive summary, the worked examples, the diagram generator and the orchestration and review of subagents |
| Claude Code subagents (Claude Sonnet), four runs | Building the working slice, the build specification, the rollout plan and the solution design document, each from a written brief and each checked by the main session before it was accepted |
| Claude Code subagents (Claude Opus), three runs | A fresh-context code review of the slice, a security audit of the repository and an architecture challenge of the design against HIPAA and SOC 2. Read-only. Findings are in `AGENTIC_REVIEWS.md` at the repository root |
| Codex, in a separate directory | An independent second attempt at the written deliverables, kept apart from the Claude work so the two could be compared |
| Codex, as reviewer | Two adversarial reviews of the Claude deliverables. Both were static reads; neither ran the code |

### Skills and plugins

| Tool | Used for |
|---|---|
| pro-dev-skillset plugins (pro-quality code reviewer, pro-security audit skill and security architect) | The role files the three Opus reviewers followed. Installed at project scope in `.claude/settings.json` |
| `10x-document-writer`, a project skill written during the work | Keeping the HTML documents in one theme. The security audit found that one of its lines led agents to copy values from `data/` into documents |
| Impeccable design lint and the frontend-design plugin | Catching generated-looking layout and prose in the pages. Exceptions are recorded in `.impeccable/config.json` |
| A diagramming skill | Guidance for the hand-drawn SVG diagrams |

### Scripts, rendering and connectors

| Tool | Used for |
|---|---|
| Python 3, standard library only | The working slice, `analysis/legacy_trace.py`, `analysis/evaluate.py` and `docs/diagrams/build.py`. Also the throwaway scripts behind the data profiling and the count-only scan for values from `data/` |
| `unittest` and `pytest` (through `uv run`) | The 21 slice tests and the four `legacy-sync` tests |
| Headless Chrome, driven by the agent | Rendering pages and diagrams to check them by eye. Also printing the executive summary to confirm it fits one page |
| Mermaid, loaded from a CDN | The diagrams in the first version of the diagnosis page. Seven were later redrawn as generated SVG after a rendering fault; one script tag remains in `docs/current-system.html` |
| Playwright MCP server | Registered for browser checks of the pages |
| Gmail connector | Reading the email that delivered the brief, once, at the start of the main session |
| Claude Docs, a private hosted document | A working copy of the agentic review report. The copy of record is `AGENTIC_REVIEWS.md` |

As far as the transcripts show, no customer record was sent to any tool other than the two coding agents and their model providers.
The agents read `data/` directly and some script output containing rows from it entered their context.

## How the tools were directed

- Evidence before prose. The first instruction was to read and report, not to build. Every count in the documents comes from a script that can be re-run (`analysis/legacy_trace.py`, the slice itself). The documents say which.
- Two models kept apart. Claude and Codex worked in separate directories and were told not to read each other's output until the review step. That gave a second opinion that was not anchored on the first.
- Written briefs for subagents. Each brief stated the goal, the facts already established, the constraints and what to report, including failures. Output was verified against the source data or by rendering before it was accepted.
- Claims labelled by strength: read from the code, observed in the data, inferred or unknown. Vendor identities and production transports are marked as inferred or unknown throughout.
- The supplied code and data were treated as read-only evidence.
- The person directing the work set scope and caught things the tools did not: an unexplained decoration, a labelling task wrongly assigned to a person, a review workflow that existed only as a box on a diagram. They also checked the work against the brief several times, which is how the missing artifacts were found.

## Where AI meaningfully sped things up

1. Root causes in minutes.
   The agent read all 365 lines of `legacy-sync`, ran the replay and tied each of the six symptoms to a file and line.
   The human work was checking each claim against the code.
2. Claims turned into counts.
   Instead of reasoning about what the code might do, the agent wrote a wrapper that imports the legacy code and counts every decision: 43 of 905 orders matched by surname and zip, 77 email overwrites, 32 of 433 registrations rejected.
   A what-if run showed that turning off the address fallback alone makes 16 orders raise an uncaught error, which changed the rollout plan.
3. Finding the examples.
   Profiling eight files surfaced one person held as eight records across four systems, relatives filed on each other's accounts and two people with the same name and email.
   Ten of these became the worked examples.
4. Parallel drafting.
   The slice, the build specification and the rollout plan were written concurrently by three subagents in a few minutes each, which left the main session free to verify them.

## Where AI was wrong or misleading and how it was caught

1. A mislabelled headline number.
   The executive summary said 45 records had their email "rewritten by someone else's order".
   The 45 is every account whose email changed at all, including a person's own second address; only 31 of the 77 overwrites carried a different person's email.
   The first Codex review noticed the units did not match the diagnosis page. Claude then checked the trace output and found the label itself was wrong.
2. A status figure wrong by a factor of twenty.
   After the slice was built, Claude reported that 1,976 of 1,994 records had confidence 1.0.
   It had rounded to one decimal place; the true count at exactly 1.0 is 92.
   Caught by the second Codex review reading the CSV.
3. Nicknames counted as relatives.
   The first summary read 23 purchases on an account with a different first name as 23 misfiled purchases.
   About 9 were the same person under a nickname.
   Caught by printing the rows instead of trusting the count.
4. Trusting the shipped replay order.
   The first numbers came from the replay tool as shipped, which runs every order before any registration.
   Production would interleave them.
   Caught while tracing one household day by day, when the story did not match the counts. The trace gained a time-ordered mode and both sets of numbers are reported.
5. Claims ahead of the evidence.
   The architecture page called the slice its reference implementation before the slice existed. It also described match scores as calibrated probabilities with a 0.90 threshold nothing had measured.
   Caught by the first Codex review. The threshold is now stated as provisional and the scores as uncalibrated.
6. A validation plan that could not support its own claim.
   The first labelling sample was spread evenly across score-sorted pairs, yet the evaluator printed a confidence interval as if it were a random sample.
   Caught by the second Codex review. The sample is now a seeded simple random sample of automatic links.
7. Safeguards promised in a document and missing from the code.
   The rollout page said plus-tag email matches stay in review, while the slice folded plus tags into its match key.
   One subagent wrote the page and another the code, each from its own brief.
   Caught by the second Codex review. The slice now enforces the rule and a test covers it.
8. An assumption presented as a finding.
   The count of kits whose buyer is still told to register depends on how an unused helper would be wired, which the repository does not show.
   The detail page said so and the summary did not.
   Caught by the first Codex review.
9. Work assigned to a person that did not need one.
   Claude said the labelling had to be done by hand by the candidate.
   The real requirement is a labeller independent of the matcher, which a second model can provide with a person settling disagreements.
   Caught when the person directing the work asked why they were needed.
10. A design reduced to a box.
    Human review appeared in the architecture as a queue and a threshold, with no lifecycle, service levels, error handling or safeguards.
    Caught by the person directing the work, who asked for the asynchronous workflow to be designed properly.
11. Decoration without meaning and a diagram that rendered wrongly.
    The agent added a barcode graphic under each title that nothing explained. A diagram library rendered labels beginning "1." as an error message.
    The first was caught by a reader asking what it was for, the second only because every diagram was rendered and looked at.
12. Recolouring that erased meaning.
    A theme change turned ordinary system boxes the same red as failure boxes. It turned the "known" status tag the same red as "unknown".
    Caught on the next render. Red is now reserved for failures.
13. Data treated as PHI in words and copied in practice.
    The agent quoted rows from `data/` in the diagnosis page and the worked examples. It also described the transcripts as redacted when names remained in the main session export.
    The project writing skill it had written told agents that case-data identifiers could be used as examples.
    Caught by the agentic security audit, which built value lists from the CSVs and searched the rest of the repository for them.
    Not yet fixed.
14. A review queue that hid the evidence against a merge.
    The slice checked the birthdate, first-name and chart rules only for automatic links.
    Nine of the 26 review items pair two people with different known birthdates and show only agreeing reason codes.
    Caught by the agentic code review, which reproduced it on the shipped output.
    Not yet fixed.
15. A build specification weaker than the prototype it describes.
    The subagent that wrote the build spec listed two of the three clustering constraints and left out the first-name rule, so the spec as written would merge twins.
    Caught by the agentic architecture challenge comparing the spec against the slice.
    Not yet fixed.

## What is still unverified

- The matcher's false-match rate has not been measured. A random sample of 100 automatic links is drawn and waiting for labels.
- The solution design document was drafted by a subagent from the other pages. Its structure, links and figures were checked. It has not been read line by line by a person.
- Service levels, capacity and staffing figures in the design document are proposals with no source in the case material. They are labelled as such.
- The agentic reviews of 2026-11-09 are recorded in `AGENTIC_REVIEWS.md` with status open. Its list of eight changes needed has not been worked yet. Until it is, the redaction statement below is not true of `claude-session-08.md`, which still holds names from `data/`.
- The HIPAA and SOC 2 citations in those reviews are an engineer's reading. Counsel has not confirmed them.

## Prompt history and transcripts

The session transcripts are in this folder.

| File | What it is |
|---|---|
| `claude-session-08.md` | The main Claude Code session, where almost all of the Claude work happened |
| `claude-session-01.md` to `claude-session-07.md` | Short Claude Code sessions in the same project |
| `claude-session-09.md` | The session that ran the three agentic reviews and recorded them |
| `codex-session-01.md` to `codex-session-04.md` | The Codex sessions: the independent attempt and the two reviews |

They are redacted exports, not raw files.
Each holds the prompts, the assistant's replies and, for Claude, one line per tool call.
Tool output, images and private tool configuration are left out. Personal contact details and the home directory path are replaced with placeholders.
Some messages sent while the agent was mid-task are recorded differently by the tool and may be missing from the main session export.
