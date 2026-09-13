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

```markdown
## Fit Check

| Req | Requirement | Priority | Repo-A | Repo-B | Repo-C |
|-----|-------------|----------|--------|--------|--------|
| R0 | Bundle size under 10kb | Must-have | ✅ [meta/repo-a_meta.json] | ❌ | ✅ [meta/repo-c_meta.json] |
| R1 | Active maintenance (push < 6mo) | Important | ✅ [meta/repo-a_meta.json] | ✅ [meta/repo-b_meta.json] | ❌ [gaps.md] |
| R2 | TypeScript types included | Must-have | ✅ [facts/repo-a_facts.json] | ✅ [facts/repo-b_facts.json] | ✅ [facts/repo-c_facts.json] |

**Weighted Scores:**
| Repo | Score | Rank |
|------|-------|------|
| Repo-A | 3.0 | 🥇 |
| Repo-B | 2.0 | 🥈 |
| Repo-C | 2.0 | 🥉 |

**Priority weights:** Must-have=1.0, Important=0.7, Nice-to-have=0.4

**Notes:**
- Repo-C fails R1: last push was 14 months ago [meta/repo-c_meta.json]
- Repo-A ✅ R0: 4.2kb gzipped [meta/repo-a_meta.json]
```

### Scoring Formula

```
score = Σ (priority_weight × {✅=1, ❌=0})

Priority weights:
  Must-have  = 1.0
  Important  = 0.7
  Nice-to-have = 0.4
```

### Source Reference Format

Every ✅ cell must include a bracketed reference to the source file:

- `[meta/{repo-slug}_meta.json]` — for data pulled by script
- `[facts/{repo-slug}_facts.json]` — for DeepWiki/Ollama answers
- The validation script checks these references exist

### Gap Marking

A ❌ cell can be:

- **Confirmed fail** — the repo genuinely doesn't meet the criterion (has a source)
- **Gap** — could not determine (DeepWiki unavailable, no data). Mark with `[gaps.md]`

Both types must appear in `gaps.md`, but gaps specifically note "unknown — no data available."
