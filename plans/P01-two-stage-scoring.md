# Two-stage scoring change

Fixes the scoring limitation captured in `shaping/starlord-scoring-limitation-analysis.md` and the guard gap from `shaping/scoring-mistake-postmortem.md`. Every decision below was locked with the user in the grilling session on 2026-09-13 and revised after the user's file review the same day. The "Settled decisions" section is closed for debate. Items marked proposed are mechanics, not decisions, and can be adjusted at implementation time.

## Why

Starlord scores repos pass/fail per rule and sums weighted points. When several repos pass everything, they tie. The browser spike ended with five repos at 3.8 and the tie was broken by prose, not numbers. The fine marks ✅✅ and ⚠️ already appear in the shaping docs but are defined nowhere in the skill. This change makes them official and adds a guard against the rating mistake documented in the postmortem.

Sources:

- `shaping/starlord-scoring-limitation-analysis.md`. The problem and the fine scale proposal.
- `shaping/scoring-mistake-postmortem.md`. The Cloudflare ⚠️ mistake and the guard ideas.
- Spike artifacts at `groundcrew/.starsieve/browser-agent-spike/`. The real 5-way tie at 3.8.
- `groundcrew/shaping/ADR-002-browser-backend-decision.md`. The decision of record this change does not revisit.

## Settled decisions

### Scoring

1. Two stages.
   - **Filter score**: pass/fail per rule, unchanged. Cuts weak candidates.
   - **Ranking score**: fine scale, ranks the survivors.
2. Fine scale points, times the rule weight:

   | Mark | Points | Meaning |
   |---|---|---|
   | ✅✅ | 1.0 | clearly better than needed |
   | ✅ | 0.7 | fine |
   | ⚠️ | 0.3 | passes with real problems |
   | ❌ | 0.0 | fails |

   Rule weights stay: must-have 1.0, important 0.7, nice-to-have 0.4. Point provenance: the analysis doc's Phase 2 table. New locked home: `references/pipeline-detail.md`. The analysis doc says "3-level scale" in prose but its table lists 4 levels. The table wins.
3. Trigger: every candidate that passes all must-haves gets a ranking score. ⚠️ on a must-have passes. ❌ on a must-have cuts the candidate, which stays in the matrix as eliminated and unranked.
4. Evidence: every ✅✅ and ⚠️ cell carries a cited fact, same as ✅ today.
5. Accept the shift: a repo that merely meets every rule scores 70% of the possible points. Only exceeding everywhere reaches the old maximum. Scores are compared only within one run.

### Recommendation

1. Ranking scores rank candidates. Every comparison shows a trade-off table for the top 3, or all ranked candidates if fewer than 3.
2. Close call: when #1 and #2 are within 1.0 points, starlord states the gap and hands the call to the user. The worked example gap, 3.38 vs 3.17 = 0.21, defers.

### Guard

1. Phase 0 detects a separate validator mechanism. Already done in commit `545e837`: sub-agent, peer-agent, RLM, or similar, anything that keeps the validator off the main agent's context and LLM.
2. New step 4.4, before Checkpoint 4:
   - Separate validator available: send it the locked criteria text, the rubric, and the rated matrix. It flags ratings that contradict what a rule explicitly allows. That is the exact Cloudflare mistake class.
   - No separate validator: the same checklist runs as self critique.
3. Every guard run writes `{task-dir}/validator-report.json`, next to goal.md, from `templates/validator-report.template.json`. Fields: how it was written, peer-review agent or same agent self critique, plus the peer agent's name when applicable; findings if any; concise reasoning; verdict approved or rejected; timestamp. Rejected means the agent fixes the flagged ratings and reruns the guard until approved.
4. Phase 5 script, two additions:
    - Implement the score consistency check for real. Parse the four marks, recompute weight × points per cell, compare with the totals. Today the script promises this check and does none of it.
    - Check programmatically that validator-report.json exists and its verdict is approved. FAIL otherwise, in both guard modes.
    - Replace the deprecated `utcnow()` call in the same pass.

