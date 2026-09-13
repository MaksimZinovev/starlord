---
name: starlord
description: Finds and compares GitHub repositories from the user starred list against custom criteria determined through interactive grilling. Use when selecting a library, tool, or framework from existing starred repos, when needing a systematic fact-grounded comparison of candidate repos. Don't use for general GitHub search, issue debugging, code review, or non-repo comparison tasks.
---
# Starlord

Sieve the user's GitHub stars down to the real candidates, then compare them against custom criteria — grounded in facts, not vibes.

## Core Principle

Scripts handle deterministic work (pulling data, filtering, validation). The main LLM only touches judgment work (criteria locking, comparison, recommendation). Optional tools (Ollama, DeepWiki, Sideshow) reduce token cost or improve UX but are not required. All fallbacks are visible to the user.

## Writing Style

Every checkpoint message, fact card, and document in this skill follows eight rules:

- Plain words. No AI vocabulary: additionally, crucial, delve, leverage, pivotal, testament, landscape.
- Short sentences. One idea per sentence.
- Numbers and mechanisms, not feelings.
- Active voice. Name the actor.
- No em dashes. Straight quotes. Sentence case headings.
- No chatbot filler: "I hope this helps", "let me know if".
- Cut wordy phrases. "In order to" becomes "to".
- Write for a first-time reader. Give context before jargon and internal shorthand.

## Prerequisites

- **Mandatory:** `gh` CLI authenticated (`gh auth login`). The skill cannot run without this.
- **Optional:** Ollama (local or cloud), DeepWiki MCP, Sideshow, `jq`.
- **Mandatory:** create a unique task directory for each run (e.g., `./.starlord/{task-slug}/`) to store intermediate files and logs. The skill will not run if the task directory already exists.

---

## Phase 0: Tool Availability Check

Run `scripts/check-tools.sh {task-dir}` to detect what is available. The script prints a status report. Check availability and announce results to the user before proceeding.

```
✅ gh CLI        — authenticated as @username
✅ Ollama local  — glm-5.1 available
❌ DeepWiki      — not connected
✅ Sideshow      — connected
✅ jq            — available
```

If Ollama and DeepWiki are both missing, warn the user that the main LLM will handle all analysis (higher token usage) and ask for confirmation.

If both Ollama local and Ollama cloud are available, ask the user which to prefer:

- **Ollama local** — zero cost, but limited to models installed on the machine. Faster if already running.
- **Ollama cloud** — pay per token, but access to larger/cheaper models. Works from any machine.
  Recommend local if available (free, no network latency). Record the choice in the execution log.

The check results determine which pipeline path each phase takes. Read `references/pipeline-detail.md` for the full decision tree of fallbacks.

Checkpoint: before proceeding to the next phase, write tool availability information into `~/.cache/starlord/{project_name}-{timestamp}/tool-availability-check.json`. Use template from `templates/tool-availability-check.template.json`. Report to user: concise status of availability check, path to written file, and any faced issues. Wait for feedback before proceeding.

---

## Phase 1: Criteria Locking

### 1.1 Collect Goal

Ask the user to state their goal, use case, or problem in one sentence. The user may optionally share additional context (files, links, pasted text). Save the goal to `./.starlord/{task-slug}/goal.md`.

### 1.2 Grill to Lock Criteria

Ask 3-5 questions, one at a time. Each question:

- Presents 2-4 options
- Includes a recommended option with reasoning
- Waits for the user's answer before asking the next question

The questions should surface:

- **Criteria** — what matters for this decision (e.g., "Does bundle size matter?" / "Is active maintenance critical?")
- **Priorities** — weight each criterion (must-have, important, nice-to-have)
- **Constraints** — hard limits (e.g., "must be MIT licensed", "must support React 19")
- **Scope** — what to exclude (e.g., "not interested in CLI-only tools")

See `references/criteria-suggestions.md` for common criteria patterns to draw from when formulating questions.

### 1.3 Save Locked Criteria

Write the final 3-5 locked criteria with priorities and constraints to `goal.md`. Copy the template from `templates/goal.template.md`. Then draft one "exceeds" line and one "meets" line per rule into the Exceeds definitions table, from the grilling answers. Do not ask the user new questions for this. See `references/rubric-examples.md` for the pattern.

### Checkpoint 1

Show the user the locked criteria table plus the exceeds definitions. Wait for explicit approval before any search. Ask: "Start searching your stars?" The user may adjust criteria before proceeding.

---

## Phase 2: Candidate Search

### 2.1 Pull Star List

Run `scripts/pull-stars.sh {task-dir}` to fetch the user's starred repos. The script uses a shared cache at `~/.cache/starlord/raw-stars.json`. Pass `--refresh` to force a re-pull.

Output: `{task-dir}/candidates-raw.json` with all starred repos (name, description, topics, language, stars, pushed_at, license).

### 2.2 Keyword Filter

