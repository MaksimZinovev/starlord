# Pipeline Detail

Full decision tree for each phase, including fallback paths.

## Phase 0: Tool Detection Fallbacks

| Tool | Available | Phase Impact | Fallback |
|------|-----------|-------------|----------|
| gh CLI | ✅ | All phases depend on it | None — skill cannot run |
| Ollama | ✅ | Phase 2 (classify), Phase 3 (fact-gather) | Skip to LLM |
| Ollama | ❌ | Phase 2: main LLM classifies candidates | Higher token cost |
| Ollama | ❌ | Phase 3: main LLM reads READMEs | Higher token cost |
| DeepWiki | ✅ | Phase 3: deep architecture questions | Use DeepWiki first |
| DeepWiki | ❌ | Phase 3: Ollama reads README | If no Ollama, LLM reads README |
| jq | ✅ | Scripts use jq for JSON | None |
| jq | ❌ | Scripts fall back to python3 for JSON parsing | None |

## Cache Lifecycle

```
~/.cache/starlord/raw-stars.json   ← shared across all projects
~/.cache/starlord/raw-stars.age    ← timestamp of last pull
```

- Default freshness: 24 hours
- `--refresh` flag: force re-pull regardless of age
- Env override: `STARLORD_CACHE_DIR=/custom/path`
- First run: pulls all stars (20 API calls for 2000 stars, ~5-10s)
- Subsequent runs: instant (reads cache)
- If cache corrupted: delete `~/.cache/starlord/` and re-run

## Phase 2: Keyword Filter Logic

The script filters by matching goal keywords against:

- `description` field (case-insensitive substring match)
- `topics` array (exact match)
- `language` field (exact match)

Example: goal "state management library for React" filters for repos where:

- description contains "state" OR "management" OR "react"
- OR topics include "state-management" OR "react" OR "redux"
- OR language is "TypeScript" OR "JavaScript"

If filtered pool < 3 repos: expand to `gh api search/repositories?q=...`

## Phase 3: DeepWiki Integration

For each candidate repo, the agent calls `deepwiki_ask_question` with criteria-specific questions.

Example questions for criterion "theming support":

- "Does this repo support custom themes? How is theming implemented?"
- "Are there CSS variables, a theme provider, or a style override system?"

Example questions for criterion "bundle size":

- "What is the bundle size of this library? Is it tree-shakeable?"
- "Does it support ESM imports for tree-shaking?"

If DeepWiki returns "repo not indexed":

1. Try `deepwiki_read_wiki_structure` to trigger indexing
2. If still not available, fall back to Ollama reading README
3. If no Ollama, fall back to main LLM reading README
4. Log the fallback in `gaps.md`

## Fit Check Format

The matrix rates every candidate against every locked rule with four marks:

| Mark | Points | Meaning |
|------|--------|---------|
| ✅✅ | 1.0 | clearly better than needed |
| ✅ | 0.7 | fine |
| ⚠️ | 0.3 | passes with real problems |
| ❌ | 0.0 | fails |

Every ✅✅, ✅ and ⚠️ cell carries a cited fact. A ❌ cell needs no fact but must appear in gaps.md. Rate cells against the exceeds definitions in goal.md. See `references/rubric-examples.md` for worked examples of exceeds and meets lines.

```markdown
## Fit Check

| Req | Requirement | Priority | Repo-A | Repo-B | Repo-C |
|-----|-------------|----------|--------|--------|--------|
| R0 | Bundle size under 10kb | Must-have | ✅✅ [meta/repo-a_meta.json] 4.2kb gzipped | ✅ [meta/repo-b_meta.json] 7.9kb gzipped | ❌ [gaps.md] |
| R1 | Runs on the runner | Must-have | ✅✅ [facts/repo-a_facts.json] fully self-contained | ✅ [facts/repo-b_facts.json] cloud-API, rule allows it | ✅ [facts/repo-c_facts.json] self-contained |
| R2 | TypeScript types included | Must-have | ✅ [facts/repo-a_facts.json] ships its own types | ✅ [facts/repo-b_facts.json] ships its own types | ⚠️ [facts/repo-c_facts.json] types via separate package |

**Notes:**
- Repo-C fails R0: unpacked size is 240kb [meta/repo-c_meta.json]
- Repo-A exceeds R0: 4.2kb gzipped, less than half the limit [meta/repo-a_meta.json]
```

