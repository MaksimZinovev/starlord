---
name: starsieve
description: Finds and compares GitHub repositories from the user starred list against custom criteria determined through interactive grilling. Use when selecting a library, tool, or framework from existing starred repos, when needing a systematic fact-grounded comparison of candidate repos. Don't use for general GitHub search, issue debugging, code review, or non-repo comparison tasks.
---

# Starsieve

Sieve the user's GitHub stars down to the real candidates, then compare them against custom criteria — grounded in facts, not vibes.

## Core Principle

Scripts handle deterministic work (pulling data, filtering, validation). The main LLM only touches judgment work (criteria locking, comparison, recommendation). Optional tools (Ollama, DeepWiki, Sideshow) reduce token cost or improve UX but are not required. All fallbacks are visible to the user.

## Prerequisites

- **Mandatory:** `gh` CLI authenticated (`gh auth login`). The skill cannot run without this.
- **Optional:** Ollama (local or cloud), DeepWiki MCP, Sideshow, `jq`.

---

## Phase 0: Tool Availability Check

Run `scripts/check-tools.sh` to detect what is available. The script prints a status report. Announce results to the user before proceeding.

```
✅ gh CLI        — authenticated as @username
✅ Ollama local  — glm-5.1 available
❌ DeepWiki      — not connected
✅ Sideshow      — connected
✅ jq            — available
```

If Ollama and DeepWiki are both missing, warn the user that the main LLM will handle all analysis (higher token usage) and ask for confirmation.

The check results determine which pipeline path each phase takes. Read `references/pipeline-detail.md` for the full decision tree of fallbacks.

---

## Phase 1: Criteria Locking

### 1.1 Collect Goal

Ask the user to state their goal, use case, or problem in one sentence. The user may optionally share additional context (files, links, pasted text). Save the goal to `./.starsieve/{task-slug}/goal.md`.

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

Write the final 3-5 locked criteria with priorities and constraints to `goal.md`. Copy the template from `assets/goal.template.md`.

### Checkpoint 1

Show the user the locked criteria table and ask: "Start searching your stars?" The user may adjust criteria before proceeding.

---

## Phase 2: Candidate Search

### 2.1 Pull Star List

Run `scripts/pull-stars.sh` to fetch the user's starred repos. The script uses a shared cache at `~/.cache/starsieve/raw-stars.json`. Pass `--refresh` to force a re-pull.

Output: `{task-dir}/candidates-raw.json` with all starred repos (name, description, topics, language, stars, pushed_at, license).

### 2.2 Keyword Filter

The script pre-filters by matching the user's goal keywords against repo description, topics, and language. This reduces the pool to a manageable size at zero token cost.

If the filtered pool has fewer than 3 repos, expand to GitHub search API (`gh api search/repositories`) using the goal keywords. Log this expansion to the user.

### 2.3 Semantic Classification

If Ollama is available, run `scripts/classify-candidates.py` which sends each candidate's metadata to a cheap Ollama model with the prompt: "Given the goal '{goal}', is this repo relevant? Y/N + one-line reason." Keep the top 8-12 candidates.

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
- **Cells:** ✅ (pass, with sourced fact) or ❌ (fail, with reason)
- **Notes:** explanation of failures, referencing the fact file

Every ✅ must reference a fact from `facts/` or `meta/`. No unsourced claims.

### 4.2 Score and Rank

Calculate weighted scores: `score = sum(priority_weight × {✅=1, ❌=0})`. Rank candidates by score. Present the ranked recommendation.

### 4.3 Highlight Gaps

List all known unknowns, missing data, and assumptions explicitly. Every ❌ cell that is a gap (rather than a confirmed failure) must be marked. Update `gaps.md`.

### Checkpoint 4

Show the user the fit check matrix + scores + ranked recommendation + gaps. Ask: "Run validation? Anything to refine?" The user may adjust priority weights or challenge specific cells.

---

## Phase 5: Validation

Run `scripts/validate-comparison.py {task-dir}` to verify the comparison:

| Check | What it verifies |
|-------|-----------------|
| Source tracing | Every ✅ in the matrix references a fact in `facts/` or `meta/` |
| Completeness | Every candidate has facts for every criterion |
| Score consistency | Weighted scores match the matrix arithmetic |
| Gap transparency | Every ❌ or missing fact is listed in `gaps.md` |
| File integrity | All referenced files exist in the task directory |

Output: PASS or FAIL with specific issues. If FAIL, fix the flagged issues and re-run.

### Final Output

Save the validated comparison to `{task-dir}/comparison.md` (copy structure from `assets/comparison.template.md`). The final output includes:
- The goal and locked criteria
- The fit check matrix with sourced facts
- Weighted scores and ranked recommendation
- All gaps and known unknowns
- Validation result

---

## File Structure

```
~/.cache/starsieve/
├── raw-stars.json          ← cached star list (shared across projects)

./.starsieve/{task-slug}/
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
└── validation.txt          ← validation script output
```

---

## Error Handling

- **`gh auth` not authenticated:** Stop. Tell the user to run `gh auth login` with read scope. Do not proceed.
- **Ollama not running:** Skip Ollama classification. Main LLM handles it. Announce the fallback.
- **DeepWiki can't index a repo:** Fall back to Ollama/LLM reading README. Log the fallback in `gaps.md`.
- **Star list empty or too small:** Expand to GitHub search API. Announce the expansion.
- **Validation fails:** Show specific failures. Fix unsourced claims or missing facts. Re-run validation.
- **Script permission error:** Run `chmod +x scripts/*.sh scripts/*.py`. Scripts should be executable.