### Rubric

1. At lock time the agent drafts one "exceeds = <concrete thing>" line per rule, built from the grilling answers, no new questions for the user. The lines live in an Exceeds Definitions table in goal.md. Checkpoint 1 shows the rubric and waits for the user's permission before searching stars.
2. R1 rubric resolution, from the review. The two shaping docs conflicted about Cloudflare on R1: the analysis doc scored it ⚠️, the postmortem called that ⚠️ the smuggling mistake. Resolution: ✅✅ on R1 means fully self-contained, no external service or account. Cloud-API tools meet, they do not exceed. So Cloudflare gets ✅ on R1, not ⚠️ and not ✅✅. The corrected worked example: Playwright 3.38, Cloudflare 3.17, gap 0.21, close call, user decides.
3. New file `references/rubric-examples.md`, as small as possible. Two or three worked example rules with exceeds and meets lines, drawn from the spike, so future runs have a concrete pattern for writing rubrics. SKILL.md Phase 1.3 and pipeline-detail.md reference it. Seed content from the review draft:

    | Rule | ✅✅ exceeds means | ✅ meets means |
    |---|---|---|
    | Wrappable | Two or more paths among SDK, MCP server, CLI | Exactly one solid programmatic path |
    | Runs on runner | Fully self-contained, no external service or account | Works within runner constraints, self-contained or cloud-API |
    | Lightweight | Zero or near-zero install on the runner, no browser download, one small binary, or cloud-side rendering | Fits the session budget but with notable cost, for example a 300MB browser download |

    ⚠️ example for context: passes but needs workarounds, for example browser extension loading on headless CI.

### Naming, examples, style

1. The stages are called **filter score** and **ranking score**.
2. The corrected worked example, Playwright 3.38 vs Cloudflare 3.17, goes into `references/pipeline-detail.md`, Fit Check Format section. The plan and docs do not carry the old 2.77 figure anywhere, it encodes the ⚠️ mistake.
3. Writing style: one short section in SKILL.md, eight rules:
    - Plain words, no AI vocabulary (additionally, crucial, delve, leverage, pivotal, testament, landscape).
    - Short sentences, one idea each.
    - Numbers and mechanisms, not feelings.
    - Active voice, name the actor.
    - No em dashes, straight quotes, sentence case headings.
    - No chatbot filler (I hope this helps, let me know if).
    - Cut wordy phrases, "in order to" becomes "to".
    - Write for a first-time reader. Give context before jargon and internal shorthand.

    Covers checkpoint messages, fact cards, comparison.md, gaps.md, the recommendation. Skips run.log and internal JSON.

### Folders and templates

1. Template consolidation:
    - `assets/goal.template.md` moves to `templates/goal.template.md`.
    - `assets/comparison.template.md` moves to `templates/comparison.template.md`.
    - `templates/tool-availability-check.json` is already renamed by the user to `templates/tool-availability-check.template.json`. Register the rename in git.
    - New: `templates/validator-report.template.json`.
    - `assets/` keeps `examples/` only.
    - Reference updates, verified sites: SKILL.md Phase 0 checkpoint line (template path to the new name), Phase 1.3 (`templates/goal.template.md`), Phase 5 final output (`templates/comparison.template.md`). Scripts reference no template paths. VERIFICATION.md stays untouched, it is a historical record.

### History and cleanup

1. groundcrew: `git mv .starsieve/browser-agent-spike .starlord/browser-agent-spike`, delete the leftover empty `.starsieve`. Fix the stale word in goal.md, "starsieve will also pull" becomes "starlord will also pull". Leave run.log and validation.txt untouched, they are history.
2. Typo fixes folded into the Phase 0 commit areas: "Wit for feedback" becomes "Wait for feedback", "agent must checks" becomes "agent must check", the "Mandatory:" line in SKILL.md gets clean wording, missing spaces in "in`facts/`" and "in`gaps.md`", and the validatorAgent command field in the JSON template says the agent checks the harness, not `check-tools.sh`.