The script pre-filters by matching the user's goal keywords against repo description, topics, and language. This reduces the pool to a manageable size at zero token cost.

If the filtered pool has fewer than 3 repos, expand to GitHub search API (`gh api search/repositories`) using the goal keywords. Log this expansion to the user.

### 2.3 Semantic Classification

If Ollama is available, run `scripts/classify-candidates.py {task-dir} {candidates-raw.json} "{goal}"` which sends each candidate's metadata to a cheap Ollama model with the prompt: "Given the goal '{goal}', is this repo relevant? Y/N + one-line reason." Keep the top 8-12 candidates.

If Ollama is NOT available, the main LLM classifies candidates from the pre-filtered pool. This costs more tokens but works.

### Checkpoint 2

Show the user the 8-12 candidate repos with a one-line relevance reason each. Ask: "Proceed to fact-gathering?" The user may remove repos, add repos manually, or request a larger pool.

---

## Phase 3: Fact Gathering

### 3.1 Pull Metadata

Run `scripts/pull-meta.sh {repo-owner/repo-name}` for each candidate. The script pulls via `gh api`:

- Description, stars, forks, watchers
- License, language, topics
- Last push date, open/closed issue counts
- Release history (latest release, frequency)
- README content (saved to `{task-dir}/meta/{repo-slug}_readme.md`)

Saved to `{task-dir}/meta/{repo-slug}_meta.json`. Zero LLM tokens.

### 3.2 Deep Fact Gathering

For each criterion, gather a fact per candidate. The tool depends on availability:

1. **DeepWiki available:** Use `deepwiki_ask_question` to ask criterion-specific questions per repo (e.g., "How does this repo handle theming?"). Save answers to `{task-dir}/facts/{repo-slug}_facts.json`.
2. **DeepWiki NOT available, Ollama available:** Send README + package.json to Ollama with the criterion questions. Ollama summarizes and answers. Save to `facts/`.
3. **Neither available:** Main LLM reads the pulled README and metadata, answers the criterion questions. Higher token cost.

### 3.3 Gap Detection

For each candidate × criterion, check if a fact was successfully gathered. If DeepWiki/Ollama could not answer, flag it as a gap. Collect all gaps into `{task-dir}/gaps.md`.

### Checkpoint 3

Show the user compact fact cards per repo + any gaps found. Ask: "Proceed to comparison?" The user may request deeper investigation on specific repos or accept the gaps.

---

## Phase 4: Comparison

### 4.1 Build Fit Check Matrix

Read `references/pipeline-detail.md` section "Fit Check Format" for the exact table structure. The matrix has:

- **Rows:** locked criteria (with priority weights)
- **Columns:** candidate repos
- **Cells:** ✅✅, ✅ or ⚠️ (pass, each with a cited fact) or ❌ (fail, with reason)
- **Notes:** explanation of failures, referencing the fact file

Every ✅✅, ✅ and ⚠️ cell must reference a fact from `facts/` or `meta/`. No unsourced claims. ⚠️ is a pass, not a gap.

### 4.2 Score and Rank

Scoring runs in two stages.

**Filter score:** pass or fail per rule. ✅✅, ✅ and ⚠️ pass. ❌ fails. A repo that fails any Must-have rule is eliminated. It stays in the matrix, marked eliminated, and gets no ranking score.

**Ranking score:** every repo that passes all Must-have rules gets a ranking score: `score = sum(rule weight × mark points)`. Mark points: ✅✅=1.0, ✅=0.7, ⚠️=0.3, ❌=0.0. Read `references/pipeline-detail.md`, section "Scoring formula", for the full rules.

Rank the surviving repos by ranking score. Show the ranking score table, the trade-off table for the top 3, and the close-call verdict: when #1 and #2 are within 1.0 points, state the gap and hand the call to the user.

### 4.3 Highlight Gaps

List all known unknowns, missing data, and assumptions explicitly. Every ❌ cell that is a gap (rather than a confirmed failure) must be marked. Update `gaps.md`. ⚠️ is a pass and never lands in gaps.md as a gap.

### 4.4 Conformance Guard

Check the rated matrix against the rule text before Checkpoint 4:

1. If Phase 0 detected a separate validator (sub-agent, peer-agent, RLM or similar), send it the locked criteria text, the exceeds definitions from goal.md, and the rated matrix.
2. If no separate validator is available, run the same checklist as self critique.
3. Flag every rating that contradicts what a rule explicitly allows. The known mistake class: a constraint the user relaxed during grilling, smuggled back into the rating. Example: ⚠️ on a rule whose text explicitly allows cloud-API tools.
4. Fix every flagged rating and rerun the guard until the verdict is approved.

Write `{task-dir}/validator-report.json` from `templates/validator-report.template.json`, next to goal.md. See `references/pipeline-detail.md`, section "Conformance guard (Phase 4.4)", for the report fields. The Phase 5 script fails the run when the file is missing or the verdict is not approved.

### Checkpoint 4

