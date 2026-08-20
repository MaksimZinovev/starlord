# Verification Review: starsieve SKILL.md vs Locked Decisions

**Date:** 2026-08-20  
**Source of locked decisions:** Sideshow session `Z66S_mxjs0I` (13 surfaces)  
**Artifacts verified:** `SKILL.md`, `references/pipeline-detail.md`, `references/criteria-suggestions.md`, `assets/goal.template.md`, `assets/comparison.template.md`, `scripts/check-tools.sh`, `scripts/pull-stars.sh`, `scripts/classify-candidates.py`, `scripts/pull-meta.sh`, `scripts/validate-comparison.py`

---

## Locked Decisions Checklist

| # | Locked Decision | Source | Status | Evidence |
|---|----------------|--------|--------|----------|
| 1 | **Domain: A — Library/tool selection from starred repos** | Q1 settled | ✅ MATCH | Frontmatter: "from the user starred list"; Phase 2.1: `pull-stars.sh` fetches starred repos |
| 2 | **Dynamic grilling criteria (no templates, no defaults)** | Q2 settled | ✅ MATCH | Phase 1.2: "Ask 3-5 questions, one at a time"; `criteria-suggestions.md` header: "Not templates — use as inspiration" |
| 3 | **Output: Fact cards + scored matrix + recommendation** | Q3 settled | ✅ MATCH | Phase 4: fit check matrix (4.1), weighted scoring (4.2), gaps (4.3); `comparison.template.md` has all three |
| 4 | **Token economy: Scripts → DeepWiki → Ollama → LLM** | Q4 settled (option C) | ✅ MATCH | Phase 3.2: three-tier fallback DeepWiki → Ollama → Main LLM; `pipeline-detail.md` Phase 3 section confirms |
| 5 | **Candidate search: script pull → keyword filter → Ollama classify → 8-12** | Q4b | ✅ MATCH | Phase 2.1–2.3; `classify-candidates.py` defaults `--max 12` |
| 6 | **DeepWiki: fact-gathering only, NOT search** | Q4c | ✅ MATCH | DeepWiki only appears in Phase 3; absent from Phase 2; `pipeline-detail.md` confirms |
| 7 | **Data storage: shared cache + per-task dir** | Q4d | ✅ MATCH | `~/.cache/starsieve/raw-stars.json` (shared); `./.starsieve/{task-slug}/` (per-task); `pull-stars.sh` uses `STARSIEVE_CACHE_DIR` env override |
| 8 | **5-phase pipeline** | Pipeline summary | ✅ MATCH | SKILL.md: Phase 0 (tool check) + Phases 1–5 |
| 9 | **4 checkpoints at phase boundaries** | Checkpoints surface | ✅ MATCH | Checkpoints 1–4 after criteria, candidates, facts, comparison |
| 10 | **Tool-agnostic: gh mandatory, rest optional with visible fallbacks** | Tool-agnostic surface | ✅ MATCH | Phase 0: `check-tools.sh`; prerequisites table; `pipeline-detail.md` fallback matrix |
| 11 | **Skill name** | Q5 recommended `repo-compare` | ⚠️ DEVIATION | Actual name: `starsieve`. Final surface title confirms user chose this name. See note below. |
| 12 | **Validation: 5 checks** | Q5 | ✅ MATCH | Phase 5 table: source tracing, completeness, score consistency, gap transparency, file integrity; `validate-comparison.py` implements all 5 |

---