## File changes

### SKILL.md

- New Writing style section near the top, the eight rules above.
- Phase 1.3: agent drafts exceeds definitions into goal.md, points at `references/rubric-examples.md` for the pattern.
- Checkpoint 1: show criteria plus exceeds definitions, wait for explicit approval.
- Phase 4.2: two-stage scoring, filter score then ranking score.
- New Phase 4.4: conformance guard, separate validator or self critique, writes `{task-dir}/validator-report.json`.
- Checkpoint 4: matrix plus ranking scores plus trade-off table plus close-call verdict.
- Phase 5 table: score consistency implemented, new row for the validator report check.
- File structure section: task dir gains `validator-report.json`.
- Template path updates from decision 18.
- Typo fixes from decision 20.

### references/pipeline-detail.md

- Fit Check Format: the four marks with citations, plus the corrected worked example table.
- Scoring Formula: filter score and ranking score, the points table, tier rules (pass all must-haves, ⚠️ passes, ❌ cuts and unranks).
- Guard checklist for step 4.4, the validator report fields and location.
- Close-call rule, gap within 1.0 defers.
- Reference to `references/rubric-examples.md`.

### references/rubric-examples.md

- New, small. The seed table from decision 14.

### templates/goal.template.md

- Moved from assets/. Exceeds Definitions table under Locked Criteria, one row per rule.

### templates/comparison.template.md

- Moved from assets/. Matrix cells allow ✅✅, ✅, ⚠️, ❌, each with a cited fact except ❌.
- Ranking score table with per-rule point columns.
- Trade-off table for the top 3.
- Close-call line stating the gap and deferring to the user.

### templates/validator-report.template.json

- New. Fields per decision 10.

### templates/tool-availability-check.template.json

- Already renamed by the user. Typo fixes, validatorAgent command field describes the agent-side check.

### scripts/validate-comparison.py

- Parse ✅✅ before ✅, the mark order matters in matching.
- Score consistency: recompute weight × points from the matrix, compare with the ranking score table, FAIL on mismatch.
- Every ✅✅ and ⚠️ cell needs a citation, same rule as ✅.
- ⚠️ is a pass, not a gap. ❌ still lands in gaps.md.
- Validator report check: `{task-dir}/validator-report.json` exists and verdict is approved, FAIL otherwise.
- Replace `datetime.datetime.utcnow()` with a timezone-aware call.
- Align the header regex with the template's Priority column (proposed, the current regex expects Status).

### README.md

- Update "How it works" and the sample output to mention filter score, ranking score, the guard, and the validator report.
- Sample task folder gains `validator-report.json`.

### Unchanged on purpose

- `references/criteria-suggestions.md`. Criteria patterns do not change.
- `shaping/`. Stays the historical source.
- The old spike comparison.md. Not re-scored. ADR-002 is the decision of record.
- `VERIFICATION.md`. Historical verification against the old decision list, refresh is a separate pass.

## Proposed execution order (mechanics, not settled decisions)

1. Folder moves: git mv both assets templates into templates/, register the tool check rename.
2. Script work: validate-comparison.py marks parsing, math check, citations, validator report check, utcnow.
3. Typo fixes across SKILL.md, check-tools.sh, templates JSON.
4. Docs: SKILL.md sections, pipeline-detail.md with corrected worked example, rubric-examples.md, both templates, validator report template, README.
5. Self test: run the script against a synthetic comparison containing all four marks, confirm PASS. Then break the math on purpose, confirm FAIL. Then remove the validator report, confirm FAIL.
6. groundcrew move: git mv, stale word fix in goal.md, delete empty .starsieve.
7. Commits: one commit for the starlord repo, one for the groundcrew move.

## Out of scope

- A standing validator agent stage in the pipeline. The step 4.4 guard is enough until a second scoring mistake happens.
- Re-scoring historical runs.
- VERIFICATION.md refresh. It verifies against the old locked decision list, so a refresh belongs to a separate pass after this change lands.