Show the user the fit check matrix + ranking scores + trade-off table + close-call verdict + gaps. Ask: "Run validation? Anything to refine?" The user may adjust priority weights or challenge specific cells.

---

## Phase 5: Validation

Run `scripts/validate-comparison.py {task-dir}` to verify the comparison:

| Check             | What it verifies                                               |
| ----------------- | -------------------------------------------------------------- |
| Source tracing    | Every ✅✅, ✅ and ⚠️ cell references a fact in `facts/` or `meta/` |
| Completeness      | Every candidate has fact or meta files                         |
| Tier rules        | A ❌ on a Must-have eliminates the repo. Eliminated repos get no ranking score |
| Score consistency | Ranking scores recompute from the matrix: rule weight × mark points |
| Gap transparency  | Every ❌ is listed in `gaps.md`                                 |
| Validator report  | `validator-report.json` exists and its verdict is approved      |
| File integrity    | All referenced files exist in the task directory               |

Output: PASS or FAIL with specific issues. If FAIL, fix the flagged issues and re-run.

### Final Output

Save the validated comparison to `{task-dir}/comparison.md` (copy structure from `templates/comparison.template.md`). The final output includes:

- The goal and locked criteria
- The fit check matrix with sourced facts
- Ranking scores, the trade-off table, and the ranked recommendation
- All gaps and known unknowns
- Validation result

---

## File Structure

```
~/.cache/starlord/
├── raw-stars.json          ← cached star list (shared across projects)

./.starlord/{task-slug}/
├── goal.md                 ← user goal + locked criteria
├── candidates-raw.json     ← all stars (pre-filter)
├── candidates.json         ← filtered 8-12 candidates
├── meta/                   ← script-pulled metadata + READMEs
│   ├── {repo}_meta.json
│   └── {repo}_readme.md
├── facts/                  ← DeepWiki/Ollama/LLM answers per criterion
│   └── {repo}_facts.json
├── comparison.md           ← fit check matrix + scores + recommendation
├── gaps.md                 ← known unknowns, missing data
├── validator-report.json   ← conformance guard verdict (Phase 4.4)
├── validation.txt          ← validation script output
└── run.log                 ← execution log (all phases, timestamps, tool choices)
```

---

## Error Handling

- **`gh auth` not authenticated:** Stop. Tell the user to run `gh auth login` with read scope. Do not proceed.
- **Ollama not running:** Skip Ollama classification. Main LLM handles it. Announce the fallback.
- **DeepWiki can't index a repo:** Fall back to Ollama/LLM reading README. Log the fallback in `gaps.md`.
- **Star list empty or too small:** Expand to GitHub search API. Announce the expansion.
- **Validation fails:** Show specific failures. Fix unsourced claims or missing facts. Re-run validation.
- **Script permission error:** Run `chmod +x scripts/*.sh scripts/*.py`. Scripts should be executable.

---

## Execution Log

Every phase appends structured entries to `{task-dir}/run.log`. The log answers questions like: "Was Ollama local or cloud used?", "Which phase failed?", "How long did each step take?"

Format: `[timestamp] [PHASE] [STATUS] message`

| Phase  | What gets logged                                                                   |
| ------ | ---------------------------------------------------------------------------------- |
| PHASE0 | Tool availability results (gh, Ollama local/cloud, DeepWiki, jq)                   |
| PHASE1 | Criteria locked (count, priorities) — logged by agent                             |
| PHASE2 | Cache hit/miss, repo count pulled, Ollama mode used, candidates kept               |
| PHASE3 | Per-repo metadata pulled (stars, license), DeepWiki vs Ollama fallback, gaps found |
| PHASE4 | Matrix built, scores calculated — logged by agent                                 |
| PHASE5 | Validation result (PASS/FAIL, claim count, warnings)                               |

### Agent Logging Responsibility

The agent must log at these points (scripts log their own steps automatically):

1. **After Phase 1 (criteria locked):** Call `scripts/log.sh {task-dir} PHASE1 OK "{N} criteria locked, priorities: {list}"`
2. **At each checkpoint:** Call `scripts/log.sh {task-dir} CHECKPOINT{N} OK "user approved {what}"` or `... ADJUSTED "user changed {what}"`
3. **After Phase 4 (comparison built):** Call `scripts/log.sh {task-dir} PHASE4 OK "matrix built, {N} candidates ranked"`
4. **On any fallback:** Call `scripts/log.sh {task-dir} {PHASE} FALLBACK "{what fell back, why}"` — e.g., "DeepWiki unavailable for {repo}, used Ollama"

### Reading the Log

At any point, the agent can read `{task-dir}/run.log` to answer user questions about execution:

- "What tools were used?" — grep `PHASE0` entries
- "Did Ollama cloud or local run?" — grep for `Ollama local` or `Ollama cloud`
- "Any failures?" — grep for `FAIL` or `WARN` or `FALLBACK`
- "How many repos were pulled?" — grep `PHASE2` for repo count