## Cross-Cutting Consistency Checks

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Priority weights | Must-have=1.0, Important=0.7, Nice-to-have=0.4 | Same across `criteria-suggestions.md`, `pipeline-detail.md`, `goal.template.md`, `comparison.template.md` | ✅ |
| Max criteria | 3–5 | Phase 1.2: "3-5 questions"; `criteria-suggestions.md`: "Maximum 5 criteria" | ✅ |
| Cache freshness | 24h default, `--refresh` override | `pull-stars.sh`: `CACHE_AGE < 86400`; `--refresh` flag | ✅ |
| Cache env var | Originally `REPO_COMPARE_CACHE_DIR` | `STARSIEVE_CACHE_DIR` (adapted for name change) | ✅ |
| Task dir naming | Originally `./.repo-compare/{task-slug}/` | `./.starsieve/{task-slug}/` (adapted for name change) | ✅ |
| File structure | goal.md, candidates.json, meta/, facts/, comparison.md, gaps.md | All present + additions: candidates-raw.json, {repo}_readme.md, validation.txt | ✅ |
| Sideshow checkpoints | "Each checkpoint is a sideshow post" | SKILL.md: "Show the user..." (Sideshow-agnostic, per later tool-agnostic decision) | ✅ |
| DeepWiki detection in Phase 0 | Can't detect from shell | `check-tools.sh`: "❓ DeepWiki — agent must verify MCP connection" | ✅ |

---

## Deviations (2)

### 1. Skill name: `starsieve` vs recommended `repo-compare` — ⚠️ Accepted deviation

**Locked recommendation:** Q5 recommended `repo-compare` (option A).  
**Actual:** `starsieve`.  
**Verdict:** The final surface title is "Starsieve skill built and validated", confirming the user explicitly chose this name during the build phase. All internal paths (`~/.cache/starsieve/`, `./.starsieve/`, `STARSIEVE_CACHE_DIR`) were consistently adapted. **This is a user override, not a violation.**

### 2. Q1 scope: GitHub search API expansion — ⚠️ Minor scope expansion

**Locked:** Q1 settled as "A — Library/tool selection" (stars only, not discovery + search).  
**Actual:** Phase 2.2 allows expanding to `gh api search/repositories` if filtered pool < 3 repos.  
**Verdict:** This expansion was explicitly discussed and accepted during Q4b ("if pool is <3 repos, expand to GitHub search API"). The user did not object. The primary domain remains starred repos; GitHub search is a fallback edge case. **Accepted — consistent with Q4b discussion, though it technically exceeds the Q1=A lock.**

---

## Script Verification

| Script | Locked requirement | Implementation | Status |
|--------|-------------------|----------------|--------|
| `check-tools.sh` | Phase 0: detect gh, Ollama, DeepWiki, Sideshow, jq | Detects gh (auth check), Ollama (local+cloud), jq. DeepWiki/Sideshow marked "❓ agent must verify" | ✅ |
| `pull-stars.sh` | Pull starred repos with pagination, shared cache, `--refresh` | `gh api user/starred --paginate`; cache at `~/.cache/starsieve/`; 24h freshness; `--refresh` flag; `STARSIEVE_CACHE_DIR` env override | ✅ |
| `classify-candidates.py` | Ollama classify, keep 8-12, fallback to LLM | Default `--max 12`; local Ollama + cloud fallback; exits 1 if unavailable (agent falls back to LLM) | ✅ |
| `pull-meta.sh` | Pull metadata + README per repo, save to meta/ | Pulls repo metadata, README (base64 decode), latest release, issue stats; saves to `{task-dir}/meta/{slug}_meta.json` + `_readme.md` | ✅ |
| `validate-comparison.py` | 5 checks: source tracing, completeness, score consistency, gap transparency, file integrity | All 5 implemented; parses goal.md for criteria, comparison.md for claims, checks fact/meta file existence, gap transparency via gaps.md | ✅ |

---

## Summary

| Category | Count |
|----------|-------|
| Locked decisions | 12 |
| ✅ Matches | 10 |
| ⚠️ Accepted deviations | 2 (skill name = user override; search expansion = Q4b discussion) |
| ❌ Violations | 0 |
| Cross-cutting checks | 8/8 passed |
| Script checks | 5/5 passed |

**Verdict:** The `starsieve` skill is consistent with all locked decisions from Sideshow session `Z66S_mxjs0I`. The two deviations are accepted: the skill name was explicitly chosen by the user during the build phase, and the GitHub search expansion was discussed and accepted during Q4b. No violations found.