### Worked Example

Two candidates in the browser agent spike passed every must-have rule. Binary scoring tied them at 3.8. The ranking score separates them:

| Req | Weight | Playwright | Cloudflare Browser Run |
|-----|--------|------------|------------------------|
| R0 Wrappable | 1.0 | ✅✅ (1.00) SDK + MCP + CLI | ✅✅ (1.00) REST + MCP + CDP |
| R1 Runs on runner | 1.0 | ✅✅ (1.00) runs locally, zero external deps | ✅ (0.70) cloud-API tool, the rule allows it |
| R2 Maintenance | 0.7 | ✅ (0.49) actively maintained | ✅ (0.49) actively maintained |
| R3 Lightweight | 0.7 | ✅ (0.49) 300MB+ browser download | ✅✅ (0.70) zero browser download |
| R4 TS/JS native | 0.4 | ✅✅ (0.40) pure TypeScript | ✅ (0.28) TS-compatible, browser is remote |
| **Ranking total** | | **3.38** | **3.17** |

The gap is 3.38 − 3.17 = 0.21. That is within 1.0, so this is a close call: state the gap and hand the call to the user.

### Scoring formula

Scoring runs in two stages.

**Stage 1: filter score.** Pass or fail per rule, unchanged. ✅✅, ✅ and ⚠️ pass. ❌ fails. A candidate that fails any Must-have rule is eliminated. It stays in the matrix, marked eliminated, and gets no ranking score.

**Stage 2: ranking score.** Every candidate that passes all Must-have rules gets a ranking score:

```text
ranking score = Σ (rule weight × mark points)

Mark points:      ✅✅=1.0, ✅=0.7, ⚠️=0.3, ❌=0.0
Priority weights: Must-have=1.0, Important=0.7, Nice-to-have=0.4
```

The point values come from the Phase 2 table in `shaping/starlord-scoring-limitation-analysis.md`. This section is the locked home for those numbers.

A repo that merely meets every rule scores 70% of the possible points. Only a repo that exceeds everywhere reaches the maximum. Compare scores only within one run.

### Close-call rule

When #1 and #2 are within 1.0 points, state the gap and hand the call to the user. When the gap is larger, name the winner and the facts that decide it.

### Conformance guard (Phase 4.4)

Before Checkpoint 4, check the rated matrix against the rule text:

1. If a separate validator is available (sub-agent, peer-agent, RLM or similar, detected in Phase 0), send it the locked criteria text, the exceeds definitions, and the rated matrix.
2. If no separate validator is available, run the same checklist as self critique.
3. The checklist: flag every rating that contradicts what a rule explicitly allows. The known mistake class is a constraint the user relaxed during grilling, smuggled back into the rating. Example: ⚠️ on a rule whose text explicitly allows cloud-API tools.
4. Fix every flagged rating and rerun the guard until the verdict is approved.

Every guard run writes `{task-dir}/validator-report.json`, next to goal.md, from `templates/validator-report.template.json`:

| Field | Content |
|-------|---------|
| mode | "peer-review" or "self-critique" |
| peerAgent | the peer agent's name, when mode is "peer-review", otherwise null |
| findings | flagged ratings, empty list when none |
| reasoning | concise reason for the verdict |
| verdict | "approved" or "rejected" |
| timestamp | ISO 8601 with timezone offset |

The Phase 5 script fails the run when this file is missing or when the verdict is not approved. This applies in both guard modes.

### Source reference format

Every ✅✅, ✅ and ⚠️ cell must include a bracketed reference to the source file:

- `[meta/{repo-slug}_meta.json]` for data pulled by script
- `[facts/{repo-slug}_facts.json]` for DeepWiki, Ollama, or LLM answers
- The validation script checks that these references exist

### Gap marking

A ❌ cell can be:

- **Confirmed fail**, the repo genuinely does not meet the rule, with a source
- **Gap**, could not determine (DeepWiki unavailable, no data), marked with `[gaps.md]`

Both types must appear in `gaps.md`, but gaps specifically note "unknown, no data available". ⚠️ is a pass with real problems. It is not a gap and never lands in gaps.md as one.
